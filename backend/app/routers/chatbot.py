"""
Routes and endpoints related to chatbot interactions.

Includes:
- POST /chat - HTTP endpoint for chatbot (for compatibility)
- POST /chat/stream - Streaming endpoint with Server-Sent Events (SSE)
- WebSocket /ws/chatbot - Real-time chatbot with conversation context
- GET /history - Retrieve chat history for a user
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import BaseModel
from datetime import datetime, timedelta
import time
import logging
import json
import asyncio
import hashlib
from app.agents.orchestrator import orchestrator_agent
from app.database import get_database
from langgraph.checkpoint.memory import InMemorySaver

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

logger = logging.getLogger(__name__)

# Use checkpointer for conversation context (memory)
# This allows the orchestrator to remember previous messages in the conversation
checkpointer = InMemorySaver()

# Simple response cache for common queries (expires after 5 minutes)
response_cache: Dict[str, tuple[str, datetime]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def clean_response_formatting(text: str) -> str:
    """
    Clean up response formatting to ensure consistency.
    - Replace ### with ## (no sub-headers)
    - Ensure consistent bullet points
    - Remove numbered lists
    """
    import re
    
    # Replace ### with ## (no sub-headers allowed)
    text = re.sub(r'^###\s+', '## ', text, flags=re.MULTILINE)
    
    # Replace numbered lists with bullet points
    text = re.sub(r'^\d+\.\s+', '• ', text, flags=re.MULTILINE)
    
    # Ensure consistent spacing after headers
    text = re.sub(r'^##\s+([^\n]+)\n(?!\n)', r'## \1\n\n', text, flags=re.MULTILINE)
    
    return text.strip()


@router.post("/clear-cache")
async def clear_cache():
    """Clear the chatbot response cache."""
    global response_cache
    cache_size = len(response_cache)
    response_cache.clear()
    return {"success": True, "cleared": cache_size, "message": f"Cleared {cache_size} cached responses"}


async def save_chat_message(user_id: str, thread_id: str, role: str, content: str):
    """
    Save a chat message to MongoDB for history retrieval.
    
    Fails gracefully - if MongoDB is unavailable, logs warning but doesn't crash.
    This allows the chatbot to continue working even without persistence.
    """
    try:
        database = get_database()
        if database is None:
            logger.warning("Database not available, skipping chat history save")
            return
        
        collection = database["chat_history"]
        await collection.insert_one({
            "user_id": user_id,
            "thread_id": thread_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow()
        })
    except Exception as e:
        # Log but don't crash - chatbot should work even if history saving fails
        logger.warning(f"Could not save chat message (chatbot will continue): {e}")


def clean_response_formatting(response: str) -> str:
    """
    Clean and enforce consistent response formatting.
    - Convert ### to ##
    - Convert ## with numbers (## 1. or ## 2.) to bullet points
    - Ensure proper spacing
    - Remove excessive blank lines
    """
    import re
    
    # Replace ### with ## (no sub-headers)
    response = re.sub(r'^###\s+', '## ', response, flags=re.MULTILINE)
    
    # Replace numbered sub-headers like "## 1. Title" with "• **Title**"
    response = re.sub(r'^##\s+\d+\.\s+\*\*(.+?)\*\*', r'• **\1**', response, flags=re.MULTILINE)
    response = re.sub(r'^##\s+\d+\.\s+(.+?)$', r'• **\1**', response, flags=re.MULTILINE)
    
    # Ensure single blank line between sections (no more than 2 consecutive newlines)
    response = re.sub(r'\n{3,}', '\n\n', response)
    
    # Remove trailing whitespace from lines
    response = '\n'.join(line.rstrip() for line in response.split('\n'))
    
    # Remove leading/trailing blank lines
    response = response.strip()
    
    return response


def clean_response_formatting(response: str) -> str:
    """
    Clean and enforce consistent formatting in agent responses.
    
    Rules:
    - Convert ### to ##
    - Ensure blank line after headers
    - Remove extra blank lines
    - Ensure consistent bullet points
    """
    import re
    
    # Replace ### with ##
    response = re.sub(r'^###\s+', '## ', response, flags=re.MULTILINE)
    
    # Ensure ONE blank line after headers (## Header)
    response = re.sub(r'(^##\s+.+)$(?!\n\n)', r'\1\n', response, flags=re.MULTILINE)
    
    # Remove more than 2 consecutive newlines
    response = re.sub(r'\n{3,}', '\n\n', response)
    
    # Ensure bullet points use • consistently
    response = re.sub(r'^[\s]*[-*]\s+', '• ', response, flags=re.MULTILINE)
    
    return response.strip()


class ChatMessage(BaseModel):
    """Chat message model."""
    message: str
    context: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    context: Dict[str, Any] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage) -> ChatResponse:
    """
    Handle chatbot conversation with response caching for common queries.
    
    Args:
        message: User message and context
    
    Returns:
        ChatResponse: Bot response
    """
    # Check cache for common queries
    cache_key = hashlib.md5(message.message.lower().strip().encode()).hexdigest()
    if cache_key in response_cache:
        cached_response, cached_time = response_cache[cache_key]
        age_seconds = (datetime.utcnow() - cached_time).total_seconds()
        if age_seconds < CACHE_TTL_SECONDS:
            logger.info(f"Cache HIT for query (age: {age_seconds:.1f}s)")
            return ChatResponse(
                response=f"{cached_response}\n\n_Note: Cached response ({int(age_seconds)}s old)_",
                context=message.context
            )
        else:
            # Expired cache entry
            del response_cache[cache_key]
    try:
        # Check if orchestrator agent is initialized
        if orchestrator_agent is None:
            raise HTTPException(
                status_code=503,
                detail="Chatbot service is unavailable. Please ensure OPENAI_API_KEY is configured."
            )
        
        # Generate a unique thread_id for this conversation
        # If you want conversation continuity, the client should pass thread_id in context
        thread_id = message.context.get("thread_id", f"http_chat_{int(time.time() * 1000)}")
        user_id = message.context.get("user_id", "anonymous")
        current_page = message.context.get("current_page", "unknown")
        
        # Enhance message with page context
        enhanced_message = message.message
        if current_page and current_page != "unknown":
            enhanced_message = f"[User is viewing: {current_page}]\n\n{message.message}"
        
        # Create config with thread_id for checkpointer (conversation memory)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Save user message to history
        await save_chat_message(user_id, thread_id, "user", message.message)
        
        # Use orchestrator agent to handle the conversation
        result = orchestrator_agent.invoke(
            {"messages": [{"role": "user", "content": enhanced_message}]},
            config
        )
        
        response_text = result["messages"][-1].content if result.get("messages") else "I'm sorry, I couldn't process that."
        
        # Clean and enforce consistent formatting
        response_text = clean_response_formatting(response_text)
        
        # Cache the response for common queries
        response_cache[cache_key] = (response_text, datetime.utcnow())
        logger.info(f"Cached response for query (cache size: {len(response_cache)})")
        
        # Save assistant response to history
        await save_chat_message(user_id, thread_id, "assistant", response_text)
        
        # Include thread_id in context so client can maintain conversation
        response_context = {**message.context, "thread_id": thread_id, "user_id": user_id}
        
        return ChatResponse(
            response=response_text,
            context=response_context
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(message: ChatMessage):
    """
    Handle chatbot conversation with streaming response (Server-Sent Events).
    
    This endpoint streams the response token by token in real-time,
    providing a better user experience for long responses.
    
    Args:
        message: User message and context
    
    Returns:
        StreamingResponse: SSE stream with tokens as they're generated
        
    Example Response (SSE format):
        data: {"token": "Hello", "done": false}
        data: {"token": " there", "done": false}
        data: {"token": "!", "done": false}
        data: {"token": "", "done": true, "context": {...}}
    """
    try:
        # Check if orchestrator agent is initialized
        if orchestrator_agent is None:
            raise HTTPException(
                status_code=503,
                detail="Chatbot service is unavailable. Please ensure OPENAI_API_KEY is configured."
            )
        
        thread_id = message.context.get("thread_id", f"http_chat_{int(time.time() * 1000)}")
        user_id = message.context.get("user_id", "anonymous")
        current_page = message.context.get("current_page", "unknown")
        
        # Enhance message with page context
        enhanced_message = message.message
        if current_page and current_page != "unknown":
            enhanced_message = f"[User is viewing: {current_page}]\n\n{message.message}"
        
        # Save user message to history
        await save_chat_message(user_id, thread_id, "user", message.message)
        
        async def generate_tokens() -> AsyncGenerator[str, None]:
            """Generate tokens from the orchestrator agent stream."""
            try:
                config = {"configurable": {"thread_id": thread_id}}
                full_response = ""
                
                # Use agent's stream method for token-by-token generation
                async for chunk in orchestrator_agent.astream(
                    {"messages": [{"role": "user", "content": enhanced_message}]},
                    config
                ):
                    # Extract content from the chunk
                    if isinstance(chunk, dict):
                        messages = chunk.get("messages", [])
                        if messages and len(messages) > 0:
                            last_message = messages[-1]
                            
                            # Handle different message formats
                            if hasattr(last_message, 'content'):
                                content = last_message.content
                            elif isinstance(last_message, dict):
                                content = last_message.get('content', '')
                            else:
                                content = str(last_message)
                            
                            # Calculate the new token (delta)
                            if content and len(content) > len(full_response):
                                new_token = content[len(full_response):]
                                full_response = content
                                
                                # Send token as SSE immediately (no delay for real-time feel)
                                yield f"data: {json.dumps({'token': new_token, 'done': False})}\n\n"
                
                # If no streaming happened, fall back to full response
                if not full_response:
                    # Get the final result
                    result = orchestrator_agent.invoke(
                        {"messages": [{"role": "user", "content": enhanced_message}]},
                        config
                    )
                    full_response = result["messages"][-1].content if result.get("messages") else "I'm sorry, I couldn't process that."
                    
                    # Stream the full response word by word for better UX
                    words = full_response.split()
                    for i, word in enumerate(words):
                        token = word if i == 0 else f" {word}"
                        yield f"data: {json.dumps({'token': token, 'done': False})}\n\n"
                        await asyncio.sleep(0.02)  # Reduced delay for faster streaming
                
                # Clean and enforce consistent formatting
                full_response = clean_response_formatting(full_response)
                
                # Clean and enforce consistent formatting
                full_response = clean_response_formatting(full_response)
                
                # Save assistant response to history
                await save_chat_message(user_id, thread_id, "assistant", full_response)
                
                # Send completion signal with context
                response_context = {**message.context, "thread_id": thread_id, "user_id": user_id}
                yield f"data: {json.dumps({'token': '', 'done': True, 'context': response_context, 'full_response': full_response})}\n\n"
                
            except Exception as e:
                logger.error(f"Streaming error: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        
        return StreamingResponse(
            generate_tokens(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat streaming setup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat streaming failed: {str(e)}")


@router.websocket("/ws")
async def websocket_chatbot(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chatbot interactions.
    
    This endpoint provides:
    - Real-time bidirectional communication
    - Conversation context management (thread_id)
    - Automatic routing to appropriate agents via Orchestrator
    - Persistent conversation memory
    
    Connection Flow:
    1. Client connects to ws://localhost:8000/api/v1/ws/chatbot
    2. Server accepts connection and creates unique thread_id
    3. Client sends messages: {"message": "user query"}
    4. Orchestrator routes to appropriate agent(s)
    5. Server sends responses: {"response": "agent response"}
    6. Conversation context is maintained via thread_id
    
    Endpoint: `ws://localhost:8000/api/v1/chatbot/ws`
    
    Example client usage:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/chatbot/ws');
    ws.onopen = () => {
        ws.send(JSON.stringify({message: "What's our revenue?"}));
    };
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data.response);
    };
    ```
    """
    await websocket.accept()
    
    # Check if orchestrator agent is initialized
    if orchestrator_agent is None:
        await websocket.send_json({
            "error": "Chatbot service is unavailable. Please ensure OPENAI_API_KEY is configured."
        })
        await websocket.close()
        return
    
    # Create unique thread_id for this conversation
    # This allows the orchestrator to maintain context across messages
    thread_id = f"chat_{websocket.client.host}_{int(time.time())}"
    logger.info(f"WebSocket connection established: {thread_id}")
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            user_message = data.get("message", "")
            
            if not user_message:
                await websocket.send_json({"error": "Message is required"})
                continue
            
            logger.info(f"[{thread_id}] Received message: {user_message[:50]}...")
            
            # Call orchestrator agent with conversation context
            # The checkpointer maintains conversation history using thread_id
            config = {"configurable": {"thread_id": thread_id}}
            
            try:
                # Invoke orchestrator agent with context
                result = orchestrator_agent.invoke(
                    {"messages": [{"role": "user", "content": user_message}]},
                    config
                )
                
                # Extract response from agent
                response_text = "I'm sorry, I couldn't process that."
                if result.get("messages") and len(result["messages"]) > 0:
                    response_text = result["messages"][-1].content
                
                # Send response back to client
                await websocket.send_json({
                    "response": response_text,
                    "thread_id": thread_id
                })
                
                logger.info(f"[{thread_id}] Sent response: {response_text[:50]}...")
                
            except Exception as e:
                logger.error(f"[{thread_id}] Error processing message: {e}")
                await websocket.send_json({
                    "error": f"Error processing message: {str(e)}",
                    "thread_id": thread_id
                })
                
    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {thread_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {thread_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass


@router.get("/history")
async def get_chat_history(
    user_id: str = Query(..., description="User ID to retrieve history for"),
    thread_id: Optional[str] = Query(None, description="Optional thread ID to filter by"),
    limit: int = Query(50, description="Maximum number of messages to return")
) -> List[Dict[str, Any]]:
    """
    Get chat history for a user.
    
    Args:
        user_id: User identifier
        thread_id: Optional thread ID to filter by specific conversation
        limit: Maximum number of messages to return (default 50)
    
    Returns:
        List: Chat history messages sorted by timestamp (newest first)
        Returns empty list if database is unavailable (graceful degradation)
    """
    try:
        database = get_database()
        if database is None:
            logger.warning("Database connection not available, returning empty chat history")
            return []  # Graceful degradation - return empty history instead of error
        
        collection = database["chat_history"]
        
        # Build query
        query = {"user_id": user_id}
        if thread_id:
            query["thread_id"] = thread_id
        
        # Retrieve messages sorted by timestamp (newest first)
        # Add timeout to prevent hanging
        cursor = collection.find(query).sort("timestamp", -1).limit(limit)
        messages = await cursor.to_list(length=limit)
        
        # Format response
        history = []
        for msg in messages:
            history.append({
                "thread_id": msg.get("thread_id", ""),
                "role": msg.get("role", ""),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", datetime.utcnow()).isoformat()
            })
        
        # Reverse to show oldest first (chronological order)
        history.reverse()
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        # Log the error but return empty list instead of failing
        # This allows the chatbot to work even if MongoDB is down
        logger.warning(f"Error fetching chat history (returning empty): {e}")
        return []  # Graceful degradation



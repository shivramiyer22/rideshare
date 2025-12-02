"""
Routes and endpoints related to chatbot interactions.

Includes:
- POST /chat - HTTP endpoint for chatbot (for compatibility)
- WebSocket /ws/chatbot - Real-time chatbot with conversation context
- GET /history - Retrieve chat history for a user
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import time
import logging
from app.agents.orchestrator import orchestrator_agent
from app.database import get_database
from langgraph.checkpoint.memory import InMemorySaver

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

logger = logging.getLogger(__name__)

# Use checkpointer for conversation context (memory)
# This allows the orchestrator to remember previous messages in the conversation
checkpointer = InMemorySaver()


async def save_chat_message(user_id: str, thread_id: str, role: str, content: str):
    """Save a chat message to MongoDB for history retrieval."""
    try:
        database = get_database()
        if database is None:
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
        logger.warning(f"Could not save chat message: {e}")


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
    Handle chatbot conversation.
    
    Args:
        message: User message and context
    
    Returns:
        ChatResponse: Bot response
    """
    try:
        # Check if orchestrator agent is initialized
        if orchestrator_agent is None:
            raise HTTPException(
                status_code=503,
                detail="Chatbot service is unavailable. Please ensure OPENAI_API_KEY is configured."
            )
        
        # Generate a unique thread_id for this conversation
        # For HTTP endpoint, we create a new thread per request
        # If you want conversation continuity, the client should pass thread_id in context
        thread_id = message.context.get("thread_id", f"http_chat_{int(time.time() * 1000)}")
        user_id = message.context.get("user_id", "anonymous")
        
        # Create config with thread_id for checkpointer (conversation memory)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Save user message to history
        await save_chat_message(user_id, thread_id, "user", message.message)
        
        # Use orchestrator agent to handle the conversation
        result = orchestrator_agent.invoke(
            {"messages": [{"role": "user", "content": message.message}]},
            config
        )
        
        response_text = result["messages"][-1].content if result.get("messages") else "I'm sorry, I couldn't process that."
        
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
    """
    try:
        database = get_database()
        if database is None:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        collection = database["chat_history"]
        
        # Build query
        query = {"user_id": user_id}
        if thread_id:
            query["thread_id"] = thread_id
        
        # Retrieve messages sorted by timestamp (newest first)
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
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")



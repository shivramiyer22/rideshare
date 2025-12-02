"""
Routes and endpoints related to chatbot interactions.

Includes:
- POST /chat - HTTP endpoint for chatbot (for compatibility)
- WebSocket /ws/chatbot - Real-time chatbot with conversation context
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List
from pydantic import BaseModel
import time
import logging
from app.agents.orchestrator import orchestrator_agent
from langgraph.checkpoint.memory import InMemorySaver

router = APIRouter(prefix="/chatbot", tags=["chatbot"])

logger = logging.getLogger(__name__)

# Use checkpointer for conversation context (memory)
# This allows the orchestrator to remember previous messages in the conversation
checkpointer = InMemorySaver()


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
        # Use orchestrator agent to handle the conversation
        result = orchestrator_agent.invoke({
            "messages": [
                {"role": "user", "content": message.message}
            ]
        })
        
        response_text = result["messages"][-1].content if result.get("messages") else "I'm sorry, I couldn't process that."
        
        return ChatResponse(
            response=response_text,
            context=message.context
        )
    except Exception as e:
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
async def get_chat_history(user_id: str) -> List[Dict[str, Any]]:
    """
    Get chat history for a user.
    
    Args:
        user_id: User identifier
    
    Returns:
        List: Chat history
    """
    # TODO: Implement chat history retrieval
    # This would query the checkpointer for conversation history
    return []



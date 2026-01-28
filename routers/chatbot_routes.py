from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any, List
import uuid
import logging
from datetime import datetime

# Import MindMate Chatbot
from agents.chat.chatbot import MindMate

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"],
    responses={404: {"description": "Not found"}},
)

# In-memory session store
# Map session_id -> MindMate instance
active_sessions: Dict[str, MindMate] = {}

class StartChatRequest(BaseModel):
    """Request to start a new chat session"""
    user_id: Optional[str] = Field(None, description="Optional user ID for personalization")

class ChatMessageRequest(BaseModel):
    """Request to send a message"""
    session_id: str = Field(..., description="Active session ID")
    message: str = Field(..., description="User message content")

class ChatResponse(BaseModel):
    """Chat response"""
    session_id: str
    response: str
    mood: Optional[str] = "neutral"
    timestamp: datetime

@router.post("/start", response_model=ChatResponse)
async def start_chat(request: StartChatRequest):
    """Start a new chat session"""
    try:
        # Create new MindMate instance
        # Note: We are currently using in-memory only without DB persistence for the session itself
        # to match the frontend's expectation of a simple chat.
        # If DB is needed, we would inject db session here.
        mindmate = MindMate() 
        
        # Generate our own session ID for routing
        session_id = str(uuid.uuid4())
        
        # Store instance
        active_sessions[session_id] = mindmate
        
        # Initial greeting is usually handled by frontend, but we can return one if needed.
        # For now, we just return the session ID.
        
        return ChatResponse(
            session_id=session_id,
            response="Hello! I'm MindMate. How are you feeling today?",
            mood="neutral",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to start chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=ChatResponse)
async def chat(request: ChatMessageRequest):
    """Send a message to the chatbot"""
    try:
        session_id = request.session_id
        
        # Get or create session (auto-create if missing to be robust)
        if session_id not in active_sessions:
            logger.info(f"Session {session_id} not found, creating new instance.")
            active_sessions[session_id] = MindMate()
            
        mindmate = active_sessions[session_id]
        
        # Get response
        response_text = mindmate.chat(request.message)
        
        # Get mood if available
        mood = "neutral"
        if hasattr(mindmate, "memory") and hasattr(mindmate.memory, "session_data"):
             mood = mindmate.memory.session_data.get("mood_trend", "neutral")
             
        return ChatResponse(
            session_id=session_id,
            response=response_text,
            mood=mood,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}")
async def end_chat(session_id: str):
    """End a chat session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"status": "success", "message": "Session ended"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from sqlalchemy.orm import Session
import uuid
import logging
from datetime import datetime

# Import MindMate Chatbot
from agents.chat.chatbot import MindMate

# Import database and auth dependencies
from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from models.sql_models.chat_models import ChatSession, ChatMessage

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

class ChatHistoryItem(BaseModel):
    """Single chat history item"""
    session_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    conversation_summary: Optional[str] = None

class ChatMessageItem(BaseModel):
    """Single chat message"""
    id: int
    role: str
    content: str
    created_at: datetime

class ChatHistoryResponse(BaseModel):
    """Response for chat history"""
    sessions: List[ChatHistoryItem]

class ChatMessagesResponse(BaseModel):
    """Response for chat messages"""
    session_id: str
    messages: List[ChatMessageItem]


@router.post("/start", response_model=ChatResponse)
async def start_chat(
    request: StartChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token)
):
    """Start a new chat session with database persistence"""
    try:
        # Get patient_id from authenticated user object
        user = current_user["user"]
        patient_id = str(user.id)
        
        # Create new MindMate instance WITH database session
        mindmate = MindMate(db_session=db, patient_id=patient_id)
        
        # Get the session_id from the ConversationMemory's db session
        if mindmate.memory.chat_session:
            session_id = mindmate.memory.chat_session.session_id
        else:
            # Fallback if DB session creation failed
            session_id = str(uuid.uuid4())
        
        # Store instance in memory for fast access
        active_sessions[session_id] = mindmate
        
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
async def chat(
    request: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token)
):
    """Send a message to the chatbot"""
    try:
        session_id = request.session_id
        user = current_user["user"]
        patient_id = str(user.id)
        
        # Get or create session
        if session_id not in active_sessions:
            logger.info(f"Session {session_id} not found in memory, creating new instance.")
            mindmate = MindMate(db_session=db, patient_id=patient_id)
            active_sessions[session_id] = mindmate
            
        mindmate = active_sessions[session_id]
        
        # Ensure db_session is set (may have been lost if instance was recreated)
        if not mindmate.memory.db_session:
            mindmate.memory.db_session = db
        
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


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token)
):
    """Get all chat sessions for the authenticated user"""
    try:
        user = current_user["user"]
        patient_id = str(user.id)
        
        # Query chat sessions for this patient
        sessions = db.query(ChatSession).filter(
            ChatSession.patient_id == patient_id
        ).order_by(ChatSession.created_at.desc()).all()
        
        history_items = []
        for session in sessions:
            # Count messages for this session
            message_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id
            ).count()
            
            history_items.append(ChatHistoryItem(
                session_id=session.session_id,
                status=session.status,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count,
                conversation_summary=session.conversation_summary
            ))
        
        return ChatHistoryResponse(sessions=history_items)
        
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=ChatMessagesResponse)
async def get_chat_messages(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token)
):
    """Get all messages for a specific chat session"""
    try:
        user = current_user["user"]
        patient_id = str(user.id)
        
        # Verify session belongs to this patient
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.patient_id == patient_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Get messages
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        message_items = [
            ChatMessageItem(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
        return ChatMessagesResponse(
            session_id=session_id,
            messages=message_items
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def end_chat(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_from_token)
):
    """End a chat session"""
    try:
        patient_id = current_user.get("id")
        
        # Update session status in database
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.patient_id == patient_id
        ).first()
        
        if session:
            session.status = "completed"
            db.commit()
        
        # Remove from memory
        if session_id in active_sessions:
            del active_sessions[session_id]
            
        return {"status": "success", "message": "Session ended"}
        
    except Exception as e:
        logger.error(f"Failed to end chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

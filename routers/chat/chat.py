from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging

from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token

# Import the new chatbot system
from chatbot.mindmate_chatbot import get_chatbot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

# Pydantic models for chat
class ChatMessage(BaseModel):
    id: str
    text: str
    sender: str  # "user" or "ai"
    timestamp: datetime
    session_id: str

class ChatSession(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    message_count: int = 0

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class SendMessageRequest(BaseModel):
    message: str
    session_id: str
    is_first_message: bool = False

class SendMessageResponse(BaseModel):
    response: str
    session_id: str

class UpdateSessionRequest(BaseModel):
    title: str

class TogglePinRequest(BaseModel):
    is_pinned: bool

# In-memory storage for chat sessions and messages (in production, use database)
chat_sessions = {}
chat_messages = {}

@router.post("/sessions", response_model=ChatSession)
async def create_chat_session(
    request: CreateSessionRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    user = current_user_data["user"]
    
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    session = ChatSession(
        id=session_id,
        title=request.title or "New Chat",
        created_at=now,
        updated_at=now,
        is_pinned=False,
        message_count=0
    )
    
    chat_sessions[session_id] = {
        "id": session_id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "is_pinned": session.is_pinned,
        "message_count": session.message_count,
        "user_id": str(user.id)
    }
    
    return session

@router.get("/sessions", response_model=dict)
async def get_chat_sessions(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user"""
    user = current_user_data["user"]
    user_id = str(user.id)
    
    # Filter sessions by user
    user_sessions = [
        session for session in chat_sessions.values() 
        if session.get("user_id") == user_id
    ]
    
    pinned_sessions = [s for s in user_sessions if s["is_pinned"]]
    other_sessions = [s for s in user_sessions if not s["is_pinned"]]
    
    # Sort by updated_at (most recent first)
    pinned_sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    other_sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    
    return {
        "pinned_sessions": pinned_sessions,
        "other_sessions": other_sessions
    }

@router.get("/sessions/{session_id}/messages", response_model=dict)
async def get_session_messages(
    session_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all messages for a specific chat session"""
    user = current_user_data["user"]
    user_id = str(user.id)
    
    # Check if session exists and belongs to user
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[session_id]
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get messages for this session
    session_messages = [
        msg for msg in chat_messages.values() 
        if msg["session_id"] == session_id
    ]
    
    # Sort by timestamp
    session_messages.sort(key=lambda x: x["timestamp"])
    
    return {"messages": session_messages}

@router.post("", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response"""
    user = current_user_data["user"]
    user_id = str(user.id)
    
    # Check if session exists and belongs to user
    if request.session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[request.session_id]
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create user message
    user_message_id = str(uuid.uuid4())
    user_message = {
        "id": user_message_id,
        "text": request.message,
        "sender": "user",
        "timestamp": datetime.utcnow(),
        "session_id": request.session_id
    }
    
    chat_messages[user_message_id] = user_message
    
    # Generate AI response using the new chatbot system
    ai_response = generate_ai_response(request.message, request.session_id)
    
    # Create AI message
    ai_message_id = str(uuid.uuid4())
    ai_message = {
        "id": ai_message_id,
        "text": ai_response,
        "sender": "ai",
        "timestamp": datetime.utcnow(),
        "session_id": request.session_id
    }
    
    chat_messages[ai_message_id] = ai_message
    
    # Update session
    session["message_count"] += 2  # User message + AI response
    session["updated_at"] = datetime.utcnow()
    
    return SendMessageResponse(
        response=ai_response,
        session_id=request.session_id
    )

@router.patch("/sessions/{session_id}", response_model=ChatSession)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update chat session title"""
    user = current_user_data["user"]
    user_id = str(user.id)
    
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[session_id]
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session["title"] = request.title
    session["updated_at"] = datetime.utcnow()
    
    return ChatSession(**session)

@router.patch("/sessions/{session_id}/toggle-pin", response_model=ChatSession)
async def toggle_pin_session(
    session_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Toggle pin status of a chat session"""
    user = current_user_data["user"]
    user_id = str(user.id)
    
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[session_id]
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session["is_pinned"] = not session["is_pinned"]
    session["updated_at"] = datetime.utcnow()
    
    return ChatSession(**session)

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    user = current_user_data["user"]
    user_id = str(user.id)
    
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    session = chat_sessions[session_id]
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete session
    del chat_sessions[session_id]
    
    # Delete all messages for this session
    message_ids_to_delete = [
        msg_id for msg_id, msg in chat_messages.items()
        if msg["session_id"] == session_id
    ]
    
    for msg_id in message_ids_to_delete:
        del chat_messages[msg_id]
    
        return {"message": "Chat session deleted successfully"}

# Global chatbot instances per session
_chatbot_instances = {}

def get_chatbot_instance(session_id: str):
    """Get or create chatbot instance for a specific session"""
    if session_id not in _chatbot_instances:
        try:
            _chatbot_instances[session_id] = get_chatbot()
            logger.info(f"Chatbot instance created for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to create chatbot instance for session {session_id}: {e}")
            return None
    return _chatbot_instances[session_id]

def generate_ai_response(user_message: str, session_id: str = None) -> str:
    """Generate AI response using the new MindMate chatbot system"""
    try:
        # If no session_id, use fallback
        if not session_id:
            return _generate_fallback_response(user_message)
        
        # Get chatbot instance for this session
        chatbot = get_chatbot_instance(session_id)
        if not chatbot:
            # Fallback to simple responses if chatbot fails
            return _generate_fallback_response(user_message)
        
        # Use the new chatbot system
        response = chatbot.chat(user_message)
        logger.info(f"Chatbot response generated for session {session_id}: {response[:100]}...")
        return response
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        # Fallback to simple responses
        return _generate_fallback_response(user_message)

def _generate_fallback_response(user_message: str) -> str:
    """Fallback response generator if chatbot fails"""
    user_message_lower = user_message.lower()
    
    # Simple keyword-based responses
    if any(word in user_message_lower for word in ["hello", "hi", "hey"]):
        return "Hello! I'm MindMate, your AI mental health companion. How are you feeling today?"
    
    elif any(word in user_message_lower for word in ["sad", "depressed", "down", "unhappy"]):
        return "I'm sorry you're feeling this way. It's important to acknowledge these feelings. Can you tell me more about what's been happening?"
    
    elif any(word in user_message_lower for word in ["anxious", "worried", "stress", "nervous"]):
        return "Anxiety can be really challenging. Let's take a moment to breathe together. What's causing you to feel anxious right now?"
    
    elif any(word in user_message_lower for word in ["angry", "mad", "frustrated"]):
        return "It's completely normal to feel angry sometimes. What happened that made you feel this way?"
    
    elif any(word in user_message_lower for word in ["tired", "exhausted", "sleep"]):
        return "Sleep and rest are crucial for mental health. How has your sleep been lately? Are you getting enough rest?"
    
    elif any(word in user_message_lower for word in ["help", "support", "need"]):
        return "I'm here to help and support you. What specific support do you need right now?"
    
    elif any(word in user_message_lower for word in ["thank", "thanks", "appreciate"]):
        return "You're very welcome! I'm glad I can help. How else can I support you today?"
    
    else:
        # Generic empathetic response
        responses = [
            "I hear you. Can you tell me more about that?",
            "That sounds challenging. How long have you felt this way?",
            "I appreciate you sharing that with me. What would help you feel better?",
            "Let's explore that together. What's been on your mind lately?",
            "I understand this is difficult. Would you like to talk more about it?",
            "Thank you for opening up. How can I best support you right now?"
        ]
        
        import random
        return random.choice(responses)


class StartAssessmentRequest(BaseModel):
    session_id: str

@router.post("/start-assessment")
async def start_assessment(
    request: StartAssessmentRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Start a new mental health assessment"""
    try:
        session_id = request.session_id
        
        # Verify session exists and belongs to user
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        user = current_user_data["user"]
        user_id = str(user.id)
        
        session = chat_sessions[session_id]
        if session.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        chatbot = get_chatbot_instance(session_id)
        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot system unavailable")
        
        # Start the assessment workflow
        response = chatbot.chat("start")
        
        return {
            "message": "Assessment started successfully",
            "response": response,
            "assessment_status": chatbot.get_assessment_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start assessment: {str(e)}")

@router.get("/assessment-status/{session_id}")
async def get_assessment_status(
    session_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get current assessment status for a specific session"""
    try:
        # Verify session exists and belongs to user
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        user = current_user_data["user"]
        user_id = str(user.id)
        
        session = chat_sessions[session_id]
        if session.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        chatbot = get_chatbot_instance(session_id)
        if not chatbot:
            raise HTTPException(status_code=500, detail="Chatbot system unavailable")
        
        status = chatbot.get_assessment_status()
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assessment status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get assessment status: {str(e)}")


"""
Chatbot Routes for MindMate
===========================
API endpoints for the RE-ACT agent chatbot system.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from chatbot.mindmate_chatbot import get_chatbot, chat_with_bot

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Pydantic models for chatbot
class ChatbotMessage(BaseModel):
    message: str = Field(..., description="User message to the chatbot")
    session_id: Optional[str] = Field(None, description="Chat session ID")

class ChatbotResponse(BaseModel):
    response: str = Field(..., description="Chatbot response")
    session_id: str = Field(..., description="Chat session ID")
    assessment_status: Optional[Dict[str, Any]] = Field(None, description="Current assessment status")
    timestamp: datetime = Field(default_factory=datetime.now)

class StartAssessmentRequest(BaseModel):
    session_id: Optional[str] = Field(None, description="Chat session ID")

class AssessmentStatus(BaseModel):
    session_id: str = Field(..., description="Chat session ID")
    current_tool: str = Field(..., description="Current assessment tool")
    progress: str = Field(..., description="Assessment progress")
    completed_tools: list = Field(default_factory=list, description="Completed assessment tools")
    timestamp: datetime = Field(default_factory=datetime.now)

# In-memory storage for chatbot sessions (in production, use database)
chatbot_sessions = {}

@router.post("/chat", response_model=ChatbotResponse)
async def chat_with_chatbot(
    request: ChatbotMessage,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Chat with the MindMate chatbot"""
    try:
        user = current_user_data["user"]
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize session if new
        if session_id not in chatbot_sessions:
            chatbot_sessions[session_id] = {
                "user_id": str(user.id),
                "created_at": datetime.now(),
                "messages": [],
                "assessment_data": {}
            }
        
        # Add user message to session
        chatbot_sessions[session_id]["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now()
        })
        
        # Get chatbot response
        chatbot = get_chatbot()
        response = chatbot.chat(request.message)
        
        # Add bot response to session
        chatbot_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })
        
        # Get assessment status
        assessment_status = chatbot.get_assessment_status()
        
        return ChatbotResponse(
            response=response,
            session_id=session_id,
            assessment_status=assessment_status,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot error: {str(e)}"
        )

@router.post("/start-assessment", response_model=ChatbotResponse)
async def start_assessment(
    request: StartAssessmentRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Start a new mental health assessment"""
    try:
        user = current_user_data["user"]
        
        # Generate session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize new session
        chatbot_sessions[session_id] = {
            "user_id": str(user.id),
            "created_at": datetime.now(),
            "messages": [],
            "assessment_data": {},
            "assessment_started": True
        }
        
        # Get chatbot welcome message
        chatbot = get_chatbot()
        response = chatbot.chat("start")
        
        # Add bot response to session
        chatbot_sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now()
        })
        
        # Get assessment status
        assessment_status = chatbot.get_assessment_status()
        
        return ChatbotResponse(
            response=response,
            session_id=session_id,
            assessment_status=assessment_status,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment start error: {str(e)}"
        )

@router.get("/sessions/{session_id}/status", response_model=AssessmentStatus)
async def get_assessment_status(
    session_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get the status of a specific assessment session"""
    try:
        user = current_user_data["user"]
        
        # Check if session exists and belongs to user
        if session_id not in chatbot_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session = chatbot_sessions[session_id]
        if session["user_id"] != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Get current assessment status
        chatbot = get_chatbot()
        status_info = chatbot.get_assessment_status()
        
        # Calculate progress
        total_tools = len(status_info["tool_sequence"])
        current_tool = status_info["current_tool"]
        completed_tools = []
        
        if current_tool:
            current_index = status_info["tool_sequence"].index(current_tool)
            completed_tools = status_info["tool_sequence"][:current_index]
        else:
            completed_tools = status_info["tool_sequence"]
        
        progress = f"{len(completed_tools)}/{total_tools}"
        
        return AssessmentStatus(
            session_id=session_id,
            current_tool=current_tool or "completed",
            progress=progress,
            completed_tools=completed_tools,
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Status retrieval error: {str(e)}"
        )

@router.get("/sessions", response_model=Dict[str, Any])
async def get_user_sessions(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all chatbot sessions for the current user"""
    try:
        user = current_user_data["user"]
        user_id = str(user.id)
        
        # Filter sessions by user
        user_sessions = [
            {
                "session_id": session_id,
                "created_at": session["created_at"],
                "message_count": len(session["messages"]),
                "assessment_started": session.get("assessment_started", False)
            }
            for session_id, session in chatbot_sessions.items()
            if session["user_id"] == user_id
        ]
        
        return {
            "sessions": user_sessions,
            "total_sessions": len(user_sessions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session retrieval error: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a specific chatbot session"""
    try:
        user = current_user_data["user"]
        
        # Check if session exists and belongs to user
        if session_id not in chatbot_sessions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session = chatbot_sessions[session_id]
        if session["user_id"] != str(user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this session"
            )
        
        # Delete session
        del chatbot_sessions[session_id]
        
        return {"message": "Session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Session deletion error: {str(e)}"
        )

@router.post("/reset-assessment")
async def reset_assessment(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Reset the current assessment workflow"""
    try:
        # Reset the chatbot assessment
        chatbot = get_chatbot()
        chatbot.reset_assessment()
        
        return {"message": "Assessment workflow reset successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assessment reset error: {str(e)}"
        )

@router.get("/health")
async def chatbot_health_check():
    """Health check for the chatbot system"""
    try:
        chatbot = get_chatbot()
        status_info = chatbot.get_assessment_status()
        
        return {
            "status": "healthy",
            "chatbot_initialized": True,
            "available_tools": status_info.get("tool_sequence", []),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }

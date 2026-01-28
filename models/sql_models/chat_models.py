from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base_model import Base


from sqlalchemy.dialects.postgresql import UUID

class ChatSession(Base):
    """Model for storing chatbot conversation sessions"""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, paused, completed
    conversation_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    summaries = relationship("ChatConversationSummary", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Model for storing individual chat messages"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON)  # Store tool calls, analysis results, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class ChatConversationSummary(Base):
    """Model for storing conversation summaries and analysis"""
    __tablename__ = "chat_conversation_summaries"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("chat_sessions.session_id"), nullable=False)
    summary = Column(Text)
    key_topics = Column(JSON)  # JSON array of key topics
    sentiment_analysis = Column(JSON)  # JSON object with sentiment data
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="summaries")

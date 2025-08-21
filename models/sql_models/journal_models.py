"""
Journal Models - SQLAlchemy Models for User Journal Entries
==========================================================
Models for storing user journal entries with timestamps and content
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone
import uuid

# Import base model
from .base_model import Base, BaseModel as SQLBaseModel

# ============================================================================
# JOURNAL ENTRY MODEL
# ============================================================================

class JournalEntry(Base, SQLBaseModel):
    """User journal entry with content and metadata"""
    
    __tablename__ = "journal_entries"
    
    # Foreign key to patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Entry content
    content = Column(Text, nullable=False)
    
    # Entry metadata
    mood = Column(String(50), nullable=True)  # Optional mood tracking
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    
    # Timestamps
    entry_date = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False, index=True)
    
    # Status
    is_archived = Column(Boolean, default=False, index=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="journal_entries")
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    @property
    def formatted_date(self) -> str:
        """Get formatted date for display"""
        return self.entry_date.strftime("%B %d, %Y at %I:%M %p")
    
    @property
    def short_date(self) -> str:
        """Get short date for display"""
        return self.entry_date.strftime("%b %d, %Y")
    
    @property
    def time_ago(self) -> str:
        """Get relative time (e.g., '2 hours ago')"""
        now = datetime.now(timezone.utc)
        diff = now - self.entry_date
        
        if diff.days > 0:
            if diff.days == 1:
                return "1 day ago"
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            if hours == 1:
                return "1 hour ago"
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            if minutes == 1:
                return "1 minute ago"
            return f"{minutes} minutes ago"
        else:
            return "Just now"


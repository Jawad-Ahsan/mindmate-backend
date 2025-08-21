"""
Journal Router - API endpoints for user journal entries
======================================================
Handles CRUD operations for journal entries with authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from models.sql_models.journal_models import JournalEntry
from models.sql_models.patient_models import Patient

router = APIRouter(prefix="/journal", tags=["Journal"])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

from pydantic import BaseModel, Field

class JournalEntryCreate(BaseModel):
    """Create a new journal entry"""
    content: str = Field(..., min_length=1, description="Journal entry content")
    mood: Optional[str] = Field(None, max_length=50, description="Optional mood tracking")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")

class JournalEntryUpdate(BaseModel):
    """Update an existing journal entry"""
    content: Optional[str] = Field(None, min_length=1, description="Journal entry content")
    mood: Optional[str] = Field(None, max_length=50, description="Optional mood tracking")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")

class JournalEntryResponse(BaseModel):
    """Journal entry response model"""
    id: str
    content: str
    mood: Optional[str]
    tags: Optional[str]
    entry_date: datetime
    formatted_date: str
    time_ago: str
    is_archived: bool

    class Config:
        from_attributes = True

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/entries", response_model=JournalEntryResponse)
async def create_journal_entry(
    entry_data: JournalEntryCreate,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new journal entry"""
    try:
        user = current_user_data["user"]
        
        # Create journal entry
        journal_entry = JournalEntry(
            patient_id=user.id,
            content=entry_data.content,
            mood=entry_data.mood,
            tags=entry_data.tags,
            entry_date=datetime.now(timezone.utc)
        )
        
        db.add(journal_entry)
        db.commit()
        db.refresh(journal_entry)
        
        return JournalEntryResponse(
            id=str(journal_entry.id),
            content=journal_entry.content,
            mood=journal_entry.mood,
            tags=journal_entry.tags,
            entry_date=journal_entry.entry_date,
            formatted_date=journal_entry.formatted_date,
            time_ago=journal_entry.time_ago,
            is_archived=journal_entry.is_archived
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create journal entry"
        )

@router.get("/entries", response_model=List[JournalEntryResponse])
async def get_journal_entries(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db),
    archived: Optional[bool] = False
):
    """Get all journal entries for the current user"""
    try:
        user = current_user_data["user"]
        
        # Query journal entries
        query = db.query(JournalEntry).filter(
            JournalEntry.patient_id == user.id,
            JournalEntry.is_archived == archived
        ).order_by(JournalEntry.entry_date.desc())
        
        entries = query.all()
        
        return [
            JournalEntryResponse(
                id=str(entry.id),
                content=entry.content,
                mood=entry.mood,
                tags=entry.tags,
                entry_date=entry.entry_date,
                formatted_date=entry.formatted_date,
                time_ago=entry.time_ago,
                is_archived=entry.is_archived
            )
            for entry in entries
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve journal entries"
        )

@router.get("/entries/{entry_id}", response_model=JournalEntryResponse)
async def get_journal_entry(
    entry_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get a specific journal entry by ID"""
    try:
        user = current_user_data["user"]
        
        # Find the entry
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.patient_id == user.id
        ).first()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        
        return JournalEntryResponse(
            id=str(entry.id),
            content=entry.content,
            mood=entry.mood,
            tags=entry.tags,
            entry_date=entry.entry_date,
            formatted_date=entry.formatted_date,
            time_ago=entry.time_ago,
            is_archived=entry.is_archived
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve journal entry"
        )

@router.put("/entries/{entry_id}", response_model=JournalEntryResponse)
async def update_journal_entry(
    entry_id: str,
    entry_data: JournalEntryUpdate,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update a journal entry"""
    try:
        user = current_user_data["user"]
        
        # Find the entry
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.patient_id == user.id
        ).first()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        
        # Update fields if provided
        if entry_data.content is not None:
            entry.content = entry_data.content
        if entry_data.mood is not None:
            entry.mood = entry_data.mood
        if entry_data.tags is not None:
            entry.tags = entry_data.tags
        
        entry.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(entry)
        
        return JournalEntryResponse(
            id=str(entry.id),
            content=entry.content,
            mood=entry.mood,
            tags=entry.tags,
            entry_date=entry.entry_date,
            formatted_date=entry.formatted_date,
            time_ago=entry.time_ago,
            is_archived=entry.is_archived
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update journal entry"
        )

@router.delete("/entries/{entry_id}")
async def delete_journal_entry(
    entry_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Permanently delete a journal entry"""
    try:
        user = current_user_data["user"]
        
        # Find the entry
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.patient_id == user.id
        ).first()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        
        # Permanently delete the entry
        db.delete(entry)
        db.commit()
        
        return {"message": "Journal entry deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete journal entry"
        )

@router.patch("/entries/{entry_id}/archive")
async def toggle_archive_journal_entry(
    entry_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Toggle archive status of a journal entry"""
    try:
        user = current_user_data["user"]
        
        # Find the entry
        entry = db.query(JournalEntry).filter(
            JournalEntry.id == entry_id,
            JournalEntry.patient_id == user.id
        ).first()
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Journal entry not found"
            )
        
        # Toggle archive status
        entry.is_archived = not entry.is_archived
        entry.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(entry)
        
        return {
            "message": f"Journal entry {'archived' if entry.is_archived else 'unarchived'} successfully",
            "is_archived": entry.is_archived
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle archive status"
        )


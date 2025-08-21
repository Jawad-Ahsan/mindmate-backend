from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

# Create single declarative base for all models
Base = declarative_base()

class USERTYPE(str, enum.Enum):
    """Enumeration for user types"""
    ADMIN = "admin"
    PATIENT = "patient"
    SPECIALIST = "specialist"

class BaseModel:
    """Base model with common fields for all tables"""
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    is_deleted = Column(Boolean, default=False, nullable=False)

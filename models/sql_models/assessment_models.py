from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base_model import Base


from sqlalchemy.dialects.postgresql import UUID

class SCIDAssessment(Base):
    """Model for storing SCID assessment sessions"""
    __tablename__ = "scid_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), unique=True, index=True, nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False)
    module_id = Column(String(100), nullable=False)
    module_name = Column(String(255), nullable=False)
    status = Column(String(50), default="in_progress", nullable=False)  # in_progress, completed, paused
    assessment_data = Column(JSON)  # JSON object containing assessment responses
    clinical_insights = Column(JSON)  # JSON object with clinical analysis
    completion_percentage = Column(Float, default=0.0, nullable=False)
    llm_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class AssessmentStatus:
    """Constants for assessment status"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class AssessmentMode:
    """Constants for assessment modes"""
    INTERACTIVE = "interactive"
    AUTOMATED = "automated"
    HYBRID = "hybrid"

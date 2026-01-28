from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
import uuid
from .base_model import Base, BaseModel

class ConsultationMessageSenderRole(str, enum.Enum):
    SPECIALIST = "specialist"
    PATIENT = "patient"
    SYSTEM = "system"

class ConsultationMessage(Base, BaseModel):
    """
    Real-time chat messages between Specialist and Patient for a specific Appointment.
    """
    __tablename__ = "consultation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to the specific appointment
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False, index=True)
    
    # Sender details
    sender_id = Column(UUID(as_uuid=True), nullable=False) # ID of the user (patient_id or specialist_id)
    sender_role = Column(Enum(ConsultationMessageSenderRole), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships (Optional, for easier join if needed)
    # appointment = relationship("Appointment", back_populates="messages")

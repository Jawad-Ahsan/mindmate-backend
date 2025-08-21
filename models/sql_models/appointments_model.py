"""
SQLAlchemy Appointment Model for Mental Health Platform
======================================================
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Numeric, Text, Boolean, CheckConstraint, Index, func
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid
from datetime import datetime
from decimal import Decimal

# Import your base model (adjust import path as needed)
from .base_model import Base, BaseModel


# ============================================================================
# ENUMERATIONS
# ============================================================================

class AppointmentStatusEnum(enum.Enum):
    """Core appointment states"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AppointmentTypeEnum(enum.Enum):
    """Consultation delivery methods"""
    VIRTUAL = "virtual"
    IN_PERSON = "in_person"


class PaymentStatusEnum(enum.Enum):
    """Payment states"""
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"


# ============================================================================
# SQLALCHEMY MODEL
# ============================================================================

class Appointment(Base, BaseModel):
    """Core appointment model - MVP version"""
    __tablename__ = "appointments"
    
    # Primary key and metadata
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Foreign Key Relationships
    # Note: Adjust the table names to match your existing schema
    specialist_id = Column(UUID(as_uuid=True), ForeignKey('specialists.id'), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False)  # Links to your Patient model
    
    # Relationships
    specialist = relationship("Specialists", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")  
    
    # Core appointment fields
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    appointment_type = Column(Enum(AppointmentTypeEnum), nullable=False, default=AppointmentTypeEnum.VIRTUAL)
    status = Column(Enum(AppointmentStatusEnum), nullable=False, default=AppointmentStatusEnum.SCHEDULED)
    
    # Payment
    fee = Column(Numeric(10, 2), nullable=False)
    payment_status = Column(Enum(PaymentStatusEnum), nullable=False, default=PaymentStatusEnum.UNPAID)
    
    # Additional fields
    notes = Column(Text)
    session_notes = Column(Text)
    cancellation_reason = Column(String(500))
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('scheduled_end > scheduled_start', name='check_end_after_start'),
        CheckConstraint('fee >= 0', name='non_negative_fee'),
        Index('idx_appointment_specialist', 'specialist_id'),
        Index('idx_appointment_patient', 'patient_id'),
        Index('idx_appointment_status', 'status'),
        Index('idx_appointment_date', 'scheduled_start'),
        Index('idx_appointment_payment', 'payment_status'),
        Index('idx_appointment_type', 'appointment_type'),
    )
    
    # ========================================
    # VALIDATION METHODS
    # ========================================
    
    @validates('scheduled_start', 'scheduled_end')
    def validate_future_date(self, key, value):
        """Validate that appointment is scheduled in the future"""
        if value < datetime.now():
            raise ValueError("Appointment must be scheduled in the future")
        return value
    
    # ========================================
    # COMPUTED PROPERTIES
    # ========================================
    
    @property
    def is_active(self) -> bool:
        """Check if appointment is active"""
        return self.status in [
            AppointmentStatusEnum.SCHEDULED,
            AppointmentStatusEnum.CONFIRMED
        ]
    
    @property
    def duration_minutes(self) -> int:
        """Duration in minutes"""
        return int((self.scheduled_end - self.scheduled_start).total_seconds() / 60)
    
    @property
    def is_paid(self) -> bool:
        """Check if appointment is paid"""
        return self.payment_status == PaymentStatusEnum.PAID
    
    # ========================================
    # BUSINESS LOGIC METHODS
    # ========================================
    
    def confirm(self):
        """Confirm a scheduled appointment"""
        if self.status != AppointmentStatusEnum.SCHEDULED:
            raise ValueError("Only scheduled appointments can be confirmed")
        self.status = AppointmentStatusEnum.CONFIRMED
    
    def complete(self, session_notes: str):
        """Complete an appointment"""
        if self.status not in [AppointmentStatusEnum.CONFIRMED, AppointmentStatusEnum.SCHEDULED]:
            raise ValueError("Only confirmed or scheduled appointments can be completed")
        
        self.status = AppointmentStatusEnum.COMPLETED
        self.session_notes = session_notes
        
        # Auto-mark as paid for MVP (can be enhanced later)
        if self.payment_status == PaymentStatusEnum.UNPAID:
            self.payment_status = PaymentStatusEnum.PAID
    
    def cancel(self, reason: str):
        """Cancel an appointment"""
        if self.status in [AppointmentStatusEnum.COMPLETED, AppointmentStatusEnum.CANCELLED]:
            raise ValueError("Cannot cancel completed or already cancelled appointments")
        
        self.status = AppointmentStatusEnum.CANCELLED
        self.cancellation_reason = reason
        
        # Handle refund for paid appointments
        if self.payment_status == PaymentStatusEnum.PAID:
            self.payment_status = PaymentStatusEnum.REFUNDED
    
    def mark_no_show(self):
        """Mark appointment as no-show"""
        if self.status != AppointmentStatusEnum.CONFIRMED:
            raise ValueError("Only confirmed appointments can be marked as no-show")
        self.status = AppointmentStatusEnum.NO_SHOW
    
    def mark_paid(self):
        """Mark appointment as paid"""
        self.payment_status = PaymentStatusEnum.PAID
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, scheduled_start={self.scheduled_start}, status={self.status.value})>"
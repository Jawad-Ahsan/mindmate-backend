"""
Specialist Appointment Schemas - Enhanced Filtering and Management
================================================================
Pydantic models for specialist appointment filtering, patient management, and session tracking.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum

# ============================================================================
# ENUMERATIONS
# ============================================================================

class AppointmentFilterStatus(str, Enum):
    """Enhanced appointment status for filtering"""
    PENDING_APPROVAL = "pending_approval"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    ALL = "all"

class PatientStatus(str, Enum):
    """Patient status for specialist management"""
    NEW = "new"
    ACTIVE = "active"
    FOLLOW_UP = "follow_up"
    DISCHARGED = "discharged"
    ALL = "all"

class SessionFilterType(str, Enum):
    """Session filtering options"""
    TODAY = "today"
    UPCOMING = "upcoming"
    COMPLETED = "completed"
    ALL = "all"

# ============================================================================
# REQUEST MODELS
# ============================================================================

class AppointmentFilterRequest(BaseModel):
    """Request model for filtering appointments"""
    status: Optional[AppointmentFilterStatus] = Field(
        default=AppointmentFilterStatus.ALL,
        description="Filter by appointment status"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter appointments from this date"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter appointments until this date"
    )
    patient_type: Optional[PatientStatus] = Field(
        default=None,
        description="Filter by patient type"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Results per page")

class PatientFilterRequest(BaseModel):
    """Request model for filtering patients"""
    status: Optional[PatientStatus] = Field(
        default=PatientStatus.ALL,
        description="Filter by patient status"
    )
    search_query: Optional[str] = Field(
        default=None,
        description="Search by patient name or email"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Results per page")

class SessionFilterRequest(BaseModel):
    """Request model for filtering sessions"""
    filter_type: SessionFilterType = Field(
        default=SessionFilterType.ALL,
        description="Type of session filter"
    )
    date_from: Optional[datetime] = Field(
        default=None,
        description="Filter sessions from this date"
    )
    date_to: Optional[datetime] = Field(
        default=None,
        description="Filter sessions until this date"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Results per page")

class UpdateAppointmentStatusRequest(BaseModel):
    """Request model for updating appointment status"""
    new_status: AppointmentFilterStatus = Field(description="New appointment status")
    notes: Optional[str] = Field(default=None, description="Specialist notes")
    session_notes: Optional[str] = Field(default=None, description="Session notes for completed appointments")

class UpdatePatientStatusRequest(BaseModel):
    """Request model for updating patient status"""
    new_status: PatientStatus = Field(description="New patient status")
    notes: Optional[str] = Field(default=None, description="Specialist notes")
    next_followup_date: Optional[datetime] = Field(default=None, description="Next follow-up date")

class AddSessionNotesRequest(BaseModel):
    """Request model for adding session notes"""
    notes: str = Field(description="Session notes")
    mood_rating: Optional[int] = Field(default=None, ge=1, le=10, description="Patient mood rating (1-10)")
    progress_notes: Optional[str] = Field(default=None, description="Progress notes")
    next_steps: Optional[str] = Field(default=None, description="Next steps for patient")

# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PatientSummary(BaseModel):
    """Patient summary for specialist view"""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    status: PatientStatus
    last_session_date: Optional[datetime] = None
    next_followup_date: Optional[datetime] = None
    total_sessions: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AppointmentSummary(BaseModel):
    """Appointment summary for specialist view"""
    id: str
    patient_id: str
    patient_name: str
    patient_email: str
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    status: AppointmentFilterStatus
    appointment_type: str
    fee: Decimal
    notes: Optional[str] = None
    session_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SessionSummary(BaseModel):
    """Session summary for specialist view"""
    id: str
    appointment_id: str
    patient_name: str
    session_date: datetime
    status: str
    notes: Optional[str] = None
    mood_rating: Optional[int] = None
    progress_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class FilteredAppointmentsResponse(BaseModel):
    """Response model for filtered appointments"""
    appointments: List[AppointmentSummary]
    total_count: int
    page: int
    size: int
    has_more: bool
    filters_applied: Dict[str, Any]

class FilteredPatientsResponse(BaseModel):
    """Response model for filtered patients"""
    patients: List[PatientSummary]
    total_count: int
    page: int
    size: int
    has_more: bool
    filters_applied: Dict[str, Any]

class FilteredSessionsResponse(BaseModel):
    """Response model for filtered sessions"""
    sessions: List[SessionSummary]
    total_count: int
    page: int
    size: int
    has_more: bool
    filters_applied: Dict[str, Any]

class StatusUpdateResponse(BaseModel):
    """Response model for status updates"""
    success: bool
    message: str
    updated_item: Dict[str, Any]
    timestamp: datetime

# ============================================================================
# STATISTICS MODELS
# ============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics for specialist"""
    total_appointments: int
    pending_approvals: int
    scheduled_appointments: int
    completed_sessions: int
    total_patients: int
    new_patients: int
    active_patients: int
    today_sessions: int
    upcoming_sessions: int

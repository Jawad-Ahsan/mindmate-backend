"""
SMA Schemas - Pydantic Models for Specialist Matching Agent
==========================================================
Request/Response schemas for specialist search, matching, and appointment booking
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid

# ============================================================================
# ENUMERATIONS
# ============================================================================

class ConsultationMode(str, Enum):
    """Consultation delivery methods"""
    ONLINE = "online"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"

class SortOption(str, Enum):
    """Sort options for specialist search"""
    BEST_MATCH = "best_match"
    FEE_LOW = "fee_low"
    FEE_HIGH = "fee_high"
    RATING_HIGH = "rating_high"
    EXPERIENCE_HIGH = "experience_high"
    AVAILABILITY_SOON = "availability_soon"

class AppointmentStatus(str, Enum):
    """Appointment status"""
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    CANCELLED_BY_PATIENT = "cancelled_by_patient"
    CANCELLED_BY_SPECIALIST = "cancelled_by_specialist"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

# ============================================================================
# PATIENT ENDPOINTS - REQUEST SCHEMAS
# ============================================================================

class SpecialistSearchRequest(BaseModel):
    """Request schema for specialist search by patients"""
    
    # Search parameters
    query: Optional[str] = Field(None, description="Free text search query")
    specialist_type: Optional[str] = Field(None, description="Type of specialist")
    consultation_mode: Optional[ConsultationMode] = Field(None, description="Preferred consultation mode")
    city: Optional[str] = Field(None, description="City for in-person consultations")
    languages: Optional[List[str]] = Field(None, description="Preferred languages")
    specializations: Optional[List[str]] = Field(None, description="Required specializations")
    budget_max: Optional[float] = Field(None, ge=0, description="Maximum budget in PKR")
    
    # Sorting and pagination
    sort_by: SortOption = Field(SortOption.BEST_MATCH, description="Sort order")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Results per page")
    
    # Availability constraints
    available_from: Optional[datetime] = Field(None, description="Earliest available date")
    available_to: Optional[datetime] = Field(None, description="Latest available date")

class BookAppointmentRequest(BaseModel):
    """Request schema for booking appointment"""
    
    specialist_id: uuid.UUID = Field(..., description="Specialist ID")
    scheduled_start: datetime = Field(..., description="Appointment start time")
    scheduled_end: datetime = Field(..., description="Appointment end time")
    consultation_mode: ConsultationMode = Field(..., description="Consultation mode")
    notes: Optional[str] = Field(None, description="Patient notes")

class CancelAppointmentRequest(BaseModel):
    """Request schema for cancelling appointment"""
    
    appointment_id: uuid.UUID = Field(..., description="Appointment ID")
    reason: Optional[str] = Field(None, description="Cancellation reason")

class RescheduleAppointmentRequest(BaseModel):
    """Request schema for rescheduling appointment"""
    
    appointment_id: uuid.UUID = Field(..., description="Appointment ID")
    new_scheduled_start: datetime = Field(..., description="New appointment start time")
    new_scheduled_end: datetime = Field(..., description="New appointment end time")
    reason: Optional[str] = Field(None, description="Reschedule reason")

# ============================================================================
# SPECIALIST ENDPOINTS - REQUEST SCHEMAS
# ============================================================================

class UpdateAppointmentStatusRequest(BaseModel):
    """Request schema for updating appointment status"""
    
    appointment_id: uuid.UUID = Field(..., description="Appointment ID")
    status: AppointmentStatus = Field(..., description="New appointment status")
    notes: Optional[str] = Field(None, description="Specialist notes")

class CancelAppointmentBySpecialistRequest(BaseModel):
    """Request schema for specialist cancelling appointment"""
    
    appointment_id: uuid.UUID = Field(..., description="Appointment ID")
    reason: Optional[str] = Field(None, description="Cancellation reason")

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class SpecialistBasicInfo(BaseModel):
    """Basic specialist information for search results"""
    
    id: uuid.UUID
    name: str
    type: str
    rating: float
    specializations: List[str]
    fee: float
    languages: List[str]
    city: Optional[str]
    consultation_mode: ConsultationMode
    match_score: Optional[float]
    
    class Config:
        from_attributes = True

class SpecialistDetailedInfo(BaseModel):
    """Detailed specialist information for public profile"""
    
    id: uuid.UUID
    name: str
    type: str
    rating: float
    specializations: List[str]
    fee: float
    languages: List[str]
    city: Optional[str]
    consultation_mode: ConsultationMode
    bio: str
    experience_years: int
    certifications: List[str]
    education: List[str]
    availability_slots: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class AppointmentInfo(BaseModel):
    """Appointment information"""
    
    id: uuid.UUID
    patient_id: uuid.UUID
    specialist_id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime
    consultation_mode: ConsultationMode
    fee: float
    status: AppointmentStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PatientPublicProfile(BaseModel):
    """Patient public profile for specialists"""
    
    id: uuid.UUID
    first_name: str
    last_name: str
    age: Optional[int]
    gender: Optional[str]
    city: Optional[str]
    consultation_history: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class PatientReportInfo(BaseModel):
    """Patient report information from PIMA"""
    
    patient_id: uuid.UUID
    report_available: bool
    report_generated_at: Optional[datetime]
    report_type: Optional[str]
    report_summary: Optional[str]
    risk_level: Optional[str]
    recommendations: Optional[List[str]]
    generated_by: Optional[str]

# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class SpecialistSearchResponse(BaseModel):
    """Response schema for specialist search"""
    
    specialists: List[SpecialistBasicInfo]
    total_count: int
    page: int
    size: int
    has_more: bool
    search_criteria: Dict[str, Any]

class SpecialistProfileResponse(BaseModel):
    """Response schema for specialist public profile"""
    
    specialist: SpecialistDetailedInfo
    message: str

class AppointmentResponse(BaseModel):
    """Response schema for appointment operations"""
    
    appointment: AppointmentInfo
    message: str

class AppointmentListResponse(BaseModel):
    """Response schema for appointment list"""
    
    appointments: List[AppointmentInfo]
    total_count: int
    page: int
    size: int
    has_more: bool

class PatientProfileResponse(BaseModel):
    """Response schema for patient public profile"""
    
    patient: PatientPublicProfile
    message: str

class PatientReportResponse(BaseModel):
    """Response schema for patient report"""
    
    report: PatientReportInfo
    message: str

# ============================================================================
# ERROR SCHEMAS
# ============================================================================

class SMAError(BaseModel):
    """Standard error response"""
    
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# ============================================================================
# UTILITY SCHEMAS
# ============================================================================

class DefaultPreferences(BaseModel):
    """Default preferences when user doesn't specify"""
    
    consultation_mode: ConsultationMode = ConsultationMode.ONLINE
    languages: List[str] = ["English", "Urdu"]
    budget_max: Optional[float] = None
    city: Optional[str] = None
    specialist_type: Optional[str] = None
    specializations: Optional[List[str]] = None

class HealthCheckResponse(BaseModel):
    """Health check response"""
    
    status: str
    service: str
    timestamp: datetime
    version: str = "1.0.0"
    message: str

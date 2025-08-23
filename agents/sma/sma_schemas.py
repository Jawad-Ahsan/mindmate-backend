from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

class ConsultationMode(str, Enum):
    ONLINE = "online"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"

class SortOption(str, Enum):
    BEST_MATCH = "best_match"
    RATING_HIGH = "rating_high"
    FEE_LOW = "fee_low"
    EXPERIENCE_HIGH = "experience_high"

class SlotStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    HELD = "held"
    EXPIRED = "expired"

class AppointmentStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

# Request Models
class DefaultPreferences(BaseModel):
    consultation_mode: ConsultationMode = ConsultationMode.ONLINE
    languages: List[str] = ["English"]
    specializations: List[str] = []
    budget_max: Optional[float] = None
    city: Optional[str] = None
    sort_by: SortOption = SortOption.BEST_MATCH
    specialist_type: Optional[str] = None

class SpecialistSearchRequest(BaseModel):
    query: Optional[str] = None
    specialist_type: Optional[str] = None
    consultation_mode: Optional[ConsultationMode] = ConsultationMode.ONLINE
    languages: Optional[List[str]] = None
    specializations: Optional[List[str]] = None
    budget_max: Optional[float] = None
    city: Optional[str] = None
    sort_by: Optional[SortOption] = SortOption.BEST_MATCH
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None
    page: int = 1
    size: int = 20

class TopSpecialistsRequest(BaseModel):
    consultation_mode: Optional[ConsultationMode] = ConsultationMode.ONLINE
    specializations: Optional[List[str]] = None
    city: Optional[str] = None
    limit: int = 5

class SlotHoldRequest(BaseModel):
    specialist_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    consultation_mode: ConsultationMode

class AppointmentConfirmRequest(BaseModel):
    slot_hold_id: uuid.UUID
    patient_id: uuid.UUID
    notes: Optional[str] = None

class AppointmentCancelRequest(BaseModel):
    appointment_id: uuid.UUID
    reason: Optional[str] = None

class AppointmentRescheduleRequest(BaseModel):
    appointment_id: uuid.UUID
    new_start_time: datetime
    new_end_time: datetime
    reason: Optional[str] = None

class BookAppointmentRequest(BaseModel):
    specialist_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    consultation_mode: ConsultationMode
    notes: Optional[str] = None

class RequestAppointmentRequest(BaseModel):
    specialist_id: uuid.UUID
    consultation_mode: ConsultationMode
    notes: Optional[str] = None

class CancelAppointmentRequest(BaseModel):
    appointment_id: uuid.UUID
    reason: Optional[str] = None

class RescheduleAppointmentRequest(BaseModel):
    appointment_id: uuid.UUID
    new_start_time: datetime
    new_end_time: datetime
    reason: Optional[str] = None

class UpdateAppointmentStatusRequest(BaseModel):
    appointment_id: uuid.UUID
    status: AppointmentStatus
    notes: Optional[str] = None

class CancelAppointmentBySpecialistRequest(BaseModel):
    appointment_id: uuid.UUID
    reason: Optional[str] = None

class SpecialistDetailedInfo(BaseModel):
    id: uuid.UUID
    full_name: str
    specialist_type: str
    years_experience: int
    city: str
    average_rating: float
    consultation_fee: float
    specializations: List[str]
    languages: List[str]
    consultation_mode: ConsultationMode
    bio: Optional[str] = None
    education: Optional[str] = None
    certifications: Optional[str] = None

class SpecialistBasicInfo(BaseModel):
    id: uuid.UUID
    full_name: str
    specialist_type: str
    years_experience: int
    city: str
    average_rating: float
    consultation_fee: float
    specializations: List[str]
    languages: List[str]

class PatientPublicProfile(BaseModel):
    id: uuid.UUID
    full_name: str
    age: Optional[int] = None
    city: str
    risk_level: Optional[str] = None

class PatientReportInfo(BaseModel):
    patient_id: uuid.UUID
    report_type: str
    report_data: Dict[str, Any]
    generated_at: datetime

class SpecialistProfileResponse(BaseModel):
    specialist: SpecialistDetailedInfo
    availability: List[Dict[str, Any]]
    reviews: List[Dict[str, Any]]

class AppointmentResponse(BaseModel):
    appointment: "AppointmentInfo"
    specialist_info: SpecialistBasicInfo
    patient_info: PatientPublicProfile

class PatientProfileResponse(BaseModel):
    patient: PatientPublicProfile
    medical_history: Optional[Dict[str, Any]] = None

class PatientReportResponse(BaseModel):
    report: PatientReportInfo
    specialist_notes: Optional[str] = None

class SMAError(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

# Response Models
class SpecialistSearchResponse(BaseModel):
    specialists: List[Dict[str, Any]]
    total_count: int
    page: int
    size: int
    total_pages: int

class TopSpecialistsResponse(BaseModel):
    specialists: List[Dict[str, Any]]
    total_count: int

class SlotHoldResponse(BaseModel):
    slot_hold_id: uuid.UUID
    specialist_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    consultation_mode: ConsultationMode
    expires_at: datetime

class AppointmentConfirmResponse(BaseModel):
    appointment_id: uuid.UUID
    specialist_id: uuid.UUID
    patient_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    consultation_mode: ConsultationMode
    status: AppointmentStatus
    fee: float

class RequestAppointmentResponse(BaseModel):
    appointment_id: uuid.UUID
    specialist_id: uuid.UUID
    patient_id: uuid.UUID
    consultation_mode: ConsultationMode
    status: AppointmentStatus
    notes: Optional[str] = None
    message: str

class AppointmentListResponse(BaseModel):
    appointments: List[Dict[str, Any]]
    total_count: int
    page: int
    size: int
    total_pages: int

class AppointmentInfo(BaseModel):
    id: uuid.UUID
    specialist_id: uuid.UUID
    patient_id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime
    consultation_mode: ConsultationMode
    status: AppointmentStatus
    fee: float
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database: str
    redis: str

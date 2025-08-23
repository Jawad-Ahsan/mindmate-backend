"""
Users Management Schema for Approving, Rejecting, suspending, deactivating etc of specialists, patients, admins for now
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Import enums from SQL models
from ..sql_models.specialist_models import (
    ApprovalStatusEnum, DocumentStatusEnum, DocumentTypeEnum,
    AvailabilityStatusEnum, EmailVerificationStatusEnum
)
from ..sql_models.patient_models import RecordStatusEnum
from ..sql_models.admin_models import AdminStatusEnum

# ============================================================================
# ENUMERATIONS
# ============================================================================

class ActionTypeEnum(str, Enum):
    """Types of actions that can be performed on users"""
    APPROVE = "approve"
    REJECT = "reject"
    SUSPEND = "suspend"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    UNSUSPEND = "unsuspend"

class UserTypeEnum(str, Enum):
    """Types of users that can be managed"""
    SPECIALIST = "specialist"
    PATIENT = "patient"
    ADMIN = "admin"

# ============================================================================
# BASE CONFIGURATION
# ============================================================================

class BaseModelConfig(BaseModel):
    """Base Pydantic model with V2 configuration"""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        extra='forbid'
    )

# ============================================================================
# SPECIALIST MANAGEMENT SCHEMAS
# ============================================================================

class SpecialistDocumentResponse(BaseModelConfig):
    """Response model for specialist documents"""
    id: uuid.UUID
    document_type: DocumentTypeEnum
    document_name: str
    file_path: str
    file_size: int
    mime_type: str
    verification_status: DocumentStatusEnum
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    upload_date: datetime
    expiry_date: Optional[datetime] = None
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2)

class SpecialistApprovalDataResponse(BaseModelConfig):
    """Response model for specialist approval data"""
    id: uuid.UUID
    license_number: Optional[str] = None
    license_issuing_authority: Optional[str] = None
    license_issue_date: Optional[datetime] = None
    license_expiry_date: Optional[datetime] = None
    highest_degree: Optional[str] = None
    university_name: Optional[str] = None
    graduation_year: Optional[int] = None
    professional_memberships: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    cnic: Optional[str] = None
    passport_number: Optional[str] = None
    submission_date: datetime
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    background_check_status: str
    background_check_date: Optional[datetime] = None
    background_check_notes: Optional[str] = None
    documents: List[SpecialistDocumentResponse] = []

class SpecialistProfileResponse(BaseModelConfig):
    """Complete specialist profile response including documents"""
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: str
    specialist_type: str
    years_experience: int
    city: str
    address: Optional[str] = None
    clinic_name: Optional[str] = None
    consultation_fee: Optional[float] = None
    bio: Optional[str] = None
    languages_spoken: Optional[List[str]] = None
    availability_status: AvailabilityStatusEnum
    approval_status: ApprovalStatusEnum
    average_rating: float
    total_reviews: int
    total_appointments: int
    profile_image_url: Optional[str] = None
    website_url: Optional[str] = None
    social_media_links: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    # Auth info
    is_email_verified: bool
    last_login_at: Optional[datetime] = None
    
    # Approval data
    approval_data: Optional[SpecialistApprovalDataResponse] = None
    
    # Specializations
    specializations: List[Dict[str, Any]] = []
    
    @property
    def full_name(self) -> str:
        """Full name for display"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_approved(self) -> bool:
        """Check if specialist is approved"""
        return self.approval_status == ApprovalStatusEnum.APPROVED
    
    @property
    def can_practice(self) -> bool:
        """Check if specialist can practice"""
        return (
            self.is_approved and 
            self.is_email_verified and
            self.availability_status == AvailabilityStatusEnum.ACCEPTING_NEW_PATIENTS
        )

class SpecialistActionRequest(BaseModelConfig):
    """Request model for specialist actions (approve, reject, suspend)"""
    specialist_id: uuid.UUID
    action: ActionTypeEnum
    reason: str = Field(..., min_length=10, max_length=1000)
    admin_notes: Optional[str] = Field(None, max_length=2000)
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Validate reason is not empty and has meaningful content"""
        if not v or not v.strip():
            raise ValueError("Reason is required and cannot be empty")
        if len(v.strip()) < 10:
            raise ValueError("Reason must be at least 10 characters long")
        return v.strip()

class SpecialistActionResponse(BaseModelConfig):
    """Response model for specialist actions"""
    specialist_id: uuid.UUID
    action: ActionTypeEnum
    previous_status: ApprovalStatusEnum
    new_status: ApprovalStatusEnum
    reason: str
    admin_notes: Optional[str] = None
    action_performed_by: uuid.UUID
    action_performed_at: datetime
    success: bool = True
    message: str

# ============================================================================
# PATIENT MANAGEMENT SCHEMAS
# ============================================================================

class PatientProfileResponse(BaseModelConfig):
    """Patient profile response for management"""
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: datetime
    gender: str
    primary_language: str
    city: str
    district: Optional[str] = None
    province: Optional[str] = None
    country: str
    record_status: RecordStatusEnum
    assigned_therapist_id: Optional[str] = None
    intake_completed_date: Optional[datetime] = None
    last_contact_date: Optional[datetime] = None
    next_appointment_date: Optional[datetime] = None
    accepts_terms_and_conditions: bool
    created_at: datetime
    updated_at: datetime
    
    # Auth info
    is_active: bool
    is_verified: bool
    is_locked: bool
    last_login: Optional[datetime] = None
    
    # Computed properties
    age: Optional[int] = None
    
    @property
    def full_name(self) -> str:
        """Full name for display"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self) -> str:
        """Format full address as string"""
        parts = [self.city, self.district, self.province, self.country]
        return ", ".join(filter(None, parts))

class PatientActionRequest(BaseModelConfig):
    """Request model for patient actions (activate, deactivate)"""
    patient_id: uuid.UUID
    action: ActionTypeEnum
    reason: str = Field(..., min_length=10, max_length=1000)
    admin_notes: Optional[str] = Field(None, max_length=2000)
    
    @field_validator('action')
    @classmethod
    def validate_patient_action(cls, v: ActionTypeEnum) -> ActionTypeEnum:
        """Validate that only patient-appropriate actions are used"""
        if v not in [ActionTypeEnum.ACTIVATE, ActionTypeEnum.DEACTIVATE, ActionTypeEnum.SUSPEND, ActionTypeEnum.UNSUSPEND]:
            raise ValueError("Invalid action for patient management")
        return v
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        """Validate reason is not empty and has meaningful content"""
        if not v or not v.strip():
            raise ValueError("Reason is required and cannot be empty")
        if len(v.strip()) < 10:
            raise ValueError("Reason must be at least 10 characters long")
        return v.strip()

class PatientActionResponse(BaseModelConfig):
    """Response model for patient actions"""
    patient_id: uuid.UUID
    action: ActionTypeEnum
    previous_status: RecordStatusEnum
    new_status: RecordStatusEnum
    reason: str
    admin_notes: Optional[str] = None
    action_performed_by: uuid.UUID
    action_performed_at: datetime
    success: bool = True
    message: str

# ============================================================================
# SEARCH AND FILTER SCHEMAS
# ============================================================================

class SpecialistSearchFilters(BaseModelConfig):
    """Filters for searching specialists"""
    approval_status: Optional[ApprovalStatusEnum] = None
    specialist_type: Optional[str] = None
    city: Optional[str] = None
    has_documents: Optional[bool] = None
    email_verified: Optional[bool] = None
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    has_license: Optional[bool] = None
    background_check_status: Optional[str] = None

class PatientSearchFilters(BaseModelConfig):
    """Filters for searching patients"""
    record_status: Optional[RecordStatusEnum] = None
    city: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    has_therapist: Optional[bool] = None
    intake_completed: Optional[bool] = None

class PaginationParams(BaseModelConfig):
    """Pagination parameters"""
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query"""
        return (self.page - 1) * self.page_size

class SearchResponse(BaseModelConfig):
    """Generic search response with pagination"""
    items: List[Any]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page"""
        return self.page < self.total_pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page"""
        return self.page > 1

# ============================================================================
# AUDIT AND LOGGING SCHEMAS
# ============================================================================

class UserActionLog(BaseModelConfig):
    """Log entry for user management actions"""
    id: uuid.UUID
    user_id: uuid.UUID
    user_type: UserTypeEnum
    action: ActionTypeEnum
    previous_status: str
    new_status: str
    reason: str
    admin_notes: Optional[str] = None
    performed_by: uuid.UUID
    performed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class UserManagementStats(BaseModelConfig):
    """Statistics for user management dashboard"""
    total_specialists: int
    pending_specialists: int
    approved_specialists: int
    rejected_specialists: int
    suspended_specialists: int
    total_patients: int
    active_patients: int
    inactive_patients: int
    suspended_patients: int
    recent_actions: List[UserActionLog] = []

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "ActionTypeEnum",
    "UserTypeEnum",
    
    # Specialist Schemas
    "SpecialistDocumentResponse",
    "SpecialistApprovalDataResponse", 
    "SpecialistProfileResponse",
    "SpecialistActionRequest",
    "SpecialistActionResponse",
    
    # Patient Schemas
    "PatientProfileResponse",
    "PatientActionRequest", 
    "PatientActionResponse",
    
    # Search and Filter Schemas
    "SpecialistSearchFilters",
    "PatientSearchFilters",
    "PaginationParams",
    "SearchResponse",
    
    # Audit and Logging Schemas
    "UserActionLog",
    "UserManagementStats",
]


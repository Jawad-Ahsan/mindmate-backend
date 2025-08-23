"""
Patient Profile Pydantic Schemas
================================
Modular, reusable, and composable schemas for different patient profile access levels:
- Public: Accessible to assigned specialists (clinical info, risk assessment, appointments)
- Protected: Accessible to admins only (account management, non-sensitive info)
- Private: Accessible to patient only (complete detailed profile)
"""

from pydantic import BaseModel, Field, ConfigDict, computed_field
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from enum import Enum
import uuid

# Import enums from your patient models
from models.sql_models.patient_models import (
    GenderEnum, RecordStatusEnum, LanguageEnum, ConsultationModeEnum,
    RiskLevel, TherapyModalityEnum, TherapyApproachEnum, PaymentMethodEnum,
    UrgencyLevelEnum
)
from models.sql_models.appointments_model import AppointmentStatusEnum, AppointmentTypeEnum, PaymentStatusEnum


# ============================================================================
# BASE COMPONENT SCHEMAS (Reusable Building Blocks)
# ============================================================================

class BasePatientInfo(BaseModel):
    """Core patient identification information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    full_name: str = Field(description="Patient's full name")
    age: Optional[int] = Field(description="Patient's age in years")
    record_status: RecordStatusEnum

class ContactInfo(BaseModel):
    """Patient contact information"""
    model_config = ConfigDict(from_attributes=True)
    
    email: Optional[str] = None
    phone: Optional[str] = None

class LocationInfo(BaseModel):
    """Patient location information"""
    model_config = ConfigDict(from_attributes=True)
    
    city: str
    district: Optional[str] = None
    province: Optional[str] = None
    country: str = "Pakistan"

class AppointmentSummary(BaseModel):
    """Summary appointment information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime
    appointment_type: AppointmentTypeEnum
    status: AppointmentStatusEnum
    payment_status: PaymentStatusEnum
    fee: float
    specialist_name: Optional[str] = None
    
    @computed_field
    @property
    def duration_minutes(self) -> int:
        return int((self.scheduled_end - self.scheduled_start).total_seconds() / 60)

class RiskAssessmentSummary(BaseModel):
    """Patient risk assessment information"""
    model_config = ConfigDict(from_attributes=True)
    
    risk_level: Optional[RiskLevel] = None
    risk_value: Optional[float] = Field(None, ge=0.0, le=1.0)
    assessment_timestamp: Optional[datetime] = None
    requires_immediate_attention: bool = False
    safety_plan_created: bool = False
    follow_up_required: bool = False
    follow_up_timeframe: Optional[str] = None

class PresentingConcernSummary(BaseModel):
    """Summary of presenting concerns"""
    model_config = ConfigDict(from_attributes=True)
    
    presenting_concern: Optional[str] = None
    hpi_severity: Optional[int] = Field(None, ge=1, le=10)
    priority_level: UrgencyLevelEnum = UrgencyLevelEnum.STANDARD
    completion_percentage: Optional[float] = None
    completion_timestamp: Optional[datetime] = None

class PreferencesSummary(BaseModel):
    """Patient preferences summary"""
    model_config = ConfigDict(from_attributes=True)
    
    consultation_mode: Optional[ConsultationModeEnum] = None
    urgency_level: UrgencyLevelEnum = UrgencyLevelEnum.STANDARD
    max_budget: Optional[float] = None
    preferred_city: Optional[str] = None

# ============================================================================
# DETAILED COMPONENT SCHEMAS (For Private Profile)
# ============================================================================

class DetailedPersonalInfo(BaseModel):
    """Detailed personal information"""
    model_config = ConfigDict(from_attributes=True)
    
    first_name: str
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    primary_language: LanguageEnum
    full_address: Optional[str] = None

class AuthenticationInfo(BaseModel):
    """Authentication and security information (non-sensitive)"""
    model_config = ConfigDict(from_attributes=True)
    
    is_active: bool = True
    is_verified: bool = False
    is_locked: bool = False
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    two_factor_enabled: bool = False
    theme_preference: str = "light"
    avatar_url: Optional[str] = None

class DetailedPreferences(BaseModel):
    """Detailed patient preferences"""
    model_config = ConfigDict(from_attributes=True)
    
    location_preferences: Dict[str, Any] = Field(default_factory=dict)
    cultural_preferences: Dict[str, Any] = Field(default_factory=dict)
    therapy_preferences: Dict[str, Any] = Field(default_factory=dict)
    financial_preferences: Dict[str, Any] = Field(default_factory=dict)
    specialist_preferences: Dict[str, Any] = Field(default_factory=dict)
    availability_preferences: Dict[str, Any] = Field(default_factory=dict)
    priority_weights: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None

class MedicalHistory(BaseModel):
    """Patient medical history"""
    model_config = ConfigDict(from_attributes=True)
    
    # Past Psychiatric History
    past_psych_dx: Optional[str] = None
    past_psych_treatment: Optional[str] = None
    hospitalizations: Optional[str] = None
    ect_history: Optional[str] = None
    
    # Current Medications & Allergies
    current_meds: Dict[str, Any] = Field(default_factory=dict)
    med_allergies: Optional[str] = None
    otc_supplements: Optional[str] = None
    medication_adherence: Optional[str] = None
    
    # Medical History
    medical_history_summary: Optional[str] = None
    chronic_illnesses: Optional[str] = None
    neurological_problems: Optional[str] = None
    head_injury: Optional[str] = None
    seizure_history: Optional[str] = None
    pregnancy_status: Optional[str] = None
    
    # Substance & Alcohol Use
    alcohol_use: Optional[str] = None
    drug_use: Optional[str] = None
    prescription_drug_abuse: Optional[str] = None
    last_use_date: Optional[str] = None
    substance_treatment: Optional[str] = None
    tobacco_use: Optional[str] = None
    
    # Cultural, Spiritual Factors
    cultural_background: Optional[str] = None
    cultural_beliefs: Optional[str] = None
    spiritual_supports: Optional[str] = None
    family_mental_health_stigma: Optional[str] = None
    
    # Metadata
    completion_timestamp: Optional[datetime] = None
    sections_completed: List[str] = Field(default_factory=list)
    completion_percentage: Optional[float] = None

class DetailedPresentingConcerns(BaseModel):
    """Detailed presenting concerns"""
    model_config = ConfigDict(from_attributes=True)
    
    presenting_concern: Optional[str] = None
    presenting_onset: Optional[str] = None
    
    # History of Present Illness (HPI)
    hpi_onset: Optional[str] = None
    hpi_duration: Optional[str] = None
    hpi_course: Optional[str] = None
    hpi_severity: Optional[int] = Field(None, ge=1, le=10)
    hpi_frequency: Optional[str] = None
    hpi_triggers: Optional[str] = None
    
    # Functional Impact
    hpi_impact_work: Optional[str] = None
    hpi_impact_relationships: Optional[str] = None
    hpi_prior_episodes: Optional[str] = None
    function_ADL: Optional[str] = None
    social_activities: Optional[str] = None
    
    # Session metadata
    conversation_complete: bool = False
    total_questions_asked: int = 0
    completion_timestamp: Optional[datetime] = None
    session_notes: Optional[str] = None
    priority_level: UrgencyLevelEnum = UrgencyLevelEnum.STANDARD
    completion_percentage: Optional[float] = None

class DetailedRiskAssessment(BaseModel):
    """Detailed risk assessment"""
    model_config = ConfigDict(from_attributes=True)
    
    # Suicide Risk Assessment
    suicide_ideation: Optional[bool] = None
    suicide_plan: Optional[str] = None
    suicide_intent: Optional[bool] = None
    past_attempts: Optional[str] = None
    self_harm_history: Optional[str] = None
    
    # Violence Risk Assessment
    homicidal_thoughts: Optional[bool] = None
    access_means: Optional[str] = None
    
    # Protective Factors
    protective_factors: Optional[str] = None
    
    # Assessment Results
    risk_level: Optional[RiskLevel] = None
    risk_value: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_reason: Optional[str] = None
    
    # Assessment Metadata
    assessment_timestamp: datetime
    assessed_by: Optional[str] = None
    assessment_type: str = "initial"
    is_current: bool = True
    
    # Follow-up Information
    requires_immediate_attention: bool = False
    safety_plan_created: bool = False
    follow_up_required: bool = False
    follow_up_timeframe: Optional[str] = None
    
    @computed_field
    @property
    def is_high_risk(self) -> bool:
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] if self.risk_level else False
    
    @computed_field
    @property
    def requires_crisis_intervention(self) -> bool:
        return (
            self.risk_level == RiskLevel.CRITICAL or 
            self.requires_immediate_attention or
            (self.suicide_ideation and self.suicide_intent)
        )

class DetailedAppointment(BaseModel):
    """Detailed appointment information"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    scheduled_start: datetime
    scheduled_end: datetime
    appointment_type: AppointmentTypeEnum
    status: AppointmentStatusEnum
    fee: float
    payment_status: PaymentStatusEnum
    notes: Optional[str] = None
    session_notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    specialist_id: uuid.UUID
    specialist_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def duration_minutes(self) -> int:
        return int((self.scheduled_end - self.scheduled_start).total_seconds() / 60)
    
    @computed_field
    @property
    def is_active(self) -> bool:
        return self.status in [AppointmentStatusEnum.SCHEDULED, AppointmentStatusEnum.CONFIRMED]

# ============================================================================
# MAIN PROFILE SCHEMAS
# ============================================================================

class PatientPublicProfile(BaseModel):
    """
    Public Profile - Accessible to assigned specialists
    Includes: clinical info, risk assessment, appointment history, contact info
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "patient_info": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "full_name": "Ahmad Hassan",
                    "age": 28,
                    "record_status": "active"
                },
                "contact_info": {
                    "email": "ahmad@example.com",
                    "phone": "+92300123456"
                },
                "risk_assessment": {
                    "risk_level": "moderate",
                    "risk_value": 0.3,
                    "requires_immediate_attention": False,
                    "assessment_timestamp": "2024-01-15T10:30:00Z"
                },
                "next_appointment_date": "2024-02-01T14:00:00Z"
            }
        }
    )
    
    # Basic patient info
    patient_info: BasePatientInfo
    contact_info: ContactInfo
    
    # Clinical information
    risk_assessment: Optional[RiskAssessmentSummary] = None
    presenting_concerns: Optional[PresentingConcernSummary] = None
    
    # Appointment information
    next_appointment_date: Optional[datetime] = None
    appointment_history: List[AppointmentSummary] = Field(default_factory=list)
    
    # Treatment context
    assigned_therapist_id: Optional[str] = None
    intake_completed_date: Optional[date] = None
    last_contact_date: Optional[date] = None
    
    # Patient report placeholder (will be provided by SMA)
    patient_report_available: bool = Field(
        default=False, 
        description="Indicates if patient report is available from Specialists Matching Agent"
    )
    
    

class PatientProtectedProfile(BaseModel):
    """
    Protected Profile - Accessible to admins only
    Includes: account management info, status management, forum management
    Excludes: sensitive health data
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "patient_info": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "full_name": "Ahmad Hassan",
                    "age": 28,
                    "record_status": "active"
                },
                "contact_info": {
                    "email": "ahmad@example.com",
                    "phone": "+92300123456"
                },
                "location_info": {
                    "city": "Rawalpindi",
                    "province": "Punjab",
                    "country": "Pakistan"
                },
                "auth_info": {
                    "is_active": True,
                    "is_verified": True,
                    "last_login": "2024-01-20T09:15:00Z"
                }
            }
        }
    )
    
    # Basic patient info
    patient_info: BasePatientInfo
    contact_info: ContactInfo
    location_info: LocationInfo
    
    # Account management
    auth_info: AuthenticationInfo
    preferences: PreferencesSummary
    
    # Status management
    intake_completed_date: Optional[date] = None
    last_contact_date: Optional[date] = None
    assigned_therapist_id: Optional[str] = None
    
    # Forum management (placeholder for forum-related fields)
    forum_activity_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary of forum participation for management purposes"
    )
    
    # Account metadata
    created_at: datetime
    updated_at: datetime
    accepts_terms_and_conditions: bool = False
    
    

class PatientPrivateProfile(BaseModel):
    """
    Private Profile - Accessible to patient only
    Includes: complete detailed profile with all information
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "personal_info": {
                    "first_name": "Ahmad",
                    "last_name": "Hassan",
                    "date_of_birth": "1995-05-15",
                    "gender": "male",
                    "primary_language": "urdu"
                },
                "contact_info": {
                    "email": "ahmad@example.com",
                    "phone": "+92300123456"
                },
                "preferences": {
                    "therapy_preferences": {
                        "modality": "individual",
                        "approach": "cognitive_behavioral_therapy"
                    },
                    "consultation_mode": "virtual",
                    "max_budget": 5000.0
                }
            }
        }
    )
    
    # Complete personal information
    personal_info: DetailedPersonalInfo
    contact_info: ContactInfo
    location_info: LocationInfo
    
    # Authentication and security
    auth_info: AuthenticationInfo
    
    # Complete preferences
    preferences: DetailedPreferences
    
    # Complete medical and psychiatric history
    medical_history: Optional[MedicalHistory] = None
    
    # Complete presenting concerns
    presenting_concerns: Optional[DetailedPresentingConcerns] = None
    
    # Complete risk assessments (list of all assessments)
    risk_assessments: List[DetailedRiskAssessment] = Field(default_factory=list)
    current_risk_assessment: Optional[DetailedRiskAssessment] = None
    
    # Complete appointment history
    appointments: List[DetailedAppointment] = Field(default_factory=list)
    next_appointment: Optional[DetailedAppointment] = None
    
    # Treatment management
    assigned_therapist_id: Optional[str] = None
    intake_completed_date: Optional[date] = None
    last_contact_date: Optional[date] = None
    
    # Account metadata
    created_at: datetime
    updated_at: datetime
    accepts_terms_and_conditions: bool = False
    
    # Profile completion status
    profile_completion_percentage: Optional[float] = Field(
        None,
        description="Overall profile completion percentage"
    )
    
    

# ============================================================================
# RESPONSE WRAPPER SCHEMAS
# ============================================================================

class PatientProfileResponse(BaseModel):
    """Generic response wrapper for patient profiles"""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool = True
    message: str = "Profile retrieved successfully"
    data: Union[PatientPublicProfile, PatientProtectedProfile, PatientPrivateProfile]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PatientReportInfo(BaseModel):
    """Information about patient report from SMA"""
    model_config = ConfigDict(from_attributes=True)
    
    report_available: bool = False
    report_generated_date: Optional[datetime] = None
    report_type: Optional[str] = None
    report_url: Optional[str] = None  # URL to download PDF report
    generated_by: str = "Specialists Matching Agent (SMA)"

# ============================================================================
# UTILITY SCHEMAS FOR PROFILE UPDATES
# ============================================================================

class ProfileUpdateRequest(BaseModel):
    """Base schema for profile update requests"""
    model_config = ConfigDict(from_attributes=True)
    
    update_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ContactInfoUpdate(ProfileUpdateRequest):
    """Schema for updating contact information"""
    update_type: str = "contact_info"
    email: Optional[str] = None
    phone: Optional[str] = None

class PreferencesUpdate(ProfileUpdateRequest):
    """Schema for updating preferences"""
    update_type: str = "preferences"
    preferences_data: Dict[str, Any] = Field(default_factory=dict)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Component Schemas
    'BasePatientInfo',
    'ContactInfo',
    'LocationInfo', 
    'AppointmentSummary',
    'RiskAssessmentSummary',
    'PresentingConcernSummary',
    'PreferencesSummary',
    'DetailedPersonalInfo',
    'AuthenticationInfo',
    'DetailedPreferences',
    'MedicalHistory',
    'DetailedPresentingConcerns',
    'DetailedRiskAssessment',
    'DetailedAppointment',
    
    # Main Profile Schemas
    'PatientPublicProfile',
    'PatientProtectedProfile', 
    'PatientPrivateProfile',
    
    # Response Schemas
    'PatientProfileResponse',
    'PatientReportInfo',
    
    # Update Schemas
    'ProfileUpdateRequest',
    'ContactInfoUpdate',
    'PreferencesUpdate',
]
"""
Patient Pydantic Models - Request/Response Schemas
=================================================
Pydantic models for patient data validation, serialization, and API schemas.
These models complement the SQLAlchemy models and provide type safety for API operations.
"""

from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from decimal import Decimal
import uuid
import re

# Import enums from your SQLAlchemy models
from models.sql_models.patient_models import (
    GenderEnum, RecordStatusEnum, LanguageEnum, ConsultationModeEnum,
    RiskLevel, TherapyModalityEnum, TherapyApproachEnum, PaymentMethodEnum,
    UrgencyLevelEnum
)

# ============================================================================
# BASE PYDANTIC CONFIGURATION
# ============================================================================

class BasePatientModel(BaseModel):
    """Base Pydantic model with common configuration for patient schemas"""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        populate_by_name=True
    )

# ============================================================================
# CORE PATIENT SCHEMAS
# ============================================================================

class PatientCreateRequest(BasePatientModel):
    """Schema for creating a new patient"""
    
    # Required fields
    first_name: str = Field(..., min_length=1, max_length=100, description="Patient's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Patient's last name")
    email: str = Field(..., max_length=255, description="Patient's email address")
    date_of_birth: date = Field(..., description="Patient's date of birth")
    
    # Optional demographic fields
    gender: Optional[GenderEnum] = Field(None, description="Patient's gender identity")
    primary_language: LanguageEnum = Field(LanguageEnum.URDU, description="Patient's primary language")
    phone: Optional[str] = Field(None, max_length=20, description="Patient's phone number")
    
    # Address information
    city: Optional[str] = Field(None, max_length=100, description="Patient's city")
    district: Optional[str] = Field(None, max_length=100, description="Patient's district")
    province: Optional[str] = Field(None, max_length=100, description="Patient's province")
    postal_code: Optional[str] = Field(None, max_length=20, description="Patient's postal code")
    country: str = Field("Pakistan", max_length=100, description="Patient's country")
    
    # Consent and preferences
    accepts_terms_and_conditions: bool = Field(False, description="Terms and conditions acceptance")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', v):
            raise ValueError('Invalid phone number format')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v):
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        if (date.today() - v).days > 36500:  # ~100 years
            raise ValueError('Date of birth seems unrealistic')
        return v

class PatientUpdateRequest(BasePatientModel):
    """Schema for updating patient information"""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    primary_language: Optional[LanguageEnum] = None
    phone: Optional[str] = Field(None, max_length=20)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    record_status: Optional[RecordStatusEnum] = None
    assigned_therapist_id: Optional[str] = Field(None, max_length=100)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower() if v else v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', v):
            raise ValueError('Invalid phone number format')
        return v

class PatientResponse(BasePatientModel):
    """Schema for patient data response"""
    
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    date_of_birth: date
    gender: Optional[GenderEnum]
    primary_language: LanguageEnum
    phone: Optional[str]
    city: Optional[str]
    district: Optional[str]
    province: Optional[str]
    postal_code: Optional[str]
    country: str
    record_status: RecordStatusEnum
    assigned_therapist_id: Optional[str]
    intake_completed_date: Optional[date]
    last_contact_date: Optional[date]
    next_appointment_date: Optional[datetime]
    accepts_terms_and_conditions: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def age(self) -> int:
        """Calculate patient's current age"""
        return (date.today() - self.date_of_birth).days // 365
    
    @computed_field
    @property
    def full_name(self) -> str:
        """Patient's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @computed_field
    @property
    def full_address(self) -> str:
        """Formatted full address"""
        parts = [self.city, self.district, self.province, self.country]
        return ", ".join(filter(None, parts))

# ============================================================================
# PATIENT AUTHENTICATION SCHEMAS
# ============================================================================

class PatientAuthCreateRequest(BasePatientModel):
    """Schema for creating patient authentication info"""
    
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="Patient password")
    google_id: Optional[str] = Field(None, description="Google OAuth ID")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    theme_preference: str = Field("light", pattern="^(light|dark)$", description="UI theme preference")
    two_factor_enabled: bool = Field(False, description="Two-factor authentication enabled")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if v and len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Add more password complexity validation as needed
        return v

class PatientAuthUpdateRequest(BasePatientModel):
    """Schema for updating patient authentication info"""
    
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    avatar_url: Optional[str] = None
    theme_preference: Optional[str] = Field(None, pattern="^(light|dark)$")
    two_factor_enabled: Optional[bool] = None
    max_concurrent_sessions: Optional[int] = Field(None, ge=1, le=10)

class PatientAuthResponse(BasePatientModel):
    """Schema for patient authentication info response"""
    
    patient_id: uuid.UUID
    is_active: bool
    is_verified: bool
    is_locked: bool
    login_attempts: int
    failed_login_attempts: int
    last_login: Optional[datetime]
    last_login_ip: Optional[str]
    last_activity: Optional[datetime]
    google_id: Optional[str]
    avatar_url: Optional[str]
    theme_preference: str
    two_factor_enabled: bool
    max_concurrent_sessions: int
    created_at: datetime
    updated_at: datetime

# ============================================================================
# PATIENT PREFERENCES SCHEMAS
# ============================================================================

class LocationPreferences(BasePatientModel):
    """Location preference structure"""
    
    consultation_mode: Optional[ConsultationModeEnum] = ConsultationModeEnum.VIRTUAL
    preferred_cities: Optional[List[str]] = Field(default_factory=list)
    max_travel_distance: Optional[int] = Field(None, ge=0, le=500, description="Max travel distance in km")
    transportation_available: Optional[bool] = None

class CulturalPreferences(BasePatientModel):
    """Cultural preference structure"""
    
    language_preference: Optional[LanguageEnum] = LanguageEnum.URDU
    therapist_gender_preference: Optional[GenderEnum] = None
    cultural_background_match: Optional[bool] = None
    religious_considerations: Optional[str] = None

class TherapyPreferences(BasePatientModel):
    """Therapy preference structure"""
    
    preferred_modality: Optional[TherapyModalityEnum] = TherapyModalityEnum.INDIVIDUAL
    preferred_approach: Optional[TherapyApproachEnum] = TherapyApproachEnum.NO_PREFERENCE
    session_duration: Optional[int] = Field(60, ge=30, le=120, description="Preferred session duration in minutes")
    frequency: Optional[str] = Field("weekly", pattern="^(daily|weekly|biweekly|monthly)$")
    time_of_day_preference: Optional[str] = None

class FinancialPreferences(BasePatientModel):
    """Financial preference structure"""
    
    max_budget: Optional[Decimal] = Field(None, ge=0, description="Maximum budget per session")
    preferred_payment_method: Optional[PaymentMethodEnum] = PaymentMethodEnum.CASH
    insurance_available: Optional[bool] = None
    sliding_scale_needed: Optional[bool] = None

class SpecialistPreferences(BasePatientModel):
    """Specialist preference structure"""
    
    min_experience_years: Optional[int] = Field(None, ge=0, le=50)
    min_rating: Optional[Decimal] = Field(None, ge=0.0, le=5.0)
    specialization_areas: Optional[List[str]] = Field(default_factory=list)
    certification_requirements: Optional[List[str]] = Field(default_factory=list)

class AvailabilityPreferences(BasePatientModel):
    """Availability preference structure"""
    
    urgency_level: UrgencyLevelEnum = UrgencyLevelEnum.STANDARD
    preferred_days: Optional[List[str]] = Field(default_factory=list)
    preferred_times: Optional[List[str]] = Field(default_factory=list)
    timezone: Optional[str] = Field("Asia/Karachi")

class PriorityWeights(BasePatientModel):
    """Priority weights for matching algorithm"""
    
    cultural_fit: Decimal = Field(0.25, ge=0.0, le=1.0)
    clinical_match: Decimal = Field(0.20, ge=0.0, le=1.0)
    location: Decimal = Field(0.15, ge=0.0, le=1.0)
    cost: Decimal = Field(0.15, ge=0.0, le=1.0)
    availability: Decimal = Field(0.10, ge=0.0, le=1.0)
    ratings: Decimal = Field(0.08, ge=0.0, le=1.0)
    experience: Decimal = Field(0.07, ge=0.0, le=1.0)

class PatientPreferencesCreateRequest(BasePatientModel):
    """Schema for creating patient preferences"""
    
    location_preferences: LocationPreferences = Field(default_factory=LocationPreferences)
    cultural_preferences: CulturalPreferences = Field(default_factory=CulturalPreferences)
    therapy_preferences: TherapyPreferences = Field(default_factory=TherapyPreferences)
    financial_preferences: FinancialPreferences = Field(default_factory=FinancialPreferences)
    specialist_preferences: SpecialistPreferences = Field(default_factory=SpecialistPreferences)
    availability_preferences: AvailabilityPreferences = Field(default_factory=AvailabilityPreferences)
    priority_weights: PriorityWeights = Field(default_factory=PriorityWeights)
    notes: Optional[str] = None

class PatientPreferencesUpdateRequest(BasePatientModel):
    """Schema for updating patient preferences"""
    
    location_preferences: Optional[LocationPreferences] = None
    cultural_preferences: Optional[CulturalPreferences] = None
    therapy_preferences: Optional[TherapyPreferences] = None
    financial_preferences: Optional[FinancialPreferences] = None
    specialist_preferences: Optional[SpecialistPreferences] = None
    availability_preferences: Optional[AvailabilityPreferences] = None
    priority_weights: Optional[PriorityWeights] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class PatientPreferencesResponse(BasePatientModel):
    """Schema for patient preferences response"""
    
    patient_id: uuid.UUID
    location_preferences: Dict[str, Any]
    cultural_preferences: Dict[str, Any]
    therapy_preferences: Dict[str, Any]
    financial_preferences: Dict[str, Any]
    specialist_preferences: Dict[str, Any]
    availability_preferences: Dict[str, Any]
    priority_weights: Dict[str, Any]
    notes: Optional[str]
    is_active: bool
    max_budget: Optional[Decimal]
    preferred_city: Optional[str]
    consultation_mode: Optional[ConsultationModeEnum]
    urgency_level: UrgencyLevelEnum
    created_at: datetime
    updated_at: datetime

# ============================================================================
# PATIENT HISTORY SCHEMAS
# ============================================================================

class PatientHistoryCreateRequest(BasePatientModel):
    """Schema for creating patient history"""
    
    # Psychiatric History
    past_psych_dx: Optional[str] = None
    past_psych_treatment: Optional[str] = None
    hospitalizations: Optional[str] = None
    ect_history: Optional[str] = None
    
    # Medications
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
    
    # Substance Use
    alcohol_use: Optional[str] = None
    drug_use: Optional[str] = None
    prescription_drug_abuse: Optional[str] = None
    last_use_date: Optional[str] = None
    substance_treatment: Optional[str] = None
    tobacco_use: Optional[str] = None
    
    # Cultural/Spiritual
    cultural_background: Optional[str] = None
    cultural_beliefs: Optional[str] = None
    spiritual_supports: Optional[str] = None
    family_mental_health_stigma: Optional[str] = None
    
    # Completion tracking
    sections_completed: List[str] = Field(default_factory=list)

class PatientHistoryUpdateRequest(BasePatientModel):
    """Schema for updating patient history"""
    
    # All fields are optional for updates
    past_psych_dx: Optional[str] = None
    past_psych_treatment: Optional[str] = None
    hospitalizations: Optional[str] = None
    ect_history: Optional[str] = None
    current_meds: Optional[Dict[str, Any]] = None
    med_allergies: Optional[str] = None
    otc_supplements: Optional[str] = None
    medication_adherence: Optional[str] = None
    medical_history_summary: Optional[str] = None
    chronic_illnesses: Optional[str] = None
    neurological_problems: Optional[str] = None
    head_injury: Optional[str] = None
    seizure_history: Optional[str] = None
    pregnancy_status: Optional[str] = None
    alcohol_use: Optional[str] = None
    drug_use: Optional[str] = None
    prescription_drug_abuse: Optional[str] = None
    last_use_date: Optional[str] = None
    substance_treatment: Optional[str] = None
    tobacco_use: Optional[str] = None
    cultural_background: Optional[str] = None
    cultural_beliefs: Optional[str] = None
    spiritual_supports: Optional[str] = None
    family_mental_health_stigma: Optional[str] = None
    sections_completed: Optional[List[str]] = None
    is_complete: Optional[bool] = None

class PatientHistoryResponse(BasePatientModel):
    """Schema for patient history response"""
    
    patient_id: uuid.UUID
    past_psych_dx: Optional[str]
    past_psych_treatment: Optional[str]
    hospitalizations: Optional[str]
    ect_history: Optional[str]
    current_meds: Dict[str, Any]
    med_allergies: Optional[str]
    otc_supplements: Optional[str]
    medication_adherence: Optional[str]
    medical_history_summary: Optional[str]
    chronic_illnesses: Optional[str]
    neurological_problems: Optional[str]
    head_injury: Optional[str]
    seizure_history: Optional[str]
    pregnancy_status: Optional[str]
    alcohol_use: Optional[str]
    drug_use: Optional[str]
    prescription_drug_abuse: Optional[str]
    last_use_date: Optional[str]
    substance_treatment: Optional[str]
    tobacco_use: Optional[str]
    cultural_background: Optional[str]
    cultural_beliefs: Optional[str]
    spiritual_supports: Optional[str]
    family_mental_health_stigma: Optional[str]
    completion_timestamp: Optional[datetime]
    sections_completed: List[str]
    is_complete: bool
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        # This would mirror the logic from your SQLAlchemy model
        total_fields = 24
        filled_fields = 0
        
        # Count non-None and non-empty fields
        history_fields = [
            self.past_psych_dx, self.past_psych_treatment, self.hospitalizations, self.ect_history,
            self.med_allergies, self.otc_supplements, self.medication_adherence,
            self.medical_history_summary, self.chronic_illnesses, self.neurological_problems,
            self.head_injury, self.seizure_history, self.pregnancy_status,
            self.alcohol_use, self.drug_use, self.prescription_drug_abuse, self.last_use_date,
            self.substance_treatment, self.tobacco_use, self.cultural_background,
            self.cultural_beliefs, self.spiritual_supports, self.family_mental_health_stigma
        ]
        
        for field in history_fields:
            if field:
                filled_fields += 1
        
        if self.current_meds and len(self.current_meds) > 0:
            filled_fields += 1
        
        return (filled_fields / total_fields) * 100

# ============================================================================
# PRESENTING CONCERNS SCHEMAS
# ============================================================================

class PresentingConcernCreateRequest(BasePatientModel):
    """Schema for creating presenting concerns"""
    
    presenting_concern: Optional[str] = None
    presenting_onset: Optional[str] = Field(None, max_length=200)
    hpi_onset: Optional[str] = Field(None, max_length=200)
    hpi_duration: Optional[str] = Field(None, max_length=200)
    hpi_course: Optional[str] = None
    hpi_severity: Optional[int] = Field(None, ge=1, le=10, description="Severity on 1-10 scale")
    hpi_frequency: Optional[str] = Field(None, max_length=200)
    hpi_triggers: Optional[str] = None
    hpi_impact_work: Optional[str] = None
    hpi_impact_relationships: Optional[str] = None
    hpi_prior_episodes: Optional[str] = None
    function_ADL: Optional[str] = None
    social_activities: Optional[str] = None
    session_notes: Optional[str] = None
    priority_level: UrgencyLevelEnum = UrgencyLevelEnum.STANDARD

class PresentingConcernUpdateRequest(BasePatientModel):
    """Schema for updating presenting concerns"""
    
    presenting_concern: Optional[str] = None
    presenting_onset: Optional[str] = Field(None, max_length=200)
    hpi_onset: Optional[str] = Field(None, max_length=200)
    hpi_duration: Optional[str] = Field(None, max_length=200)
    hpi_course: Optional[str] = None
    hpi_severity: Optional[int] = Field(None, ge=1, le=10)
    hpi_frequency: Optional[str] = Field(None, max_length=200)
    hpi_triggers: Optional[str] = None
    hpi_impact_work: Optional[str] = None
    hpi_impact_relationships: Optional[str] = None
    hpi_prior_episodes: Optional[str] = None
    function_ADL: Optional[str] = None
    social_activities: Optional[str] = None
    conversation_complete: Optional[bool] = None
    total_questions_asked: Optional[int] = Field(None, ge=0)
    session_notes: Optional[str] = None
    is_active: Optional[bool] = None
    priority_level: Optional[UrgencyLevelEnum] = None

class PresentingConcernResponse(BasePatientModel):
    """Schema for presenting concern response"""
    
    id: uuid.UUID
    patient_id: uuid.UUID
    presenting_concern: Optional[str]
    presenting_onset: Optional[str]
    hpi_onset: Optional[str]
    hpi_duration: Optional[str]
    hpi_course: Optional[str]
    hpi_severity: Optional[int]
    hpi_frequency: Optional[str]
    hpi_triggers: Optional[str]
    hpi_impact_work: Optional[str]
    hpi_impact_relationships: Optional[str]
    hpi_prior_episodes: Optional[str]
    function_ADL: Optional[str]
    social_activities: Optional[str]
    conversation_complete: bool
    total_questions_asked: int
    completion_timestamp: Optional[datetime]
    session_notes: Optional[str]
    is_active: bool
    priority_level: UrgencyLevelEnum
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        total_fields = 12
        filled_fields = 0
        
        concern_fields = [
            self.presenting_concern, self.presenting_onset, self.hpi_onset, self.hpi_duration,
            self.hpi_course, self.hpi_severity, self.hpi_frequency, self.hpi_triggers,
            self.hpi_impact_work, self.hpi_impact_relationships, self.function_ADL, self.social_activities
        ]
        
        for field in concern_fields:
            if field:
                filled_fields += 1
        
        return (filled_fields / total_fields) * 100

# ============================================================================
# RISK ASSESSMENT SCHEMAS
# ============================================================================

class RiskAssessmentCreateRequest(BasePatientModel):
    """Schema for creating risk assessments"""
    
    suicide_ideation: Optional[bool] = None
    suicide_plan: Optional[str] = None
    suicide_intent: Optional[bool] = None
    past_attempts: Optional[str] = None
    self_harm_history: Optional[str] = None
    homicidal_thoughts: Optional[bool] = None
    access_means: Optional[str] = None
    protective_factors: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    risk_value: Optional[Decimal] = Field(None, ge=0.0, le=1.0, description="Risk value between 0.0 and 1.0")
    risk_reason: Optional[str] = None
    assessed_by: Optional[str] = Field(None, max_length=100)
    assessment_type: str = Field("initial", pattern="^(initial|follow_up|crisis|periodic)$")
    safety_plan_created: bool = Field(False)
    follow_up_required: bool = Field(False)
    follow_up_timeframe: Optional[str] = Field(None, max_length=100)

class RiskAssessmentUpdateRequest(BasePatientModel):
    """Schema for updating risk assessments"""
    
    suicide_ideation: Optional[bool] = None
    suicide_plan: Optional[str] = None
    suicide_intent: Optional[bool] = None
    past_attempts: Optional[str] = None
    self_harm_history: Optional[str] = None
    homicidal_thoughts: Optional[bool] = None
    access_means: Optional[str] = None
    protective_factors: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    risk_value: Optional[Decimal] = Field(None, ge=0.0, le=1.0)
    risk_reason: Optional[str] = None
    safety_plan_created: Optional[bool] = None
    follow_up_required: Optional[bool] = None
    follow_up_timeframe: Optional[str] = Field(None, max_length=100)
    is_current: Optional[bool] = None

class RiskAssessmentResponse(BasePatientModel):
    """Schema for risk assessment response"""
    
    id: uuid.UUID
    patient_id: uuid.UUID
    suicide_ideation: Optional[bool]
    suicide_plan: Optional[str]
    suicide_intent: Optional[bool]
    past_attempts: Optional[str]
    self_harm_history: Optional[str]
    homicidal_thoughts: Optional[bool]
    access_means: Optional[str]
    protective_factors: Optional[str]
    risk_level: Optional[RiskLevel]
    risk_value: Optional[Decimal]
    risk_reason: Optional[str]
    assessment_timestamp: datetime
    assessed_by: Optional[str]
    assessment_type: str
    is_current: bool
    requires_immediate_attention: bool
    safety_plan_created: bool
    follow_up_required: bool
    follow_up_timeframe: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def is_high_risk(self) -> bool:
        """Check if this is a high risk assessment"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @computed_field
    @property
    def requires_crisis_intervention(self) -> bool:
        """Check if crisis intervention is needed"""
        return (self.risk_level == RiskLevel.CRITICAL or 
                self.requires_immediate_attention or
                (self.suicide_ideation and self.suicide_intent))

# ============================================================================
# COMPREHENSIVE PATIENT SCHEMAS
# ============================================================================

class PatientSummaryResponse(BasePatientModel):
    """Summary response model for patient listings"""
    
    id: uuid.UUID
    full_name: str
    email: str
    age: int
    gender: Optional[GenderEnum]
    phone: Optional[str]
    city: Optional[str]
    record_status: RecordStatusEnum
    assigned_therapist_id: Optional[str]
    last_contact_date: Optional[date]
    current_risk_level: Optional[RiskLevel] = None
    requires_follow_up: bool = False
    intake_completed: bool = False
    history_completion_percentage: float = 0.0
    has_presenting_concerns: bool = False
    created_at: datetime

class CompletePatientCreateRequest(BasePatientModel):
    """Schema for creating a complete patient profile"""
    
    patient: PatientCreateRequest
    auth_info: Optional[PatientAuthCreateRequest] = None
    preferences: Optional[PatientPreferencesCreateRequest] = None
    history: Optional[PatientHistoryCreateRequest] = None
    presenting_concerns: Optional[PresentingConcernCreateRequest] = None
    initial_risk_assessment: Optional[RiskAssessmentCreateRequest] = None

class CompletePatientResponse(BasePatientModel):
    """Complete patient information response"""
    
    patient: PatientResponse
    auth_info: Optional[PatientAuthResponse] = None
    preferences: Optional[PatientPreferencesResponse] = None
    history: Optional[PatientHistoryResponse] = None
    presenting_concerns: Optional[List[PresentingConcernResponse]] = None
    risk_assessments: Optional[List[RiskAssessmentResponse]] = None
    current_risk_assessment: Optional[RiskAssessmentResponse] = None
    
    # Summary statistics
    total_risk_assessments: int = 0
    total_presenting_concerns: int = 0
    profile_completion_percentage: float = 0.0
    
    @computed_field
    @property
    def requires_immediate_attention(self) -> bool:
        """Check if patient requires immediate attention"""
        if self.current_risk_assessment:
            return (self.current_risk_assessment.requires_immediate_attention or
                    self.current_risk_assessment.requires_crisis_intervention)
        return False

# ============================================================================
# SEARCH AND FILTER SCHEMAS
# ============================================================================

class PatientSearchCriteria(BasePatientModel):
    """Schema for patient search criteria"""
    
    name: Optional[str] = Field(None, description="Search by first or last name")
    email: Optional[str] = Field(None, description="Search by email")
    phone: Optional[str] = Field(None, description="Search by phone number")
    city: Optional[str] = Field(None, description="Search by city")
    assigned_therapist_id: Optional[str] = Field(None, description="Filter by assigned therapist")
    record_status: Optional[RecordStatusEnum] = Field(None, description="Filter by record status")
    age_min: Optional[int] = Field(None, ge=0, le=120, description="Minimum age")
    age_max: Optional[int] = Field(None, ge=0, le=120, description="Maximum age")
    risk_level: Optional[RiskLevel] = Field(None, description="Filter by current risk level")
    gender: Optional[GenderEnum] = Field(None, description="Filter by gender")
    primary_language: Optional[LanguageEnum] = Field(None, description="Filter by primary language")
    has_presenting_concerns: Optional[bool] = Field(None, description="Filter patients with presenting concerns")
    intake_completed: Optional[bool] = Field(None, description="Filter by intake completion status")
    created_after: Optional[date] = Field(None, description="Filter patients created after this date")
    created_before: Optional[date] = Field(None, description="Filter patients created before this date")
    
    @field_validator('age_min', 'age_max')
    @classmethod
    def validate_age_range(cls, v, info):
        if v is not None and v < 0:
            raise ValueError('Age cannot be negative')
        return v

class PatientSearchRequest(BasePatientModel):
    """Schema for patient search requests with pagination"""
    
    criteria: PatientSearchCriteria = Field(default_factory=PatientSearchCriteria)
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Number of results per page")
    sort_by: str = Field("created_at", description="Field to sort by")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")

class PatientSearchResponse(BasePatientModel):
    """Schema for patient search results"""
    
    patients: List[PatientSummaryResponse]
    total_count: int = Field(ge=0, description="Total number of matching patients")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Number of results per page")
    total_pages: int = Field(ge=0, description="Total number of pages")
    
    @computed_field
    @property
    def has_next(self) -> bool:
        """Check if there are more pages"""
        return self.page < self.total_pages
    
    @computed_field
    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages"""
        return self.page > 1

# ============================================================================
# FOLLOW-UP AND MONITORING SCHEMAS
# ============================================================================

class FollowUpPatientInfo(BasePatientModel):
    """Schema for patient follow-up information"""
    
    patient_id: uuid.UUID
    full_name: str
    email: str
    phone: Optional[str]
    risk_level: RiskLevel
    follow_up_timeframe: str
    assessment_date: datetime
    requires_immediate_attention: bool
    assigned_therapist_id: Optional[str]
    last_contact_date: Optional[date]
    next_appointment_date: Optional[datetime]

class FollowUpListResponse(BasePatientModel):
    """Schema for follow-up patient list"""
    
    patients: List[FollowUpPatientInfo]
    total_count: int
    immediate_attention_count: int = 0
    critical_risk_count: int = 0
    high_risk_count: int = 0
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class HighRiskPatientResponse(BasePatientModel):
    """Schema for high-risk patient information"""
    
    patient_id: uuid.UUID
    full_name: str
    email: str
    phone: Optional[str]
    current_risk_level: RiskLevel
    current_risk_value: Optional[Decimal]
    risk_reason: Optional[str]
    assessment_timestamp: datetime
    requires_immediate_attention: bool
    requires_crisis_intervention: bool
    assigned_therapist_id: Optional[str]
    safety_plan_created: bool
    last_contact_date: Optional[date]

# ============================================================================
# BULK OPERATIONS SCHEMAS
# ============================================================================

class BulkPatientCreateRequest(BasePatientModel):
    """Schema for bulk patient creation"""
    
    patients: List[PatientCreateRequest] = Field(..., min_length=1, max_length=100)
    skip_duplicates: bool = Field(True, description="Skip patients with duplicate emails")
    send_welcome_emails: bool = Field(False, description="Send welcome emails to new patients")

class BulkPatientUpdateRequest(BasePatientModel):
    """Schema for bulk patient updates"""
    
    patient_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100)
    updates: PatientUpdateRequest
    skip_errors: bool = Field(True, description="Skip patients that fail validation")

class BulkOperationResponse(BasePatientModel):
    """Schema for bulk operation results"""
    
    total_requested: int = Field(ge=0)
    successful: int = Field(ge=0)
    failed: int = Field(ge=0)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    successful_ids: List[uuid.UUID] = Field(default_factory=list)
    failed_ids: List[uuid.UUID] = Field(default_factory=list)
    
    @computed_field
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requested == 0:
            return 0.0
        return (self.successful / self.total_requested) * 100

# ============================================================================
# STATISTICS AND ANALYTICS SCHEMAS
# ============================================================================

class PatientStatistics(BasePatientModel):
    """Schema for patient statistics"""
    
    total_patients: int = Field(ge=0)
    active_patients: int = Field(ge=0)
    inactive_patients: int = Field(ge=0)
    high_risk_patients: int = Field(ge=0)
    patients_needing_follow_up: int = Field(ge=0)
    new_patients_this_month: int = Field(ge=0)
    average_age: Optional[float] = None
    gender_distribution: Dict[str, int] = Field(default_factory=dict)
    language_distribution: Dict[str, int] = Field(default_factory=dict)
    city_distribution: Dict[str, int] = Field(default_factory=dict)
    risk_level_distribution: Dict[str, int] = Field(default_factory=dict)
    intake_completion_rate: float = Field(ge=0.0, le=100.0)
    
    @computed_field
    @property
    def inactive_rate(self) -> float:
        """Calculate inactive patient rate"""
        if self.total_patients == 0:
            return 0.0
        return (self.inactive_patients / self.total_patients) * 100

class PatientDemographics(BasePatientModel):
    """Schema for patient demographic analysis"""
    
    age_groups: Dict[str, int] = Field(default_factory=dict)  # "18-25", "26-35", etc.
    gender_breakdown: Dict[str, int] = Field(default_factory=dict)
    language_preferences: Dict[str, int] = Field(default_factory=dict)
    geographic_distribution: Dict[str, int] = Field(default_factory=dict)
    consultation_mode_preferences: Dict[str, int] = Field(default_factory=dict)
    therapy_modality_preferences: Dict[str, int] = Field(default_factory=dict)

# ============================================================================
# VALIDATION AND ERROR SCHEMAS
# ============================================================================

class ValidationError(BasePatientModel):
    """Schema for validation errors"""
    
    field: str
    message: str
    invalid_value: Any = None

class PatientValidationResponse(BasePatientModel):
    """Schema for patient data validation results"""
    
    is_valid: bool
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    @computed_field
    @property
    def error_count(self) -> int:
        """Number of validation errors"""
        return len(self.errors)

# ============================================================================
# EXPORT AND IMPORT SCHEMAS
# ============================================================================

class PatientExportRequest(BasePatientModel):
    """Schema for patient data export requests"""
    
    patient_ids: Optional[List[uuid.UUID]] = Field(None, description="Specific patient IDs to export")
    search_criteria: Optional[PatientSearchCriteria] = None
    include_auth_info: bool = Field(False, description="Include authentication information")
    include_history: bool = Field(True, description="Include patient history")
    include_preferences: bool = Field(True, description="Include patient preferences")
    include_risk_assessments: bool = Field(True, description="Include risk assessments")
    include_presenting_concerns: bool = Field(True, description="Include presenting concerns")
    format: str = Field("json", pattern="^(json|csv|xlsx)$", description="Export format")
    anonymize: bool = Field(False, description="Anonymize sensitive data")

class PatientImportRequest(BasePatientModel):
    """Schema for patient data import requests"""
    
    file_format: str = Field(..., pattern="^(json|csv|xlsx)$")
    skip_duplicates: bool = Field(True)
    validate_only: bool = Field(False, description="Only validate without importing")
    send_welcome_emails: bool = Field(False)
    default_therapist_id: Optional[str] = None

class ImportValidationResult(BasePatientModel):
    """Schema for import validation results"""
    
    total_records: int = Field(ge=0)
    valid_records: int = Field(ge=0)
    invalid_records: int = Field(ge=0)
    duplicate_records: int = Field(ge=0)
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)
    
    @computed_field
    @property
    def validation_success_rate(self) -> float:
        """Calculate validation success rate"""
        if self.total_records == 0:
            return 0.0
        return (self.valid_records / self.total_records) * 100

# ============================================================================
# NOTIFICATION AND COMMUNICATION SCHEMAS
# ============================================================================

class PatientNotificationRequest(BasePatientModel):
    """Schema for patient notification requests"""
    
    patient_ids: List[uuid.UUID] = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    notification_type: str = Field(..., pattern="^(email|sms|both)$")
    urgent: bool = Field(False)
    scheduled_for: Optional[datetime] = None

class PatientCommunicationLog(BasePatientModel):
    """Schema for patient communication logging"""
    
    patient_id: uuid.UUID
    communication_type: str = Field(..., pattern="^(email|sms|phone|in_person|video_call)$")
    direction: str = Field(..., pattern="^(inbound|outbound)$")
    subject: Optional[str] = None
    summary: str = Field(..., min_length=1)
    staff_member: str = Field(..., min_length=1)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    follow_up_required: bool = Field(False)
    follow_up_date: Optional[datetime] = None

# ============================================================================
# UTILITY SCHEMAS
# ============================================================================

class PatientIDRequest(BasePatientModel):
    """Schema for requests that only need patient ID"""
    
    patient_id: uuid.UUID

class PatientIDListRequest(BasePatientModel):
    """Schema for requests with multiple patient IDs"""
    
    patient_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100)

class SuccessResponse(BasePatientModel):
    """Generic success response schema"""
    
    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None

class ErrorResponse(BasePatientModel):
    """Generic error response schema"""
    
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ============================================================================
# PASSWORD AND AUTHENTICATION SCHEMAS
# ============================================================================

class PasswordChangeRequest(BasePatientModel):
    """Schema for password change requests"""
    
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('confirm_password')
    @classmethod
    def validate_password_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

class PasswordResetRequest(BasePatientModel):
    """Schema for password reset requests"""
    
    email: str = Field(..., description="Patient's email address")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()

class PasswordResetConfirmRequest(BasePatientModel):
    """Schema for password reset confirmation"""
    
    reset_token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('confirm_password')
    @classmethod
    def validate_password_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

class LoginRequest(BasePatientModel):
    """Schema for patient login requests"""
    
    email: str = Field(..., description="Patient's email address")
    password: str = Field(..., min_length=1)
    remember_me: bool = Field(False)
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()

class LoginResponse(BasePatientModel):
    """Schema for login response"""
    
    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    patient_id: Optional[uuid.UUID] = None
    message: Optional[str] = None
    requires_verification: bool = False
    requires_2fa: bool = False

# ============================================================================
# MODEL EXPORTS
# ============================================================================

__all__ = [
    # Base models
    'BasePatientModel',
    
    # Core patient schemas
    'PatientCreateRequest',
    'PatientUpdateRequest', 
    'PatientResponse',
    
    # Authentication schemas
    'PatientAuthCreateRequest',
    'PatientAuthUpdateRequest',
    'PatientAuthResponse',
    'LoginRequest',
    'LoginResponse',
    'PasswordChangeRequest',
    'PasswordResetRequest',
    'PasswordResetConfirmRequest',
    
    # Preferences schemas
    'LocationPreferences',
    'CulturalPreferences',
    'TherapyPreferences',
    'FinancialPreferences',
    'SpecialistPreferences',
    'AvailabilityPreferences',
    'PriorityWeights',
    'PatientPreferencesCreateRequest',
    'PatientPreferencesUpdateRequest',
    'PatientPreferencesResponse',
    
    # History schemas
    'PatientHistoryCreateRequest',
    'PatientHistoryUpdateRequest',
    'PatientHistoryResponse',
    
    # Presenting concerns schemas
    'PresentingConcernCreateRequest',
    'PresentingConcernUpdateRequest',
    'PresentingConcernResponse',
    
    # Risk assessment schemas
    'RiskAssessmentCreateRequest',
    'RiskAssessmentUpdateRequest',
    'RiskAssessmentResponse',
    
    # Comprehensive schemas
    'PatientSummaryResponse',
    'CompletePatientCreateRequest',
    'CompletePatientResponse',
    
    # Search and filtering
    'PatientSearchCriteria',
    'PatientSearchRequest',
    'PatientSearchResponse',
    
    # Follow-up and monitoring
    'FollowUpPatientInfo',
    'FollowUpListResponse',
    'HighRiskPatientResponse',
    
    # Bulk operations
    'BulkPatientCreateRequest',
    'BulkPatientUpdateRequest',
    'BulkOperationResponse',
    
    # Statistics and analytics
    'PatientStatistics',
    'PatientDemographics',
    
    # Validation
    'ValidationError',
    'PatientValidationResponse',
    
    # Export/Import
    'PatientExportRequest',
    'PatientImportRequest',
    'ImportValidationResult',
    
    # Communication
    'PatientNotificationRequest',
    'PatientCommunicationLog',
    
    # Utility schemas
    'PatientIDRequest',
    'PatientIDListRequest',
    'SuccessResponse',
    'ErrorResponse'
]
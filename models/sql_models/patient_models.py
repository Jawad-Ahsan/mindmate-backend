"""
Enhanced Patient Models - Complete Patient Management System
===========================================================
Comprehensive patient models including demographics, authentication, preferences, 
history, presenting concerns, and risk assessment
"""

from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Boolean, Enum, Text, JSON,
    ForeignKey, Index, UniqueConstraint, CheckConstraint, Numeric
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass, field
import enum
import uuid
import re

# Import your base model
from .base_model import BaseModel as SQLAlchemyBaseModel, USERTYPE, Base

# Import related models
from .appointments_model import Appointment
# from models.clinical_models.symptoms_model import SymptomRecord
# from models.clinical_models.diagnosis_model import DiagnosisRecord
# from models.clinical_models.treatment_model import TreatmentRecord

# ============================================================================
# SHARED ENUMERATIONS
# ============================================================================

class GenderEnum(str, enum.Enum):
    """Gender identity options"""
    MALE = "male"
    FEMALE = "female"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    OTHER = "other"

class RecordStatusEnum(str, enum.Enum):
    """Patient record status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    TRANSFERRED = "transferred"

class LanguageEnum(str, enum.Enum):
    """Language options for Pakistan context"""
    ENGLISH = "english"
    URDU = "urdu"
    PUNJABI = "punjabi"
    SINDHI = "sindhi"
    PASHTO = "pashto"

class ConsultationModeEnum(str, enum.Enum):
    """Consultation mode preferences"""
    VIRTUAL = "virtual"
    IN_PERSON = "in_person"
    HYBRID = "hybrid"

class RiskLevel(str, enum.Enum):
    """Risk assessment levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class TherapyModalityEnum(str, enum.Enum):
    """Therapy modality preferences"""
    INDIVIDUAL = "individual"
    GROUP = "group"
    COUPLES = "couples"
    FAMILY = "family"
    NO_PREFERENCE = "no_preference"

class TherapyApproachEnum(str, enum.Enum):
    """Therapeutic approach preferences"""
    CBT = "cognitive_behavioral_therapy"
    DBT = "dialectical_behavior_therapy"
    PSYCHODYNAMIC = "psychodynamic_therapy"
    HUMANISTIC = "humanistic_person_centered"
    EMDR = "eye_movement_desensitization_reprocessing"
    MINDFULNESS = "mindfulness_based_therapy"
    SOLUTION_FOCUSED = "solution_focused_brief_therapy"
    NO_PREFERENCE = "no_preference"

class PaymentMethodEnum(str, enum.Enum):
    """Payment method preferences"""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    JAZZCASH = "jazzcash"
    EASYPAISA = "easypaisa"
    CARD = "card"
    INSURANCE = "insurance"

class UrgencyLevelEnum(str, enum.Enum):
    """Appointment urgency levels"""
    EMERGENCY = "emergency"
    URGENT = "urgent"
    STANDARD = "standard"
    FLEXIBLE = "flexible"


# ============================================================================
# DATACLASSES FOR COMPLEX DATA STRUCTURES
# ============================================================================

# Note: These dataclasses are no longer used as data is collected via questionnaire
# Keeping for potential future use or reference

# ============================================================================
# 1. CORE PATIENT TABLE
# ============================================================================

class Patient(Base, SQLAlchemyBaseModel):
    """Core patient demographics and identity information"""
    
    __tablename__ = "patients"

    # User Type
    user_type = Column(Enum(USERTYPE), nullable=False, default=USERTYPE.PATIENT)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(Enum(GenderEnum), nullable=False )
    primary_language = Column(Enum(LanguageEnum), default=LanguageEnum.URDU)
    
    # Contact Information
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20))
    
    # Address Information
    city = Column(String(100), nullable=True, index=True)
    district = Column(String(100))
    province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100), default="Pakistan")
    
    # Record Management
    record_status = Column(Enum(RecordStatusEnum), default=RecordStatusEnum.ACTIVE)
    assigned_therapist_id = Column(String(100))
    intake_completed_date = Column(Date)
    last_contact_date = Column(Date)
    next_appointment_date = Column(DateTime(timezone=True))
    
    # Consent to policy
    accepts_terms_and_conditions = Column(Boolean, default=False)
    
    # Relationships
    auth_info = relationship("PatientAuthInfo", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("PatientPreferences", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    history = relationship("PatientHistory", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    presenting_concerns = relationship("PatientPresentingConcerns", back_populates="patient", cascade="all, delete-orphan")
    risk_assessments = relationship("PatientRiskAssessment", back_populates="patient", cascade="all, delete-orphan")
    
    forum_questions = relationship("ForumQuestion", back_populates="patient", lazy="dynamic", cascade="all, delete-orphan")
    forum_bookmarks = relationship("ForumBookmark", back_populates="patient", lazy="dynamic", cascade="all, delete-orphan")
    
    # New relationships for journal and forum
    journal_entries = relationship("JournalEntry", back_populates="patient", cascade="all, delete-orphan")
    
    # Clinical relationships
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    
    # diagnoses = relationship("DiagnosisRecord", back_populates="patient", cascade="all, delete-orphan")
    # treatments = relationship("TreatmentRecord", back_populates="patient", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        Index('idx_patient_name', 'last_name', 'first_name'),
        Index('idx_patient_email', 'email'),
        Index('idx_patient_phone', 'phone'),
        Index('idx_patient_status', 'record_status'),
        Index('idx_patient_user_type', 'user_type'),
        Index('idx_patient_deleted', 'is_deleted'),
        Index('idx_patient_therapist', 'assigned_therapist_id'),
        Index('idx_patient_dob', 'date_of_birth'),
        UniqueConstraint('email', name='uq_patient_email'),
    )
    
    # Computed properties
    @property
    def age(self) -> int:
        """Calculate patient's age in years"""
        if self.date_of_birth:
            return (date.today() - self.date_of_birth).days // 365
        return None
    
    @property
    def full_name(self) -> str:
        """Full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self) -> str:
        """Format full address as string"""
        parts = [self.city, self.district, self.province, self.country]
        return ", ".join(filter(None, parts))
    
    # Validation
    @validates('date_of_birth')
    def validate_dob(self, key, dob):
        if isinstance(dob, datetime):
            dob = dob.date()
        if dob > date.today():
            raise ValueError("Date of birth cannot be in the future")
        if (date.today() - dob).days > 36500:
            raise ValueError("Date of birth seems unrealistic (over 100 years old)")
        return dob
    
    @validates('user_type')
    def validate_user_type(self, key, user_type):
        if user_type != USERTYPE.PATIENT:
            raise ValueError("Patient model can only have user_type as PATIENT")
        return user_type
    
    @validates('email')
    def validate_email(self, key, email):
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError(f"Invalid email format: {email}")
        return email
    
    @validates('phone')
    def validate_phone(self, key, phone):
        if phone and not re.match(r'^\+?[\d\s\-\(\)]{10,20}$', phone):
            raise ValueError(f"Invalid phone number format: {phone}")
        return phone

# ============================================================================
# 2. PATIENT AUTHENTICATION INFO TABLE idx_auth_last_login
# ============================================================================

class PatientAuthInfo(Base, SQLAlchemyBaseModel):
    """Patient authentication and security information"""
    
    __tablename__ = "patient_auth_info"
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Authentication fields
    hashed_password = Column(String, nullable=True)
    password_salt = Column(String, nullable=True)
    password_changed_at = Column(DateTime(timezone=True))
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    
    # OTP and verification
    otp = Column(String, nullable=True)
    otp_expiry = Column(DateTime(timezone=True), nullable=True)
    verification_token = Column(String, nullable=True)
    verification_token_expiry = Column(DateTime(timezone=True), nullable=True)
    
    # Login tracking
    login_attempts = Column(Integer, default=0)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45))
    last_activity = Column(DateTime(timezone=True))
    
    # External authentication
    google_id = Column(String, unique=True, nullable=True)
    
    # Profile and preferences
    avatar_url = Column(String, nullable=True)
    theme_preference = Column(String(20), default="light")
    
    # Security settings
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_code = Column(String(6), nullable=True)
    two_factor_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Session management
    max_concurrent_sessions = Column(Integer, default=3)
    
    # Relationship
    patient = relationship("Patient", back_populates="auth_info")
    
    # Constraints
    __table_args__ = (
        Index('idx_auth_patient', 'patient_id'),
        Index('idx_auth_google', 'google_id'),
    )
    
    @property
    def is_account_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.is_locked:
            return True
        if self.locked_until and self.locked_until > datetime.now():
            return True
        return False

# ============================================================================
# 3. PATIENT PREFERENCES TABLE
# ============================================================================

class PatientPreferences(Base, SQLAlchemyBaseModel):
    """Patient preferences for matching and treatment"""
    
    __tablename__ = "patient_preferences"

    # Foreign key to patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Basic preferences
    consultation_mode = Column(Enum(ConsultationModeEnum), default=ConsultationModeEnum.VIRTUAL)
    urgency_level = Column(Enum(UrgencyLevelEnum), default=UrgencyLevelEnum.STANDARD)
    max_budget = Column(Numeric(10, 2), nullable=True)
    
    # Additional preferences
    notes = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    patient = relationship("Patient", back_populates="preferences")

    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint('max_budget >= 0', name='check_max_budget_positive'),
        Index('idx_patient_preferences_patient', 'patient_id'),
        Index('idx_patient_preferences_mode', 'consultation_mode'),
        Index('idx_patient_preferences_urgency', 'urgency_level'),
        Index('idx_patient_preferences_active', 'is_active'),
    )

# ============================================================================
# 4. PATIENT HISTORY TABLE - SIMPLIFIED
# ============================================================================

class PatientHistory(Base, SQLAlchemyBaseModel):
    """Patient basic medical history summary"""
    
    __tablename__ = "patient_history"
    
    # Foreign key to patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Basic medical summary
    medical_summary = Column(Text, nullable=True)
    last_updated = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="history")

    # Constraints
    __table_args__ = (
        Index('idx_patient_history_patient', 'patient_id'),
        Index('idx_patient_history_updated', 'last_updated'),
    )

# ============================================================================
# 5. PATIENT PRESENTING CONCERNS TABLE - SIMPLIFIED
# ============================================================================

class PatientPresentingConcerns(Base, SQLAlchemyBaseModel):
    """Patient current presenting concerns"""
    
    __tablename__ = "patient_presenting_concerns"
    
    # Foreign key to patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    
    # Current concern
    presenting_concern = Column(Text, nullable=True)
    severity_level = Column(Enum(UrgencyLevelEnum), default=UrgencyLevelEnum.STANDARD)
    
    # Session metadata
    conversation_complete = Column(Boolean, default=False)
    completion_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="presenting_concerns")
    
    # Constraints
    __table_args__ = (
        Index('idx_presenting_concerns_patient', 'patient_id'),
        Index('idx_presenting_concerns_complete', 'conversation_complete'),
        Index('idx_presenting_concerns_active', 'is_active'),
        Index('idx_presenting_concerns_timestamp', 'completion_timestamp'),
    )

# ============================================================================
# 6. PATIENT RISK ASSESSMENT TABLE - SIMPLIFIED
# ============================================================================

class PatientRiskAssessment(Base, SQLAlchemyBaseModel):
    """Patient safety and risk assessment"""
    
    __tablename__ = "patient_risk_assessment"
    
    # Foreign key to patient
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    
    # Risk assessment
    risk_level = Column(Enum(RiskLevel), nullable=True)
    risk_summary = Column(Text, nullable=True)
    
    # Assessment metadata
    assessment_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    assessed_by = Column(String(100), nullable=True)
    is_current = Column(Boolean, default=True)
    
    # Follow-up information
    requires_immediate_attention = Column(Boolean, default=False)
    safety_plan_created = Column(Boolean, default=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="risk_assessments")
    
    # Constraints
    __table_args__ = (
        Index('idx_risk_assessment_patient', 'patient_id'),
        Index('idx_risk_assessment_level', 'risk_level'),
        Index('idx_risk_assessment_current', 'is_current'),
        Index('idx_risk_assessment_timestamp', 'assessment_timestamp'),
        Index('idx_risk_assessment_attention', 'requires_immediate_attention'),
    )
    
    @property
    def is_high_risk(self) -> bool:
        """Check if this assessment indicates high risk"""
        return self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    @property
    def requires_crisis_intervention(self) -> bool:
        """Check if crisis intervention is needed"""
        return (self.risk_level == RiskLevel.CRITICAL or 
                self.requires_immediate_attention)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_complete_patient_record(
    session,
    patient_data: dict,
    hashed_password: str
) -> Patient:
    """Create a complete patient record with auth info and default preferences"""
    
    # Create core patient record
    patient = Patient(**patient_data)
    session.add(patient)
    session.flush()  # Get the patient ID
    
    # Create auth info
    from utils.email_utils import generate_otp, get_otp_expiry
    
    otp = generate_otp()
    otp_expiry = get_otp_expiry()
    
    auth_info = PatientAuthInfo(
        patient_id=patient.id,
        hashed_password=hashed_password,
        is_active=False,  # Inactive until verified
        is_verified=False,
        otp=otp,
        otp_expiry=otp_expiry,
        theme_preference="light",
        max_concurrent_sessions=3
    )
    
    session.add(auth_info)
    
    # Create default preferences
    default_preferences = PatientPreferences(
        patient_id=patient.id,
        consultation_mode=ConsultationModeEnum.VIRTUAL,
        urgency_level=UrgencyLevelEnum.STANDARD,
        max_budget=5000.0,
        is_active=True
    )
    
    session.add(default_preferences)
    
    return patient

def create_patient_profile(
    session,
    patient_data: dict,
    hashed_password: str
) -> Patient:
    """Create a complete patient profile with basic records"""
    
    # Create the basic patient record first
    patient = create_complete_patient_record(session, patient_data, hashed_password)
    
    # Create history record if provided
    if history_data:
        history_dict = {
            'patient_id': patient.id,
            'past_psych_dx': history_data.past_psych_dx,
            'past_psych_treatment': history_data.past_psych_treatment,
            'hospitalizations': history_data.hospitalizations,
            'ect_history': history_data.ect_history,
            'current_meds': history_data.current_meds,
            'med_allergies': history_data.med_allergies,
            'otc_supplements': history_data.otc_supplements,
            'medication_adherence': history_data.medication_adherence,
            'medical_history_summary': history_data.medical_history_summary,
            'chronic_illnesses': history_data.chronic_illnesses,
            'neurological_problems': history_data.neurological_problems,
            'head_injury': history_data.head_injury,
            'seizure_history': history_data.seizure_history,
            'pregnancy_status': history_data.pregnancy_status,
            'alcohol_use': history_data.alcohol_use,
            'drug_use': history_data.drug_use,
            'prescription_drug_abuse': history_data.prescription_drug_abuse,
            'last_use_date': history_data.last_use_date,
            'substance_treatment': history_data.substance_treatment,
            'tobacco_use': history_data.tobacco_use,
            'cultural_background': history_data.cultural_background,
            'cultural_beliefs': history_data.cultural_beliefs,
            'spiritual_supports': history_data.spiritual_supports,
            'family_mental_health_stigma': history_data.family_mental_health_stigma,
            'completion_timestamp': history_data.completion_timestamp,
            'sections_completed': history_data.sections_completed
        }
        
        history = PatientHistory(**history_dict)
        session.add(history)
    
    # Create presenting concerns record if provided
    if presenting_concern_data:
        concerns_dict = {
            'patient_id': patient.id,
            'presenting_concern': presenting_concern_data.presenting_concern,
            'presenting_onset': presenting_concern_data.presenting_onset,
            'hpi_onset': presenting_concern_data.hpi_onset,
            'hpi_duration': presenting_concern_data.hpi_duration,
            'hpi_course': presenting_concern_data.hpi_course,
            'hpi_severity': presenting_concern_data.hpi_severity,
            'hpi_frequency': presenting_concern_data.hpi_frequency,
            'hpi_triggers': presenting_concern_data.hpi_triggers,
            'hpi_impact_work': presenting_concern_data.hpi_impact_work,
            'hpi_impact_relationships': presenting_concern_data.hpi_impact_relationships,
            'hpi_prior_episodes': presenting_concern_data.hpi_prior_episodes,
            'function_ADL': presenting_concern_data.function_ADL,
            'social_activities': presenting_concern_data.social_activities,
            'conversation_complete': presenting_concern_data.conversation_complete,
            'total_questions_asked': presenting_concern_data.total_questions_asked,
            'completion_timestamp': presenting_concern_data.completion_timestamp
        }
        
        concerns = PatientPresentingConcerns(**concerns_dict)
        session.add(concerns)
    
    # Create initial risk assessment if provided
    if initial_risk_assessment:
        risk_dict = {
            'patient_id': patient.id,
            'suicide_ideation': initial_risk_assessment.suicide_ideation,
            'suicide_plan': initial_risk_assessment.suicide_plan,
            'suicide_intent': initial_risk_assessment.suicide_intent,
            'past_attempts': initial_risk_assessment.past_attempts,
            'self_harm_history': initial_risk_assessment.self_harm_history,
            'homicidal_thoughts': initial_risk_assessment.homicidal_thoughts,
            'access_means': initial_risk_assessment.access_means,
            'protective_factors': initial_risk_assessment.protective_factors,
            'risk_level': initial_risk_assessment.risk_level,
            'risk_value': initial_risk_assessment.risk_value,
            'risk_reason': initial_risk_assessment.risk_reason,
            'assessment_timestamp': initial_risk_assessment.assessment_timestamp or datetime.utcnow(),
            'assessment_type': 'initial'
        }
        
        risk_assessment = PatientRiskAssessment(**risk_dict)
        session.add(risk_assessment)
    
    return patient


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    'GenderEnum',
    'RecordStatusEnum', 
    'LanguageEnum',
    'ConsultationModeEnum',
    'RiskLevel',
    'TherapyModalityEnum',
    'TherapyApproachEnum',
    'PaymentMethodEnum',
    'UrgencyLevelEnum',
    
    # Data Classes - No longer used, kept for reference
    
    # Models
    'Patient',
    'PatientAuthInfo',
    'PatientPreferences',
    'PatientHistory',
    'PatientPresentingConcerns',
    'PatientRiskAssessment',
        
    # Utility Functions
    'create_complete_patient_record',
    'create_patient_profile',
]
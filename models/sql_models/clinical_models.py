"""
Clinical Models for Mental Health Platform
==========================================
Unified SQLAlchemy models for diagnosis, treatment, and symptom management
with proper relationships to Patient model.
"""

from datetime import date, datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import uuid4
import enum

# SQLAlchemy imports
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime, Boolean, 
    Enum, ForeignKey, CheckConstraint, Index, Numeric
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property

# Base model import
from .base_model import Base, BaseModel as SQLAlchemyBaseModel

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .patient_models import Patient

# ============================================================================
# SHARED ENUMERATIONS FOR CLINICAL DATA
# ============================================================================

class DiagnosisType(str, enum.Enum):
    """Diagnosis classifications"""
    PRIMARY = "primary"
    SECONDARY = "secondary" 
    PROVISIONAL = "provisional"
    DIFFERENTIAL = "differential"
    RULE_OUT = "rule_out"

class DiagnosisStatus(str, enum.Enum):
    """Diagnosis lifecycle status"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    IN_REMISSION = "in_remission"
    UNDER_REVIEW = "under_review"
    DISCONTINUED = "discontinued"

class TreatmentStatus(str, enum.Enum):
    """Treatment lifecycle status"""
    PLANNED = "planned"
    ACTIVE = "active" 
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"

class TreatmentType(str, enum.Enum):
    """Treatment modalities"""
    MEDICATION = "medication"
    PSYCHOTHERAPY = "psychotherapy"
    BEHAVIORAL_THERAPY = "behavioral_therapy"
    COGNITIVE_THERAPY = "cognitive_therapy"
    COMBINATION = "combination"
    GROUP_THERAPY = "group_therapy"
    FAMILY_THERAPY = "family_therapy"

class SymptomSeverity(int, enum.Enum):
    """Symptom severity levels (0-5 scale)"""
    NONE = 0
    MINIMAL = 1
    MILD = 2
    MODERATE = 3
    SEVERE = 4
    VERY_SEVERE = 5

class SymptomFrequency(str, enum.Enum):
    """Symptom frequency patterns"""
    NEVER = "never"
    RARELY = "rarely"
    OCCASIONALLY = "occasionally" 
    SOMETIMES = "sometimes"
    OFTEN = "often"
    FREQUENTLY = "frequently"
    DAILY = "daily"
    CONSTANT = "constant"

class ImpactLevel(int, enum.Enum):
    """Impact on daily functioning (0-10 scale)"""
    NO_IMPACT = 0
    MINIMAL = 1
    SLIGHT = 2
    MILD = 3
    MODERATE = 4
    MARKED = 5
    SEVERE = 6
    VERY_SEVERE = 7
    EXTREME = 8
    INCAPACITATING = 9
    TOTAL_IMPAIRMENT = 10

# ============================================================================
# DIAGNOSIS RECORD MODEL
# ============================================================================

class DiagnosisRecord(Base, SQLAlchemyBaseModel):
    """SQLAlchemy model for diagnosis records"""
    __tablename__ = "diagnosis_records"

    # Primary key and relationships
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False, index=True)
    
    # Diagnosis classification
    diagnosis_code = Column(String(20), nullable=False, index=True)  # ICD-11/DSM-5 code
    diagnosis_name = Column(String(300), nullable=False, index=True)
    diagnosis_type = Column(Enum(DiagnosisType), nullable=False, default=DiagnosisType.PRIMARY)
    diagnosis_status = Column(Enum(DiagnosisStatus), nullable=False, default=DiagnosisStatus.ACTIVE)
    
    # Clinical assessment
    confidence_level = Column(Integer, nullable=False, default=80)  # 0-100%
    diagnosis_date = Column(Date, nullable=False, default=func.current_date())
    onset_date = Column(Date)  # When symptoms first appeared
    
    # Supporting information
    presenting_symptoms = Column(Text)  # JSON array of symptoms
    clinical_notes = Column(Text)
    diagnostic_criteria_met = Column(Text)  # Which criteria were satisfied
    
    # Severity and specifiers
    severity_level = Column(String(50))  # mild, moderate, severe
    specifiers = Column(Text)  # Additional diagnostic specifiers
    
    # Review and updates
    last_review_date = Column(Date)
    next_review_date = Column(Date)
    reviewed_by = Column(String(100))
    
    # Provider information
    diagnosing_provider_id = Column(String(100))
    diagnosing_provider_name = Column(String(200))
    
    # Relationships
    patient = relationship("Patient", back_populates="diagnoses")
    treatments = relationship(
        "TreatmentRecord", 
        back_populates="diagnosis", 
        cascade="all, delete-orphan",
        order_by="TreatmentRecord.start_date.desc()"
    )
    symptoms = relationship(
        "SymptomRecord", 
        back_populates="diagnosis", 
        cascade="all, delete-orphan",
        order_by="SymptomRecord.recorded_date.desc()"
    )
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            'confidence_level BETWEEN 0 AND 100', 
            name='chk_diagnosis_confidence_range'
        ),
        CheckConstraint(
            'onset_date IS NULL OR diagnosis_date IS NULL OR onset_date <= diagnosis_date',
            name='chk_diagnosis_onset_before_diagnosis'
        ),
        Index('idx_diagnosis_patient_status', 'patient_id', 'diagnosis_status'),
        Index('idx_diagnosis_code_status', 'diagnosis_code', 'diagnosis_status'),
        Index('idx_diagnosis_date', 'diagnosis_date'),
        Index('idx_diagnosis_provider', 'diagnosing_provider_id'),
    )

    # Validation methods
    @validates('diagnosis_code')
    def validate_diagnosis_code(self, key, code):
        """Validate diagnosis code format"""
        if not code or len(code.strip()) < 3:
            raise ValueError("Diagnosis code must be at least 3 characters")
        return code.upper().strip()

    @validates('confidence_level')
    def validate_confidence_level(self, key, level):
        """Validate confidence level range"""
        if level is not None and (level < 0 or level > 100):
            raise ValueError("Confidence level must be between 0 and 100")
        return level

    @validates('diagnosis_name')
    def validate_diagnosis_name(self, key, name):
        """Validate and clean diagnosis name"""
        if not name or len(name.strip()) < 5:
            raise ValueError("Diagnosis name must be at least 5 characters")
        return name.strip()

    # Hybrid properties
    @hybrid_property
    def is_active(self) -> bool:
        """Check if diagnosis is currently active"""
        return self.diagnosis_status == DiagnosisStatus.ACTIVE

    @hybrid_property
    def is_primary(self) -> bool:
        """Check if this is a primary diagnosis"""
        return self.diagnosis_type == DiagnosisType.PRIMARY

    @hybrid_property
    def days_since_diagnosis(self) -> Optional[int]:
        """Calculate days since diagnosis"""
        if self.diagnosis_date:
            return (date.today() - self.diagnosis_date).days
        return None

    @hybrid_property
    def days_since_onset(self) -> Optional[int]:
        """Calculate days since symptom onset"""
        if self.onset_date:
            return (date.today() - self.onset_date).days
        return None

    # Instance methods
    def update_status(self, new_status: DiagnosisStatus, notes: Optional[str] = None) -> None:
        """Update diagnosis status with optional notes"""
        old_status = self.diagnosis_status
        self.diagnosis_status = new_status
        self.last_review_date = date.today()
        
        if notes:
            self.add_clinical_note(f"Status changed from {old_status.value} to {new_status.value}: {notes}")

    def add_clinical_note(self, note: str) -> None:
        """Add a clinical note with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_notes = self.clinical_notes or ""
        self.clinical_notes = f"{current_notes}\n[{timestamp}] {note}".strip()

    def __repr__(self) -> str:
        return f"<DiagnosisRecord(id={self.id}, code={self.diagnosis_code}, status={self.diagnosis_status})>"

# ============================================================================
# TREATMENT RECORD MODEL
# ============================================================================

class TreatmentRecord(Base, SQLAlchemyBaseModel):
    """SQLAlchemy model for treatment records"""
    __tablename__ = "treatment_records"

    # Primary key and relationships
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False, index=True)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey('diagnosis_records.id'), index=True)
    
    # Treatment identification
    treatment_name = Column(String(300), nullable=False)
    treatment_type = Column(Enum(TreatmentType), nullable=False, index=True)
    status = Column(Enum(TreatmentStatus), nullable=False, default=TreatmentStatus.PLANNED)
    
    # Treatment details
    description = Column(Text)
    treatment_goals = Column(Text)  # Primary objectives
    intervention_details = Column(Text)  # Specific interventions used
    
    # Session tracking
    planned_sessions = Column(Integer)
    sessions_completed = Column(Integer, default=0)
    session_frequency = Column(String(100))  # e.g., "weekly", "biweekly"
    session_duration = Column(Integer)  # Duration in minutes
    
    # Effectiveness and progress
    effectiveness_rating = Column(Integer)  # 1-5 scale
    progress_notes = Column(Text)
    client_feedback = Column(Text)
    
    # Dates
    start_date = Column(Date, index=True)
    end_date = Column(Date)
    last_session_date = Column(Date)
    next_session_date = Column(Date)
    
    # Provider information
    provider_id = Column(String(100))
    provider_name = Column(String(200))
    provider_type = Column(String(100))  # psychiatrist, psychologist, counselor
    
    # Cost and insurance
    cost_per_session = Column(Numeric(10, 2))
    total_cost = Column(Numeric(10, 2))
    insurance_covered = Column(Boolean, default=False)
    
    # Additional notes
    notes = Column(Text)
    side_effects = Column(Text)  # For medication treatments
    contraindications = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="treatments")
    diagnosis = relationship("DiagnosisRecord", back_populates="treatments")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            'effectiveness_rating IS NULL OR effectiveness_rating BETWEEN 1 AND 5',
            name='chk_treatment_effectiveness_range'
        ),
        CheckConstraint(
            'sessions_completed >= 0',
            name='chk_treatment_sessions_positive'
        ),
        CheckConstraint(
            'planned_sessions IS NULL OR planned_sessions > 0',
            name='chk_treatment_planned_sessions_positive'
        ),
        CheckConstraint(
            'end_date IS NULL OR start_date IS NULL OR end_date >= start_date',
            name='chk_treatment_dates_logical'
        ),
        CheckConstraint(
            'session_duration IS NULL OR session_duration > 0',
            name='chk_treatment_duration_positive'
        ),
        CheckConstraint(
            'cost_per_session IS NULL OR cost_per_session >= 0',
            name='chk_treatment_cost_positive'
        ),
        Index('idx_treatment_patient_status', 'patient_id', 'status'),
        Index('idx_treatment_type_status', 'treatment_type', 'status'),
        Index('idx_treatment_provider', 'provider_id'),
        Index('idx_treatment_dates', 'start_date', 'end_date'),
    )

    # Validation methods
    @validates('sessions_completed')
    def validate_sessions_completed(self, key, sessions):
        """Validate completed sessions"""
        if sessions is not None:
            if sessions < 0:
                raise ValueError("Completed sessions cannot be negative")
            if self.planned_sessions and sessions > self.planned_sessions:
                raise ValueError("Completed sessions cannot exceed planned sessions")
        return sessions

    @validates('effectiveness_rating')
    def validate_effectiveness_rating(self, key, rating):
        """Validate effectiveness rating range"""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Effectiveness rating must be between 1 and 5")
        return rating

    @validates('planned_sessions', 'session_duration')
    def validate_positive_values(self, key, value):
        """Validate that certain fields are positive"""
        if value is not None and value <= 0:
            raise ValueError(f"{key} must be positive")
        return value

    # Hybrid properties
    @hybrid_property
    def is_active(self) -> bool:
        """Check if treatment is currently active"""
        return self.status == TreatmentStatus.ACTIVE

    @hybrid_property
    def completion_percentage(self) -> float:
        """Calculate treatment completion percentage"""
        if self.planned_sessions and self.sessions_completed:
            return min(100.0, (self.sessions_completed / self.planned_sessions) * 100)
        return 0.0

    @hybrid_property
    def duration_days(self) -> Optional[int]:
        """Calculate treatment duration in days"""
        if self.start_date:
            end_date = self.end_date or date.today()
            return (end_date - self.start_date).days
        return None

    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if treatment has sessions overdue"""
        return (
            self.next_session_date is not None and 
            self.next_session_date < date.today() and
            self.status == TreatmentStatus.ACTIVE
        )

    # Instance methods
    def start_treatment(self, start_date: Optional[date] = None) -> None:
        """Start treatment with proper status update"""
        self.start_date = start_date or date.today()
        self.status = TreatmentStatus.ACTIVE

    def complete_treatment(self, end_date: Optional[date] = None, notes: Optional[str] = None) -> None:
        """Complete treatment with proper status update"""
        self.end_date = end_date or date.today()
        self.status = TreatmentStatus.COMPLETED
        if notes:
            self.add_progress_note(f"Treatment completed: {notes}")

    def add_progress_note(self, note: str) -> None:
        """Add a progress note with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_notes = self.progress_notes or ""
        self.progress_notes = f"{current_notes}\n[{timestamp}] {note}".strip()

    def record_session(self, session_date: Optional[date] = None, notes: Optional[str] = None) -> None:
        """Record a completed session"""
        self.sessions_completed = (self.sessions_completed or 0) + 1
        self.last_session_date = session_date or date.today()
        
        if notes:
            self.add_progress_note(f"Session {self.sessions_completed}: {notes}")

    def calculate_total_cost(self) -> None:
        """Calculate total cost based on sessions and cost per session"""
        if self.cost_per_session and self.sessions_completed:
            self.total_cost = self.cost_per_session * self.sessions_completed

    def __repr__(self) -> str:
        return f"<TreatmentRecord(id={self.id}, name={self.treatment_name}, status={self.status})>"

# ============================================================================
# SYMPTOM RECORD MODEL  
# ============================================================================

class SymptomRecord(Base, SQLAlchemyBaseModel):
    """SQLAlchemy model for symptom records"""
    __tablename__ = "symptom_records"

    # Primary key and relationships
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False, index=True)
    diagnosis_id = Column(UUID(as_uuid=True), ForeignKey('diagnosis_records.id'), index=True)
    
    # Symptom identification
    symptom_name = Column(String(200), nullable=False, index=True)
    symptom_category = Column(String(100))  # anxiety, depression, psychotic, etc.
    symptom_code = Column(String(20))  # Standardized symptom codes if available
    
    # Severity and frequency
    severity = Column(Enum(SymptomSeverity), nullable=False, index=True)
    frequency = Column(Enum(SymptomFrequency), nullable=False)
    impact_score = Column(Enum(ImpactLevel), default=ImpactLevel.NO_IMPACT)
    
    # Detailed description
    description = Column(Text)
    triggers = Column(Text)  # What triggers this symptom
    coping_strategies = Column(Text)  # What helps manage it
    
    # Timeline information
    recorded_date = Column(Date, nullable=False, default=func.current_date(), index=True)
    onset_date = Column(Date)  # When symptom first appeared
    last_occurrence = Column(Date)  # Most recent occurrence
    
    # Context and patterns
    time_of_day = Column(String(50))  # morning, afternoon, evening, night
    duration_minutes = Column(Integer)  # How long symptom lasts
    associated_symptoms = Column(Text)  # Other symptoms that occur together
    
    # Status and monitoring
    is_active = Column(Boolean, default=True, index=True)
    is_primary_complaint = Column(Boolean, default=False)
    monitoring_frequency = Column(String(50))  # daily, weekly, monthly
    
    # Provider assessment
    assessed_by = Column(String(100))
    assessment_notes = Column(Text)
    intervention_recommended = Column(Text)
    
    # Progress tracking
    improvement_rating = Column(Integer)  # 1-5 scale, how much improved
    worsening_factors = Column(Text)
    improvement_factors = Column(Text)
    
    # Relationships
    patient = relationship("Patient", back_populates="symptoms")
    diagnosis = relationship("DiagnosisRecord", back_populates="symptoms")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            'duration_minutes IS NULL OR duration_minutes > 0',
            name='chk_symptom_duration_positive'
        ),
        CheckConstraint(
            'improvement_rating IS NULL OR improvement_rating BETWEEN 1 AND 5',
            name='chk_symptom_improvement_range'
        ),
        CheckConstraint(
            'onset_date IS NULL OR recorded_date IS NULL OR onset_date <= recorded_date',
            name='chk_symptom_onset_before_recorded'
        ),
        Index('idx_symptom_patient_active', 'patient_id', 'is_active'),
        Index('idx_symptom_severity_active', 'severity', 'is_active'),
        Index('idx_symptom_category', 'symptom_category'),
        Index('idx_symptom_dates', 'recorded_date', 'onset_date'),
    )

    # Validation methods
    @validates('symptom_name')
    def validate_symptom_name(self, key, name):
        """Validate and clean symptom name"""
        if not name or len(name.strip()) < 2:
            raise ValueError("Symptom name must be at least 2 characters")
        return name.strip().title()

    @validates('duration_minutes')
    def validate_duration(self, key, duration):
        """Validate duration is positive"""
        if duration is not None and duration <= 0:
            raise ValueError("Duration must be positive")
        return duration

    @validates('improvement_rating')
    def validate_improvement_rating(self, key, rating):
        """Validate improvement rating range"""
        if rating is not None and (rating < 1 or rating > 5):
            raise ValueError("Improvement rating must be between 1 and 5")
        return rating

    # Hybrid properties
    @hybrid_property
    def severity_numeric(self) -> int:
        """Get numeric severity value"""
        return self.severity.value

    @hybrid_property
    def is_severe(self) -> bool:
        """Check if symptom is severe (4+ on scale)"""
        return self.severity.value >= 4

    @hybrid_property
    def is_chronic(self) -> bool:
        """Check if symptom is chronic (ongoing for 6+ months)"""
        if self.onset_date:
            return (date.today() - self.onset_date).days >= 180
        return False

    @hybrid_property
    def days_since_onset(self) -> Optional[int]:
        """Calculate days since symptom onset"""
        if self.onset_date:
            return (date.today() - self.onset_date).days
        return None

    @hybrid_property
    def high_impact(self) -> bool:
        """Check if symptom has high impact on functioning"""
        return self.impact_score.value >= 7

    # Instance methods
    def update_severity(self, new_severity: SymptomSeverity, notes: Optional[str] = None) -> None:
        """Update symptom severity with notes"""
        old_severity = self.severity
        self.severity = new_severity
        self.last_occurrence = date.today()
        
        if notes:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            current_notes = self.assessment_notes or ""
            severity_note = f"Severity updated from {old_severity.name} to {new_severity.name}: {notes}"
            self.assessment_notes = f"{current_notes}\n[{timestamp}] {severity_note}".strip()

    def mark_inactive(self, reason: Optional[str] = None) -> None:
        """Mark symptom as inactive"""
        self.is_active = False
        if reason:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M") 
            current_notes = self.assessment_notes or ""
            self.assessment_notes = f"{current_notes}\n[{timestamp}] Marked inactive: {reason}".strip()

    def add_assessment_note(self, note: str) -> None:
        """Add an assessment note with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        current_notes = self.assessment_notes or ""
        self.assessment_notes = f"{current_notes}\n[{timestamp}] {note}".strip()

    def __repr__(self) -> str:
        return f"<SymptomRecord(id={self.id}, name={self.symptom_name}, severity={self.severity})>"

# ============================================================================
# CLINICAL ASSESSMENT MODEL (Additional)
# ============================================================================

class ClinicalAssessment(Base, SQLAlchemyBaseModel):
    """Model for comprehensive clinical assessments"""
    __tablename__ = "clinical_assessments"

    # Primary key and relationships
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False, index=True)
    
    # Assessment details
    assessment_type = Column(String(100), nullable=False)  # intake, progress, discharge
    assessment_date = Column(Date, nullable=False, default=func.current_date())
    assessor_id = Column(String(100))
    assessor_name = Column(String(200))
    
    # Assessment scores and findings
    mental_status_exam = Column(Text)  # JSON or structured text
    risk_assessment = Column(Text)  # Suicide, violence, self-harm risk
    functional_assessment = Column(Text)  # Daily functioning assessment
    
    # Standardized assessment scores
    phq9_score = Column(Integer)  # Depression screening
    gad7_score = Column(Integer)  # Anxiety screening
    other_assessment_scores = Column(Text)  # JSON for other standardized tools
    
    # Clinical impressions
    clinical_impressions = Column(Text)
    recommendations = Column(Text)
    treatment_planning_notes = Column(Text)
    
    # Follow-up information
    next_assessment_date = Column(Date)
    follow_up_required = Column(Boolean, default=False)
    priority_level = Column(String(20))  # low, medium, high, urgent
    
    # Relationships
    patient = relationship("Patient", back_populates="clinical_assessments")
    
    # Constraints and indexes
    __table_args__ = (
        CheckConstraint(
            'phq9_score IS NULL OR phq9_score BETWEEN 0 AND 27',
            name='chk_assessment_phq9_range'
        ),
        CheckConstraint(
            'gad7_score IS NULL OR gad7_score BETWEEN 0 AND 21', 
            name='chk_assessment_gad7_range'
        ),
        Index('idx_assessment_patient_date', 'patient_id', 'assessment_date'),
        Index('idx_assessment_type', 'assessment_type'),
        Index('idx_assessment_assessor', 'assessor_id'),
    )

    def __repr__(self) -> str:
        return f"<ClinicalAssessment(id={self.id}, type={self.assessment_type}, date={self.assessment_date})>"

# ============================================================================
# UTILITY FUNCTIONS FOR CLINICAL DATA MANAGEMENT
# ============================================================================

def get_active_diagnoses_for_patient(patient_id, session):
    """Get all active diagnoses for a patient"""
    return session.query(DiagnosisRecord).filter(
        DiagnosisRecord.patient_id == patient_id,
        DiagnosisRecord.diagnosis_status == DiagnosisStatus.ACTIVE,
        DiagnosisRecord.is_deleted == False
    ).order_by(DiagnosisRecord.diagnosis_date.desc()).all()

def get_primary_diagnoses_for_patient(patient_id, session):
    """Get primary diagnoses for a patient"""
    return session.query(DiagnosisRecord).filter(
        DiagnosisRecord.patient_id == patient_id,
        DiagnosisRecord.diagnosis_type == DiagnosisType.PRIMARY,
        DiagnosisRecord.is_deleted == False
    ).order_by(DiagnosisRecord.diagnosis_date.desc()).all()

def get_active_treatments_for_patient(patient_id, session):
    """Get all active treatments for a patient"""
    return session.query(TreatmentRecord).filter(
        TreatmentRecord.patient_id == patient_id,
        TreatmentRecord.status == TreatmentStatus.ACTIVE,
        TreatmentRecord.is_deleted == False
    ).order_by(TreatmentRecord.start_date.desc()).all()

def get_severe_symptoms_for_patient(patient_id, session):
    """Get severe symptoms for a patient"""
    return session.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.severity >= SymptomSeverity.SEVERE,
        SymptomRecord.is_active == True,
        SymptomRecord.is_deleted == False
    ).order_by(SymptomRecord.severity.desc()).all()

def get_patient_clinical_overview(patient_id, session):
    """Get comprehensive clinical overview for a patient"""
    from collections import Counter
    
    # Get all clinical data
    diagnoses = session.query(DiagnosisRecord).filter(
        DiagnosisRecord.patient_id == patient_id,
        DiagnosisRecord.is_deleted == False
    ).all()
    
    treatments = session.query(TreatmentRecord).filter(
        TreatmentRecord.patient_id == patient_id,
        TreatmentRecord.is_deleted == False
    ).all()
    
    symptoms = session.query(SymptomRecord).filter(
        SymptomRecord.patient_id == patient_id,
        SymptomRecord.is_deleted == False
    ).all()
    
    # Calculate statistics
    active_diagnoses = [d for d in diagnoses if d.is_active]
    active_treatments = [t for t in treatments if t.is_active]
    active_symptoms = [s for s in symptoms if s.is_active]
    severe_symptoms = [s for s in active_symptoms if s.is_severe]
    
    # Treatment completion rates
    completed_treatments = [t for t in treatments if t.status == TreatmentStatus.COMPLETED]
    treatment_completion_rate = (
        len(completed_treatments) / len(treatments) * 100 
        if treatments else 0
    )
    
    # Symptom categories
    symptom_categories = Counter(s.symptom_category for s in active_symptoms if s.symptom_category)
    
    return {
        'patient_id': patient_id,
        'summary': {
            'total_diagnoses': len(diagnoses),
            'active_diagnoses': len(active_diagnoses),
            'primary_diagnoses': len([d for d in diagnoses if d.is_primary]),
            'total_treatments': len(treatments),
            'active_treatments': len(active_treatments),
            'treatment_completion_rate': round(treatment_completion_rate, 2),
            'total_symptoms': len(symptoms),
            'active_symptoms': len(active_symptoms),
            'severe_symptoms': len(severe_symptoms)
        },
        'current_active_diagnoses': [
            {
                'id': d.id,
                'code': d.diagnosis_code,
                'name': d.diagnosis_name,
                'type': d.diagnosis_type.value,
                'confidence': d.confidence_level,
                'days_since_diagnosis': d.days_since_diagnosis
            }
            for d in active_diagnoses
        ],
        'current_active_treatments': [
            {
                'id': t.id,
                'name': t.treatment_name,
                'type': t.treatment_type.value,
                'sessions_completed': t.sessions_completed,
                'planned_sessions': t.planned_sessions,
                'completion_percentage': t.completion_percentage,
                'effectiveness_rating': t.effectiveness_rating
            }
            for t in active_treatments
        ],
        'severe_symptoms': [
            {
                'id': s.id,
                'name': s.symptom_name,
                'severity': s.severity.name,
                'frequency': s.frequency.value,
                'impact_score': s.impact_score.value,
                'days_since_onset': s.days_since_onset
            }
            for s in severe_symptoms
        ],
        'symptom_categories': dict(symptom_categories),
        'risk_indicators': {
            'has_severe_symptoms': len(severe_symptoms) > 0,
            'multiple_active_diagnoses': len(active_diagnoses) > 1,
            'treatment_gaps': len(active_diagnoses) > len(active_treatments),
            'chronic_symptoms': len([s for s in active_symptoms if s.is_chronic]) > 0
        }
    }

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enumerations
    "DiagnosisType",
    "DiagnosisStatus", 
    "TreatmentStatus",
    "TreatmentType",
    "SymptomSeverity",
    "SymptomFrequency",
    "ImpactLevel",
    
    # SQLAlchemy Models
    "DiagnosisRecord",
    "TreatmentRecord",
    "SymptomRecord",
    "ClinicalAssessment",
    
    # Utility Functions
    "get_active_diagnoses_for_patient",
    "get_primary_diagnoses_for_patient", 
    "get_active_treatments_for_patient",
    "get_severe_symptoms_for_patient",
    "get_patient_clinical_overview"
]

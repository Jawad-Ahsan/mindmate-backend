"""
DA Diagnosis Agent Schemas
Pydantic models for input/output validation and serialization
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, model_validator
import json


class SymptomSeverity(str, Enum):
    """Symptom severity levels"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    UNKNOWN = "unknown"


class DiagnosisConfidence(float, Enum):
    """Standardized confidence levels"""
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.9


class DisorderCategory(str, Enum):
    """DSM-5 disorder categories"""
    MOOD_DISORDERS = "mood_disorders"
    ANXIETY_DISORDERS = "anxiety_disorders"
    TRAUMA_STRESSOR_DISORDERS = "trauma_stressor_disorders"
    OBSESSIVE_COMPULSIVE_DISORDERS = "obsessive_compulsive_disorders"
    SUBSTANCE_USE_DISORDERS = "substance_use_disorders"
    EATING_DISORDERS = "eating_disorders"
    NEURODEVELOPMENTAL_DISORDERS = "neurodevelopmental_disorders"
    PERSONALITY_DISORDERS = "personality_disorders"
    PSYCHOTIC_DISORDERS = "psychotic_disorders"
    OTHER_DISORDERS = "other_disorders"


class SupportedDisorder(str, Enum):
    """All supported psychiatric disorders"""
    MDD = "MDD"
    GAD = "GAD"
    PANIC = "PANIC"
    SUBSTANCE_USE = "SUBSTANCE_USE"
    ADHD = "ADHD"
    ADJUSTMENT = "ADJUSTMENT"
    BIPOLAR = "BIPOLAR"
    SOCIAL_ANXIETY = "SOCIAL_ANXIETY"
    SPECIFIC_PHOBIA = "SPECIFIC_PHOBIA"
    AGORAPHOBIA = "AGORAPHOBIA"
    PTSD = "PTSD"
    OCD = "OCD"
    ALCOHOL_USE = "ALCOHOL_USE"
    EATING_DISORDERS = "EATING_DISORDERS"


# Input Schemas

class SymptomInput(BaseModel):
    """Individual symptom input"""
    description: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Symptom description in natural language"
    )
    duration: Optional[str] = Field(
        None,
        description="Duration of symptom (e.g., '2 weeks', '3 months')"
    )
    severity: Optional[SymptomSeverity] = Field(
        None,
        description="Patient-reported symptom severity"
    )
    frequency: Optional[str] = Field(
        None,
        description="How often symptom occurs (e.g., 'daily', 'most days')"
    )

    @validator('description')
    def validate_description(cls, v):
        """Validate symptom description"""
        if not v or not v.strip():
            raise ValueError('Symptom description cannot be empty')

        # Check for minimum meaningful content
        words = v.strip().split()
        if len(words) < 1:
            raise ValueError('Symptom description must contain at least one word')

        return v.strip()


class PatientContext(BaseModel):
    """Additional patient context information"""
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")
    medical_history: Optional[List[str]] = Field(
        None,
        description="Relevant medical history items"
    )
    medications: Optional[List[str]] = Field(
        None,
        description="Current medications"
    )
    family_history: Optional[List[str]] = Field(
        None,
        description="Family psychiatric history"
    )
    chief_complaint: Optional[str] = Field(
        None,
        description="Patient's main complaint"
    )
    onset_timeline: Optional[str] = Field(
        None,
        description="When symptoms began"
    )


class DiagnosisRequest(BaseModel):
    """Main input schema for diagnosis requests"""
    symptoms: List[Union[str, SymptomInput]] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of patient symptoms"
    )
    patient_context: Optional[PatientContext] = Field(
        None,
        description="Additional patient information"
    )
    differential_candidates: Optional[List[SupportedDisorder]] = Field(
        None,
        description="Specific disorders to consider in differential diagnosis"
    )
    include_clinical_reasoning: Optional[bool] = Field(
        True,
        description="Whether to include detailed clinical reasoning"
    )
    confidence_threshold: Optional[float] = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for diagnosis"
    )

    @validator('symptoms')
    def validate_symptoms(cls, v):
        """Validate symptoms list"""
        if not v:
            raise ValueError('At least one symptom is required')

        # Convert string symptoms to SymptomInput objects
        validated_symptoms = []
        for symptom in v:
            if isinstance(symptom, str):
                validated_symptoms.append(SymptomInput(description=symptom))
            elif isinstance(symptom, SymptomInput):
                validated_symptoms.append(symptom)
            else:
                raise ValueError(f'Invalid symptom format: {symptom}')

        return validated_symptoms

    @model_validator(mode='after')
    def validate_request(self):
        """Validate the complete request"""
        symptoms = self.symptoms
        confidence_threshold = self.confidence_threshold

        # Check for duplicate symptoms
        descriptions = [s.description.lower() for s in symptoms]
        if len(descriptions) != len(set(descriptions)):
            raise ValueError('Duplicate symptoms are not allowed')

        return self


# Output Schemas

class MatchedCriterion(BaseModel):
    """Individual matched DSM criterion"""
    criterion_id: str = Field(..., description="DSM criterion identifier")
    description: str = Field(..., description="Full criterion description")
    match_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How well the symptom matches this criterion"
    )


class MissingCriterion(BaseModel):
    """Individual missing DSM criterion"""
    criterion_id: str = Field(..., description="DSM criterion identifier")
    description: str = Field(..., description="Full criterion description")
    importance: str = Field(
        ...,
        description="Importance level (critical, important, optional)"
    )


class FlaggedCriterion(BaseModel):
    """Flagged missing criterion requiring attention"""
    description: str = Field(..., description="Criterion description")
    importance: str = Field(..., description="Importance level")
    clinical_significance: str = Field(
        ...,
        description="Why this criterion is clinically significant"
    )


class DiagnosisMetadata(BaseModel):
    """Metadata about the diagnosis process"""
    agent_type: str = Field(..., description="Type of agent used")
    model_used: str = Field(..., description="LLM model used")
    timestamp: datetime = Field(default_factory=datetime.now, description="Diagnosis timestamp")
    processing_time_seconds: Optional[float] = Field(
        None,
        description="Time taken to process diagnosis"
    )
    tools_used: List[str] = Field(
        ...,
        description="List of tools used in diagnosis"
    )
    react_steps_executed: List[str] = Field(
        ...,
        description="ReAct workflow steps executed"
    )
    symptom_count: int = Field(..., description="Number of symptoms analyzed")
    matched_criteria_count: int = Field(..., description="Number of criteria matched")
    missing_criteria_count: int = Field(..., description="Number of criteria missing")
    flagged_criteria_count: int = Field(..., description="Number of flagged criteria")


class ConfidenceBreakdown(BaseModel):
    """Detailed confidence calculation breakdown"""
    overall_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall diagnostic confidence"
    )
    criteria_match_confidence: float = Field(
        ...,
        description="Confidence from DSM criteria matching"
    )
    symptom_consistency: float = Field(
        ...,
        description="How consistent symptoms are within categories"
    )
    disorder_specificity: float = Field(
        ...,
        description="How specific the diagnosis is vs alternatives"
    )
    symptom_completeness: float = Field(
        ...,
        description="How complete the symptom picture is"
    )
    factors: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional confidence factors"
    )


class ClinicalRecommendation(BaseModel):
    """Individual clinical recommendation"""
    recommendation: str = Field(..., description="Recommendation text")
    urgency: str = Field(
        ...,
        description="Urgency level (immediate, urgent, routine, monitor)"
    )
    rationale: str = Field(..., description="Reasoning behind recommendation")
    category: str = Field(
        ...,
        description="Category (assessment, treatment, monitoring, etc.)"
    )


class DiagnosisResponse(BaseModel):
    """Main output schema for diagnosis results"""
    diagnosis: str = Field(..., description="Primary diagnosis name")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall diagnostic confidence (0.0-1.0)"
    )
    severity: SymptomSeverity = Field(..., description="Estimated severity level")
    reasoning: str = Field(
        ...,
        description="Clinical reasoning explaining the diagnosis"
    )
    flagged_criteria: str = Field(
        ...,
        description="Formatted string of flagged missing criteria"
    )

    # Detailed information
    matched_criteria: List[MatchedCriterion] = Field(
        default_factory=list,
        description="Detailed list of matched criteria"
    )
    missing_criteria: List[MissingCriterion] = Field(
        default_factory=list,
        description="Detailed list of missing criteria"
    )
    flagged_criteria_list: List[FlaggedCriterion] = Field(
        default_factory=list,
        description="Structured list of flagged criteria"
    )

    # Analysis results
    confidence_breakdown: ConfidenceBreakdown = Field(
        ...,
        description="Detailed confidence calculation"
    )
    clinical_recommendations: List[ClinicalRecommendation] = Field(
        default_factory=list,
        description="Clinical recommendations"
    )
    differential_diagnoses: List[str] = Field(
        default_factory=list,
        description="Alternative diagnoses considered"
    )

    # Metadata
    metadata: DiagnosisMetadata = Field(
        ...,
        description="Processing metadata"
    )

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Validation and Error Schemas

class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field that failed validation")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Human-readable error message")
    provided_value: Any = Field(None, description="Value that was provided")


class DiagnosisError(BaseModel):
    """Error response for diagnosis failures"""
    error_type: str = Field(..., description="Type of error encountered")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request identifier for tracking"
    )


class ValidationResponse(BaseModel):
    """Response for input validation"""
    valid: bool = Field(..., description="Whether input is valid")
    errors: List[ValidationError] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-blocking warnings"
    )
    symptom_count: Optional[int] = Field(
        None,
        description="Number of valid symptoms"
    )


# Batch Processing Schemas

class BatchDiagnosisRequest(BaseModel):
    """Input schema for batch diagnosis requests"""
    requests: List[DiagnosisRequest] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of diagnosis requests to process"
    )
    batch_id: Optional[str] = Field(
        None,
        description="Identifier for the batch"
    )
    priority: Optional[str] = Field(
        "normal",
        description="Processing priority (low, normal, high, urgent)"
    )


class BatchDiagnosisResponse(BaseModel):
    """Output schema for batch diagnosis results"""
    batch_id: str = Field(..., description="Batch identifier")
    total_requests: int = Field(..., description="Total number of requests")
    successful_diagnoses: int = Field(..., description="Number of successful diagnoses")
    failed_diagnoses: int = Field(..., description="Number of failed diagnoses")
    results: List[Union[DiagnosisResponse, DiagnosisError]] = Field(
        ...,
        description="Results for each request (in same order as input)"
    )
    processing_time_seconds: float = Field(
        ...,
        description="Total processing time"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Batch completion timestamp"
    )


# Integration Schemas

class DiagnosisServiceConfig(BaseModel):
    """Configuration for DA service"""
    model_name: Optional[str] = Field(
        None,
        description="LLM model to use"
    )
    confidence_threshold: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )
    include_clinical_reasoning: bool = Field(
        True,
        description="Whether to include detailed reasoning"
    )
    max_symptoms_per_request: int = Field(
        50,
        ge=1,
        le=100,
        description="Maximum symptoms per diagnosis request"
    )
    enable_caching: bool = Field(
        True,
        description="Whether to enable response caching"
    )


class DiagnosisServiceStats(BaseModel):
    """Service statistics and health metrics"""
    total_diagnoses: int = Field(..., description="Total diagnoses performed")
    average_confidence: float = Field(..., description="Average confidence across all diagnoses")
    average_processing_time: float = Field(..., description="Average processing time in seconds")
    success_rate: float = Field(..., description="Percentage of successful diagnoses")
    most_common_diagnoses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most frequently diagnosed conditions"
    )
    uptime_seconds: float = Field(..., description="Service uptime")
    last_health_check: datetime = Field(
        default_factory=datetime.now,
        description="Last health check timestamp"
    )


# Utility Functions

def create_sample_request() -> DiagnosisRequest:
    """Create a sample diagnosis request for testing"""
    return DiagnosisRequest(
        symptoms=[
            SymptomInput(
                description="depressed mood most of the day",
                duration="2 weeks",
                frequency="daily"
            ),
            SymptomInput(
                description="loss of interest in activities",
                duration="2 weeks",
                frequency="most days"
            ),
            SymptomInput(
                description="insomnia nearly every night",
                duration="2 weeks",
                frequency="nightly"
            )
        ],
        patient_context=PatientContext(
            age=35,
            chief_complaint="Feeling down and can't sleep"
        ),
        confidence_threshold=0.5
    )


def validate_diagnosis_response(response: Dict[str, Any]) -> DiagnosisResponse:
    """Validate and convert dict to DiagnosisResponse"""
    try:
        return DiagnosisResponse(**response)
    except Exception as e:
        raise ValueError(f"Invalid diagnosis response format: {e}")


def serialize_for_api(response: DiagnosisResponse) -> Dict[str, Any]:
    """Convert DiagnosisResponse to API-friendly format"""
    if hasattr(response, 'model_dump'):
        # Pydantic V2 method
        return response.model_dump(by_alias=True)
    else:
        # Pydantic V1 method (deprecated)
        return response.dict(by_alias=True)


# Export all schemas
__all__ = [
    # Enums
    'SymptomSeverity',
    'DiagnosisConfidence',
    'DisorderCategory',
    'SupportedDisorder',

    # Input schemas
    'SymptomInput',
    'PatientContext',
    'DiagnosisRequest',

    # Output schemas
    'MatchedCriterion',
    'MissingCriterion',
    'FlaggedCriterion',
    'DiagnosisMetadata',
    'ConfidenceBreakdown',
    'ClinicalRecommendation',
    'DiagnosisResponse',

    # Error schemas
    'ValidationError',
    'DiagnosisError',
    'ValidationResponse',

    # Batch schemas
    'BatchDiagnosisRequest',
    'BatchDiagnosisResponse',

    # Service schemas
    'DiagnosisServiceConfig',
    'DiagnosisServiceStats',

    # Utility functions
    'create_sample_request',
    'validate_diagnosis_response',
    'serialize_for_api'
]

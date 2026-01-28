from typing import List, Dict, Optional, Union, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

# Import progress tracking schemas from TPT
try:
    from .treatment_plan_tracker.tpt_schemas import ProgressReport
except ImportError:
    # Fallback if TPT is not available
    class ProgressReport(BaseModel):
        """Fallback ProgressReport schema"""
        patient_id: str
        report_date: datetime
        metrics: Dict[str, Any]
        step_progress: List[Dict[str, Any]]
        insights: List[str]
        recommendations: List[str]
        next_steps: List[str]

class SymptomSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

class TherapyType(str, Enum):
    CBT = "CBT"
    DBT = "DBT"
    ACT = "ACT"
    MINDFULNESS = "Mindfulness"
    PSYCHOEDUCATION = "Psychoeducation"
    JOURNALING = "Journaling"
    SLEEP_HYGIENE = "Sleep Hygiene"
    EXERCISE = "Exercise"
    DIET = "Diet"
    SOCIAL_SUPPORT = "Social Support"
    EXPOSURE_THERAPY = "Exposure Therapy"
    RELAXATION_TECHNIQUES = "Relaxation Techniques"

class InterventionLevel(str, Enum):
    SELF_HELP = "self_help"
    GUIDED_SELF_HELP = "guided_self_help"
    THERAPY = "therapy"
    SPECIALIST_REFERRAL = "specialist_referral"

class PatientPreferences(BaseModel):
    """Patient preferences for treatment"""
    preferred_approach: Literal["self_help", "therapy", "group_support", "hybrid"] = Field(
        description="Patient's preferred treatment approach"
    )
    weekly_time_commitment: int = Field(
        description="Hours per week patient can dedicate to treatment",
        ge=1, le=20
    )
    mode_preference: Literal["in_person", "online", "hybrid"] = Field(
        description="Preferred mode of treatment delivery"
    )
    budget_level: Literal["free", "low_cost", "premium"] = Field(
        description="Patient's budget constraints"
    )
    cultural_considerations: Optional[str] = Field(
        default=None,
        description="Any cultural factors that should be considered"
    )

class SymptomCluster(BaseModel):
    """Represents a cluster of related symptoms"""
    name: str = Field(description="Name of the symptom cluster (e.g., anxiety, depression)")
    severity: SymptomSeverity = Field(description="Overall severity of the cluster")
    symptoms: List[str] = Field(description="List of specific symptoms in this cluster")
    triggers: Optional[List[str]] = Field(
        default=None,
        description="Known triggers for these symptoms"
    )
    impact_on_daily_life: Optional[str] = Field(
        default=None,
        description="How these symptoms affect daily functioning"
    )

class ProvisionalDiagnosis(BaseModel):
    """Provisional diagnosis from the Diagnosis Agent"""
    primary_diagnosis: str = Field(description="Primary mental health diagnosis")
    severity: SymptomSeverity = Field(description="Overall severity of the condition")
    comorbidities: List[str] = Field(
        default_factory=list,
        description="List of comorbid conditions"
    )
    confidence_level: float = Field(
        description="Confidence level of the diagnosis (0.0 to 1.0)",
        ge=0.0, le=1.0
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Identified risk factors"
    )

class PatientDemographics(BaseModel):
    """Patient demographic information from PIMA"""
    age: int = Field(description="Patient age", ge=0, le=120)
    gender: str = Field(description="Patient gender")
    occupation: Optional[str] = Field(default=None, description="Patient occupation")
    cultural_background: Optional[str] = Field(
        default=None,
        description="Cultural or ethnic background"
    )
    living_situation: Optional[str] = Field(
        default=None,
        description="Living situation (alone, with family, etc.)"
    )
    support_system: Optional[str] = Field(
        default=None,
        description="Available support system"
    )

class PatientGoals(BaseModel):
    """Patient's stated goals and preferences"""
    primary_goals: List[str] = Field(description="Main goals for treatment")
    treatment_preferences: List[str] = Field(
        description="Specific treatment preferences or aversions"
    )
    previous_treatments: List[str] = Field(
        default_factory=list,
        description="Previous treatment experiences"
    )
    success_metrics: Optional[List[str]] = Field(
        default=None,
        description="How patient defines success"
    )

class Intervention(BaseModel):
    """Individual intervention or therapy approach"""
    name: str = Field(description="Name of the intervention")
    type: TherapyType = Field(description="Type of therapy/intervention")
    description: str = Field(description="Description of the intervention")
    evidence_level: str = Field(description="Level of evidence supporting this intervention")
    duration: str = Field(description="Expected duration of this intervention")
    frequency: str = Field(description="Recommended frequency")
    resources_needed: List[str] = Field(
        description="Resources required for this intervention"
    )
    contraindications: List[str] = Field(
        default_factory=list,
        description="When this intervention should not be used"
    )

class TreatmentPlan(BaseModel):
    """Complete treatment plan generated by TPA"""
    patient_id: str = Field(description="Unique patient identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Primary treatment approach
    primary_approach: Intervention = Field(description="Main treatment approach")
    
    # Complementary strategies
    complementary_strategies: List[Intervention] = Field(
        description="Additional interventions to support primary approach"
    )
    
    # Self-help resources
    self_help_resources: List[Dict[str, str]] = Field(
        description="Recommended self-help materials and resources"
    )
    
    # Follow-up recommendations
    follow_up_schedule: str = Field(description="Recommended follow-up schedule")
    reassessment_timeline: str = Field(description="When to reassess progress")
    
    # Specialist recommendations
    suggested_specialists: List[Dict[str, str]] = Field(
        description="Recommended specialists if therapy is needed"
    )
    
    # Safety considerations
    safety_notes: List[str] = Field(
        default_factory=list,
        description="Important safety considerations"
    )
    
    # Expected outcomes
    expected_outcomes: List[str] = Field(
        description="Expected outcomes from this treatment plan"
    )
    
    # Risk assessment
    risk_level: Literal["low", "medium", "high"] = Field(
        description="Overall risk level of the treatment plan"
    )
    
    # Escalation criteria
    escalation_criteria: List[str] = Field(
        description="When to escalate to human specialist"
    )

class TPAInput(BaseModel):
    """Complete input data for TPA processing"""
    patient_demographics: PatientDemographics
    patient_goals: PatientGoals
    symptom_clusters: List[SymptomCluster]
    provisional_diagnosis: ProvisionalDiagnosis
    patient_preferences: PatientPreferences
    red_flags: List[str] = Field(
        default_factory=list,
        description="Any safety concerns or red flags"
    )

class TPAOutput(BaseModel):
    """Output from TPA processing"""
    treatment_plan: TreatmentPlan
    confidence_score: float = Field(
        description="Confidence in the treatment plan (0.0 to 1.0)",
        ge=0.0, le=1.0
    )
    reasoning: str = Field(description="Explanation of why this plan was chosen")
    alternatives_considered: List[str] = Field(
        description="Alternative approaches that were considered"
    )
    requires_human_review: bool = Field(
        description="Whether this plan requires human specialist review"
    )
    review_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons why human review is needed"
    )

class SimpleTreatmentStep(BaseModel):
    """Simple, patient-friendly treatment step"""
    step_number: int = Field(description="Sequential step number")
    title: str = Field(description="Simple, clear title for the step")
    description: str = Field(description="Simple explanation of what to do")
    duration: str = Field(description="How long this step takes")
    frequency: str = Field(description="How often to do this step")
    reminder_text: str = Field(description="Simple reminder message for emails")
    tracking_question: str = Field(description="Simple question to track progress")
    expected_progress: str = Field(description="What progress to expect")
    tips: List[str] = Field(description="Simple tips for success")

class SimpleTreatmentPlan(BaseModel):
    """Patient-friendly, step-by-step treatment plan"""
    patient_id: str = Field(description="Unique patient identifier")
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Simple overview
    condition_summary: str = Field(description="Simple explanation of the condition")
    overall_goal: str = Field(description="What we're working toward")
    
    # Step-by-step process
    treatment_steps: List[SimpleTreatmentStep] = Field(description="Ordered treatment steps")
    
    # Tracking
    tracking_frequency: str = Field(description="How often to track progress")
    progress_questions: List[str] = Field(description="Simple questions to track progress")
    
    # Reminders
    reminder_schedule: str = Field(description="When reminders will be sent")
    email_reminders: bool = Field(description="Whether to send email reminders")
    
    # Support
    when_to_contact_help: List[str] = Field(description="When to get help")
    emergency_contacts: List[str] = Field(description="Emergency contact information")

class TreatmentProgress(BaseModel):
    """Simple progress tracking for patients"""
    patient_id: str = Field(description="Patient identifier")
    date: datetime = Field(default_factory=datetime.now)
    step_number: int = Field(description="Which step was completed")
    completed: bool = Field(description="Whether the step was completed")
    difficulty_level: Literal["easy", "medium", "hard"] = Field(description="How difficult it was")
    notes: Optional[str] = Field(description="Patient's notes about the step")
    mood_before: Optional[Literal["great", "good", "okay", "bad", "terrible"]] = Field(description="Mood before the step")
    mood_after: Optional[Literal["great", "good", "okay", "bad", "terrible"]] = Field(description="Mood after the step")

class TreatmentReminder(BaseModel):
    """Email reminder for treatment steps"""
    patient_id: str = Field(description="Patient identifier")
    step_number: int = Field(description="Step to remind about")
    reminder_date: datetime = Field(description="When to send reminder")
    email_subject: str = Field(description="Subject line for email")
    email_body: str = Field(description="Body of reminder email")
    sent: bool = Field(description="Whether reminder was sent")
    sent_date: Optional[datetime] = Field(description="When reminder was actually sent")

# ============================================================================
# NEW SIMPLIFIED TPA SCHEMAS
# ============================================================================

class PlanMetadata(BaseModel):
    """Metadata about the treatment plan"""
    total_duration: str = Field(description="Total duration of the plan")
    total_steps: int = Field(description="Total number of steps")
    estimated_time_per_day: str = Field(description="Estimated time commitment per day")
    frequency: str = Field(description="How often tasks should be done")

class TrackingSchema(BaseModel):
    """Schema for tracking patient progress"""
    daily_tasks: List[str] = Field(description="Tasks to track daily")
    weekly_summary: List[str] = Field(description="Weekly summary fields")
    progress_rules: List[str] = Field(description="Rules for progress monitoring")

class TreatmentPlanSimple(BaseModel):
    """Simple, patient-friendly treatment plan according to new TPA guidelines"""
    patient_id: str = Field(description="Unique patient identifier")
    title: str = Field(description="Simple, clear plan title")
    goal: str = Field(description="What we're working toward")
    
    # Top 3 actions in simple language
    top_actions: List[str] = Field(description="Top 3 actions in simple language")
    
    # Step-by-step actions (numbered)
    step_by_step: List[Dict[str, Any]] = Field(description="Numbered steps with what, when, how long, why, how to track")
    
    # Weekly plan & timeline
    weekly_plan: Dict[str, List[str]] = Field(description="Weekly breakdown of the plan")
    
    # Simple safety note & escalation
    safety_note: str = Field(description="Simple safety note and escalation guidance")
    
    # Plan metadata
    plan_metadata: PlanMetadata = Field(description="Metadata about the plan")
    
    # Tracking schema
    tracking_schema: TrackingSchema = Field(description="Schema for tracking progress")
    
    # Reminder schedule
    reminder_schedule: str = Field(description="When reminders will be sent")

# ============================================================================
# AGENTIC TPA MODELS (MVP)
# ============================================================================

class PatientContext(BaseModel):
    """Patient context for agentic operations"""
    patient_id: str = Field(description="Unique patient identifier")
    current_plan: Optional[TreatmentPlanSimple] = Field(default=None, description="Current active treatment plan")
    symptom_history: List[Dict[str, Any]] = Field(default_factory=list, description="Recent symptom changes")
    last_interaction: datetime = Field(default_factory=datetime.now, description="Last interaction time")
    risk_level: Literal["low", "medium", "high", "emergency"] = Field(default="low", description="Current risk level")

class TPARequest(BaseModel):
    """Request from PIMA to TPA"""
    operation: Literal["create_plan", "adapt_plan", "assess_risk", "get_recommendations"] = Field(description="Type of operation")
    patient_context: PatientContext = Field(description="Current patient context")
    trigger_event: str = Field(description="What triggered this request")
    urgency_level: Literal["low", "medium", "high", "emergency"] = Field(default="medium", description="Urgency of request")
    additional_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional context data")

class TPAResponse(BaseModel):
    """Response from TPA to PIMA"""
    operation_result: Any = Field(description="Result of the operation")
    confidence_score: float = Field(description="Confidence in the response (0.0 to 1.0)", ge=0.0, le=1.0)
    recommendations: List[str] = Field(description="Actionable recommendations")
    next_actions: List[str] = Field(description="Next steps to take")
    requires_pima_action: bool = Field(description="Whether PIMA needs to take action")
    escalation_level: Literal["none", "pima_notification", "specialist_review", "emergency"] = Field(default="none", description="Escalation level required")
    updated_context: PatientContext = Field(description="Updated patient context")

class TPAEvent(BaseModel):
    """Event for real-time communication"""
    event_type: Literal["risk_alert", "plan_update", "intervention_needed", "progress_milestone"] = Field(description="Type of event")
    patient_id: str = Field(description="Patient identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When event occurred")
    message: str = Field(description="Event message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Event data")
    priority: Literal["low", "medium", "high", "critical"] = Field(default="medium", description="Event priority")

# ============================================================================
# SIMPLE API SCHEMAS FOR EASY TPA ACCESS
# ============================================================================

class PlanGenerationRequest(BaseModel):
    """Simple request schema for generating treatment plans"""
    patient_id: Optional[str] = Field(default=None, description="Patient identifier (auto-generated if not provided)")

    # Required patient data
    patient_demographics: PatientDemographics = Field(description="Patient demographic information")
    patient_goals: PatientGoals = Field(description="Patient's stated goals and preferences")
    symptom_clusters: List[SymptomCluster] = Field(description="Recognized symptom clusters from SRA")
    provisional_diagnosis: ProvisionalDiagnosis = Field(description="Provisional diagnosis from DA")
    patient_preferences: PatientPreferences = Field(description="Patient's treatment preferences")

    # Optional safety information
    red_flags: Optional[List[str]] = Field(default_factory=list, description="Any safety concerns or red flags")

    class Config:
        schema_extra = {
            "example": {
                "patient_id": "patient_123",
                "patient_demographics": {
                    "age": 28,
                    "gender": "female",
                    "occupation": "software_engineer",
                    "living_situation": "with_partner"
                },
                "patient_goals": {
                    "primary_goals": ["Reduce anxiety and panic attacks", "Improve sleep quality"],
                    "treatment_preferences": ["CBT approaches", "Mindfulness"],
                    "success_metrics": ["Anxiety rating below 5/10"]
                },
                "symptom_clusters": [
                    {
                        "name": "anxiety",
                        "severity": "moderate",
                        "symptoms": ["racing_thoughts", "physical_tension", "panic_attacks"],
                        "triggers": ["work_deadlines", "social_situations"]
                    }
                ],
                "provisional_diagnosis": {
                    "primary_diagnosis": "Generalized Anxiety Disorder",
                    "severity": "moderate",
                    "confidence_level": 0.85
                },
                "patient_preferences": {
                    "preferred_approach": "self_help",
                    "weekly_time_commitment": 8,
                    "mode_preference": "online",
                    "budget_level": "low_cost"
                },
                "red_flags": []
            }
        }


class PlanUpdateRequest(BaseModel):
    """Simple request schema for updating treatment plans"""
    # All fields are optional - only provide what needs to be updated
    patient_demographics: Optional[PatientDemographics] = Field(default=None, description="Updated patient demographics")
    patient_goals: Optional[PatientGoals] = Field(default=None, description="Updated patient goals")
    symptom_clusters: Optional[List[SymptomCluster]] = Field(default=None, description="Updated symptom clusters")
    provisional_diagnosis: Optional[ProvisionalDiagnosis] = Field(default=None, description="Updated diagnosis")
    patient_preferences: Optional[PatientPreferences] = Field(default=None, description="Updated preferences")
    red_flags: Optional[List[str]] = Field(default=None, description="Updated safety concerns")

    class Config:
        schema_extra = {
            "example": {
                "patient_goals": {
                    "primary_goals": ["Reduce anxiety", "Improve focus", "Better sleep"],
                    "treatment_preferences": ["CBT", "Exercise"],
                    "success_metrics": ["Daily anxiety rating < 4/10"]
                },
                "patient_preferences": {
                    "preferred_approach": "therapy",
                    "weekly_time_commitment": 10,
                    "mode_preference": "in_person",
                    "budget_level": "premium"
                }
            }
        }


class PlanResponse(BaseModel):
    """Simple response schema for treatment plan operations"""
    plan_id: str = Field(description="Unique identifier for the treatment plan")
    plan: TreatmentPlanSimple = Field(description="The treatment plan data")
    created_at: datetime = Field(description="When the plan was created/updated")
    status: str = Field(description="Current status of the plan (active, updated, etc.)")
    message: str = Field(description="Status message")

    class Config:
        schema_extra = {
            "example": {
                "plan_id": "plan_123",
                "plan": {
                    "patient_id": "patient_123",
                    "title": "8-week plan to reduce anxiety & improve daily life",
                    "goal": "Feel calmer and more in control of daily life",
                    "top_actions": [
                        "Weekly CBT sessions (50 min) — focus on thought challenging",
                        "Daily mindfulness practice (10 min) — reduce racing thoughts"
                    ],
                    "step_by_step": [
                        {
                            "step_number": 1,
                            "title": "Learn Thought Challenging",
                            "description": "Practice identifying negative thoughts and replacing them",
                            "when": "Daily",
                            "how_long": "15 minutes",
                            "why": "Helps break the cycle of anxious thinking",
                            "how_to_track": "Rate anxiety before/after (0-10 scale)"
                        }
                    ],
                    "weekly_plan": {
                        "Week 1": ["Onboarding + first steps + start daily routine"],
                        "Weeks 2-7": ["Continue skills + weekly check-ins + homework"],
                        "Week 8": ["Review & plan next steps"]
                    },
                    "safety_note": "If your mood drops quickly, contact emergency services.",
                    "plan_metadata": {
                        "total_duration": "8 weeks",
                        "total_steps": 12,
                        "estimated_time_per_day": "25 minutes",
                        "frequency": "Daily"
                    },
                    "tracking_schema": {
                        "daily_tasks": ["mood_rating", "task_completed"],
                        "weekly_summary": ["mood_trend", "adherence_rate"],
                        "progress_rules": ["If mood drops by 2+ points for 2+ days → flag for clinician review"]
                    },
                    "reminder_schedule": "Daily reminders at 9 AM"
                },
                "created_at": "2024-01-15T10:30:00Z",
                "status": "active",
                "message": "Treatment plan generated successfully"
            }
        }


class ProgressResponse(BaseModel):
    """Simple response schema for progress tracking data"""
    plan_id: str = Field(description="Treatment plan identifier")
    progress: ProgressReport = Field(description="Detailed progress report from TPT")
    retrieved_at: datetime = Field(description="When the progress data was retrieved")
    message: str = Field(description="Status message")

    class Config:
        schema_extra = {
            "example": {
                "plan_id": "plan_123",
                "progress": {
                    "patient_id": "patient_123",
                    "report_date": "2024-01-15",
                    "metrics": {
                        "total_steps": 12,
                        "completed_steps": 8,
                        "completion_rate": 0.67,
                        "current_streak": 5,
                        "longest_streak": 7,
                        "total_days_active": 14
                    },
                    "insights": [
                        "Consistent daily practice improving mood",
                        "Sleep quality improving with routine",
                        "Anxiety ratings dropping steadily"
                    ],
                    "recommendations": [
                        "Consider increasing weekly CBT sessions to 2x per week",
                        "Add evening relaxation routine for better sleep"
                    ],
                    "next_steps": [
                        "Continue current daily mindfulness practice",
                        "Schedule follow-up CBT session",
                        "Track progress weekly"
                    ]
                },
                "retrieved_at": "2024-01-15T10:30:00Z",
                "message": "Progress data retrieved successfully"
            }
        }


# Quick Access Functions for Easy TPA Usage
def create_quick_plan_request(
    age: int,
    gender: str,
    primary_goals: List[str],
    symptoms: List[str],
    diagnosis: str = "General mental health concerns",
    severity: str = "moderate"
) -> PlanGenerationRequest:
    """
    Create a quick treatment plan request with minimal required data.

    This function makes it easy to call TPA from anywhere with just the essential information.

    Args:
        age: Patient age
        gender: Patient gender
        primary_goals: List of treatment goals
        symptoms: List of symptoms
        diagnosis: Primary diagnosis (optional)
        severity: Symptom severity (optional)

    Returns:
        Complete PlanGenerationRequest ready to send to TPA
    """
    return PlanGenerationRequest(
        patient_demographics=PatientDemographics(
            age=age,
            gender=gender,
            occupation=None,
            cultural_background=None,
            living_situation=None,
            support_system=None
        ),
        patient_goals=PatientGoals(
            primary_goals=primary_goals,
            treatment_preferences=[],
            previous_treatments=[],
            success_metrics=None
        ),
        symptom_clusters=[
            SymptomCluster(
                name="primary_symptoms",
                severity=SymptomSeverity(severity),
                symptoms=symptoms,
                triggers=None,
                impact_on_daily_life=None
            )
        ],
        provisional_diagnosis=ProvisionalDiagnosis(
            primary_diagnosis=diagnosis,
            severity=SymptomSeverity(severity),
            comorbidities=[],
            confidence_level=0.7,
            risk_factors=[]
        ),
        patient_preferences=PatientPreferences(
            preferred_approach="self_help",
            weekly_time_commitment=5,
            mode_preference="online",
            budget_level="low_cost",
            cultural_considerations=None
        ),
        red_flags=[]
    )

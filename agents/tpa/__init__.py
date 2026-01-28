"""
Treatment Planning Agent (TPA) Package

The TPA is an AI module in the MindMate pipeline that creates personalized,
structured treatment plans for patients focusing on non-medication interventions.

Key Components:
- TreatmentPlanningAgent: Main agent class for orchestrating treatment planning
- TPATools: Core tools for symptom analysis and intervention selection
- TreatmentGuidelines: Evidence-based intervention database and mapping
- TreatmentPlanValidator: Safety and appropriateness validation
- TPALLMWrapper: LLM integration for enhanced plan generation
- TPAAgenticInterface: Interface for PIMA to call TPA anytime
- TPADatabaseIntegration: Database persistence for TPA interactions
- TreatmentPlanTracker: Progress tracking and reminders

Usage:

    # Original TPA (Treatment Planning)
    from agents.tpa import TreatmentPlanningAgent
    tpa = TreatmentPlanningAgent()
    plan = tpa.create_treatment_plan(demographics, goals, symptoms, diagnosis, preferences)

    # Agentic Interface (PIMA Integration)
    from agents.tpa import TPAAgenticInterface
    tpa_interface = TPAAgenticInterface()
    response = await tpa_interface.handle_request(tpa_request)
"""

# Original TPA components
from .tpa_ import TreatmentPlanningAgent
from .tpa_tools import TPATools
from .treatment_guidelines import TreatmentGuidelines
from .treatment_plan_validator import TreatmentPlanValidator
from .tpa_llm_wrapper import TPALLMWrapper
from .tpa_schemas import (
    TPAInput, TPAOutput, TreatmentPlan, Intervention, SymptomSeverity,
    PatientPreferences, SymptomCluster, ProvisionalDiagnosis, PatientDemographics, PatientGoals,
    SimpleTreatmentPlan, SimpleTreatmentStep, TreatmentProgress, TreatmentReminder,
    TreatmentPlanSimple, PlanMetadata, TrackingSchema
)

# Treatment Plan Tracker (TPT) imports - temporarily disabled
# TODO: Implement proper treatment plan tracker module
# from .treatment_plan_tracker import (
#     TreatmentPlanTracker, TPTAgent, TPTDatabase, TPTReminder, TPTProgress,
#     TreatmentStep, ProgressEntry, ProgressReport, ReminderSchedule,
#     TrackingMetrics, PatientPlan, PlanStatus
# )

# Placeholder classes for now
class TreatmentPlanTracker:
    """Placeholder for TreatmentPlanTracker"""
    pass

class TPTAgent:
    """Placeholder for TPTAgent"""
    pass

class TPTDatabase:
    """Placeholder for TPTDatabase"""
    pass

class TPTReminder:
    """Placeholder for TPTReminder"""
    pass

class TPTProgress:
    """Placeholder for TPTProgress"""
    pass

class TreatmentStep:
    """Placeholder for TreatmentStep"""
    pass

class ProgressEntry:
    """Placeholder for ProgressEntry"""
    pass

class ProgressReport:
    """Placeholder for ProgressReport"""
    pass

class ReminderSchedule:
    """Placeholder for ReminderSchedule"""
    pass

class TrackingMetrics:
    """Placeholder for TrackingMetrics"""
    pass

class PatientPlan:
    """Placeholder for PatientPlan"""
    pass

class PlanStatus:
    """Placeholder for PlanStatus"""
    pass

# Agentic TPA imports
from .tpa_database_integration import TPADatabaseIntegration

# TPA components

__version__ = "2.0.0"
__author__ = "MindMate Team"

__all__ = [
    # Original TPA classes
    "TreatmentPlanningAgent",
    "TPATools",
    "TreatmentGuidelines",
    "TreatmentPlanValidator",
    "TPALLMWrapper",

    # Data models
    "TPAInput",
    "TPAOutput",
    "TreatmentPlan",
    "Intervention",
    "SymptomSeverity",
    "PatientPreferences",
    "SymptomCluster",
    "ProvisionalDiagnosis",
    "PatientDemographics",
    "PatientGoals",

    # Simple treatment plan models
    "SimpleTreatmentPlan",
    "SimpleTreatmentStep",
    "TreatmentProgress",
    "TreatmentReminder",

    # New simplified TPA models
    "TreatmentPlanSimple",
    "PlanMetadata",
    "TrackingSchema",

    # Treatment Plan Tracker (TPT) classes
    "TreatmentPlanTracker",
    "TPTAgent",
    "TPTDatabase",
    "TPTReminder",
    "TPTProgress",

    # TPT data models
    "TreatmentStep",
    "ProgressEntry",
    "ProgressReport",
    "ReminderSchedule",
    "TrackingMetrics",
    "PatientPlan",
    "PlanStatus",

    # Agentic TPA models
    
    "TPADatabaseIntegration",
    "TPARequest",
    "TPAResponse",
    "PatientContext",
    "TPAEvent"
]

# TPA package exports complete

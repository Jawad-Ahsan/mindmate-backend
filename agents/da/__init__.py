"""
DA Diagnosis Agent Package
Provides ReAct-based psychiatric diagnosis using DSM-5 criteria
"""

from .re_da import (
    DiagnosisReActAgent,
    MCPDiagnosisAgent,
    diagnosis_agent,
    diagnose_patient,
    get_available_disorders
)

from .da_tools import (
    DSMCriteriaChecker,
    SymptomAnalyzer,
    ConfidenceCalculator,
    DiagnosisResult,
    dsm_checker,
    symptom_analyzer,
    confidence_calculator
)

__all__ = [
    # Main agent classes
    "DiagnosisReActAgent",
    "MCPDiagnosisAgent",

    # Global instances
    "diagnosis_agent",

    # Convenience functions
    "diagnose_patient",
    "get_available_disorders",

    # Tool classes
    "DSMCriteriaChecker",
    "SymptomAnalyzer",
    "ConfidenceCalculator",
    "DiagnosisResult",

    # Tool instances
    "dsm_checker",
    "symptom_analyzer",
    "confidence_calculator"
]

__version__ = "1.0.0"
__description__ = "ReAct-based psychiatric diagnosis agent using DSM-5 criteria"

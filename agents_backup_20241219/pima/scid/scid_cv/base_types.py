# scid_cv/base_types.py
"""
Base data types and classes for SCID-CV implementation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional

class ResponseType(Enum):
    """Types of responses for SCID questions"""
    YES_NO = "yes_no"
    SCALE = "scale"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    DATE = "date"

class Severity(Enum):
    """Severity levels for symptoms"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"

@dataclass
class SCIDResponse:
    """Single response to a SCID question"""
    question_id: str
    response: Any
    timestamp: datetime = field(default_factory=datetime.now)
    notes: str = ""
    confidence: float = 1.0

@dataclass
class SCIDQuestion:
    """Individual SCID-CV question"""
    id: str
    text: str
    simple_text: str  # Layman-friendly version
    response_type: ResponseType
    options: List[str] = field(default_factory=list)
    scale_range: Tuple[int, int] = (0, 3)
    scale_labels: List[str] = field(default_factory=list)
    required: bool = True
    skip_logic: Dict[str, str] = field(default_factory=dict)  # response -> next_question_id
    criteria_weight: float = 1.0
    symptom_category: str = ""
    follow_up_questions: List[str] = field(default_factory=list)
    help_text: str = ""  # Additional explanation for the question
    examples: List[str] = field(default_factory=list)  # Examples to clarify the question

@dataclass
class SymptomExtraction:
    """Extracted symptom information from responses"""
    symptom_name: str
    present: bool
    severity: Optional[Severity] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    onset: Optional[str] = None
    triggers: List[str] = field(default_factory=list)
    impact_areas: List[str] = field(default_factory=list)
    confidence: float = 1.0

@dataclass
class ModuleResult:
    """Results for a completed SCID-CV module"""
    module_id: str
    module_name: str
    total_score: float
    max_possible_score: float
    percentage_score: float
    criteria_met: bool
    severity_level: Optional[Severity] = None
    symptoms_present: List[SymptomExtraction] = field(default_factory=list)
    responses: List[SCIDResponse] = field(default_factory=list)
    administration_time_mins: int = 0
    completion_date: datetime = field(default_factory=datetime.now)
    notes: str = ""
    raw_scores: Dict[str, float] = field(default_factory=dict)

@dataclass
class SCIDModule:
    """Complete SCID-CV module definition"""
    id: str
    name: str
    description: str
    questions: List[SCIDQuestion] = field(default_factory=list)
    diagnostic_threshold: float = 0.6
    estimated_time_mins: int = 20
    dsm_criteria: List[str] = field(default_factory=list)
    severity_thresholds: Dict[str, float] = field(default_factory=dict)
    category: str = "psychiatric"
    version: str = "1.0"
    clinical_notes: str = ""
    
    def __post_init__(self):
        """Validate module data after initialization"""
        if not self.questions:
            raise ValueError(f"Module {self.id} must have at least one question")
        
        if not 0 <= self.diagnostic_threshold <= 1:
            raise ValueError(f"Diagnostic threshold must be between 0 and 1, got {self.diagnostic_threshold}")
        
        # Validate question IDs are unique
        question_ids = [q.id for q in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError(f"Duplicate question IDs found in module {self.id}")
    
    def get_question_by_id(self, question_id: str) -> Optional[SCIDQuestion]:
        """Get a specific question by ID"""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def get_questions_by_category(self, category: str) -> List[SCIDQuestion]:
        """Get all questions in a specific symptom category"""
        return [q for q in self.questions if q.symptom_category == category]
    
    def get_required_questions(self) -> List[SCIDQuestion]:
        """Get all required questions"""
        return [q for q in self.questions if q.required]
    
    def get_total_possible_score(self) -> float:
        """Calculate the maximum possible score for this module"""
        return sum(q.criteria_weight for q in self.questions)
    
    def validate_responses(self, responses: Dict[str, Any]) -> List[str]:
        """Validate a set of responses against the module's questions"""
        errors = []
        
        # Check required questions
        required_ids = {q.id for q in self.get_required_questions()}
        missing_required = required_ids - set(responses.keys())
        if missing_required:
            errors.append(f"Missing required responses: {missing_required}")
        
        # Check response types
        for question_id, response in responses.items():
            question = self.get_question_by_id(question_id)
            if not question:
                errors.append(f"Unknown question ID: {question_id}")
                continue
            
            # Validate response type
            if question.response_type == ResponseType.YES_NO:
                if response not in [True, False, "yes", "no", "Yes", "No", "YES", "NO", 1, 0]:
                    errors.append(f"Invalid yes/no response for {question_id}: {response}")
            
            elif question.response_type == ResponseType.SCALE:
                try:
                    val = float(response)
                    if not (question.scale_range[0] <= val <= question.scale_range[1]):
                        errors.append(f"Scale response {val} out of range {question.scale_range} for {question_id}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid scale response for {question_id}: {response}")
            
            elif question.response_type == ResponseType.MULTIPLE_CHOICE:
                if isinstance(response, str):
                    if response not in question.options:
                        errors.append(f"Invalid option '{response}' for {question_id}")
                elif isinstance(response, list):
                    invalid_options = set(response) - set(question.options)
                    if invalid_options:
                        errors.append(f"Invalid options {invalid_options} for {question_id}")
        
        return errors
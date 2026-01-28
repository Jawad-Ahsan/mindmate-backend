# scid_pd/base_types.py
"""
Base data types and classes for SCID-PD implementation
Extension of SCID-CV base types for personality disorder assessment
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional

class ResponseType(Enum):
    """Types of responses for SCID-PD questions"""
    YES_NO = "yes_no"
    SCALE = "scale"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    DATE = "date"
    FREQUENCY = "frequency"  # How often behavior occurs
    ONSET_AGE = "onset_age"  # When pattern first began

class PersonalityDimensionType(Enum):
    """Core personality dimensions assessed"""
    INTERPERSONAL = "interpersonal"
    AFFECTIVE = "affective"
    COGNITIVE = "cognitive"
    BEHAVIORAL = "behavioral"
    IDENTITY = "identity"

class PervasivenessCriteria(Enum):
    """How pervasive the pattern is across contexts"""
    LIMITED = "limited"  # Few contexts
    MODERATE = "moderate"  # Some contexts
    EXTENSIVE = "extensive"  # Most contexts
    PERVASIVE = "pervasive"  # All contexts

class OnsetCriteria(Enum):
    """When the personality pattern began"""
    CHILDHOOD = "childhood"  # Before age 12
    ADOLESCENCE = "adolescence"  # Ages 12-18
    EARLY_ADULTHOOD = "early_adulthood"  # Ages 18-25
    UNKNOWN = "unknown"

class Severity(Enum):
    """Severity levels for personality patterns"""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EXTREME = "extreme"

class DSMCluster(Enum):
    """DSM-5 personality disorder clusters"""
    CLUSTER_A = "cluster_a"  # Odd, eccentric
    CLUSTER_B = "cluster_b"  # Dramatic, emotional, erratic
    CLUSTER_C = "cluster_c"  # Anxious, fearful

@dataclass
class SCIDPDResponse:
    """Single response to a SCID-PD question"""
    question_id: str
    response: Any
    timestamp: datetime = field(default_factory=datetime.now)
    notes: str = ""
    confidence: float = 1.0
    onset_age: Optional[int] = None  # Age when pattern began
    examples_provided: List[str] = field(default_factory=list)  # Specific examples given

@dataclass
class SCIDPDQuestion:
    """Individual SCID-PD question"""
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
    dimension_type: PersonalityDimensionType = PersonalityDimensionType.BEHAVIORAL
    trait_measured: str = ""  # Specific trait or pattern being assessed
    follow_up_questions: List[str] = field(default_factory=list)
    help_text: str = ""
    examples: List[str] = field(default_factory=list)
    requires_examples: bool = False  # Whether concrete examples are required
    onset_relevant: bool = True  # Whether onset timing is important
    pervasiveness_check: bool = True  # Whether to assess across contexts

@dataclass
class PersonalityPatternExtraction:
    """Extracted personality pattern information from responses"""
    pattern_name: str
    present: bool
    severity: Optional[Severity] = None
    dimension_type: PersonalityDimensionType = PersonalityDimensionType.BEHAVIORAL
    pervasiveness: Optional[PervasivenessCriteria] = None
    onset_period: Optional[OnsetCriteria] = None
    onset_age: Optional[int] = None
    contexts_affected: List[str] = field(default_factory=list)  # Work, relationships, etc.
    behavioral_examples: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    functional_impairment: List[str] = field(default_factory=list)
    stability_over_time: bool = True  # Whether pattern is stable
    confidence: float = 1.0

@dataclass
class PersonalityModuleResult:
    """Results for a completed SCID-PD module"""
    module_id: str
    module_name: str
    dsm_cluster: DSMCluster
    total_score: float
    max_possible_score: float
    percentage_score: float
    criteria_met: bool
    dimensional_score: Optional[float] = None  # Dimensional scoring (0-100)
    severity_level: Optional[Severity] = None
    patterns_present: List[PersonalityPatternExtraction] = field(default_factory=list)
    responses: List[SCIDPDResponse] = field(default_factory=list)
    administration_time_mins: int = 0
    completion_date: datetime = field(default_factory=datetime.now)
    notes: str = ""
    raw_scores: Dict[str, float] = field(default_factory=dict)
    onset_pattern: Optional[OnsetCriteria] = None
    pervasiveness_assessment: Optional[PervasivenessCriteria] = None
    differential_considerations: List[str] = field(default_factory=list)  # Other PDs to consider

@dataclass
class SCIDPDModule:
    """Complete SCID-PD module definition for a personality disorder"""
    id: str
    name: str
    description: str
    dsm_cluster: DSMCluster
    questions: List[SCIDPDQuestion] = field(default_factory=list)
    diagnostic_threshold: float = 0.6
    dimensional_threshold: float = 50.0  # For dimensional scoring
    estimated_time_mins: int = 30
    dsm_criteria: List[str] = field(default_factory=list)
    severity_thresholds: Dict[str, float] = field(default_factory=dict)
    core_features: List[str] = field(default_factory=list)  # Core personality features
    differential_diagnoses: List[str] = field(default_factory=list)  # Related PDs
    version: str = "1.0"
    clinical_notes: str = ""
    requires_onset_before_18: bool = True  # Most PDs require early onset
    minimum_criteria_count: int = 5  # Minimum number of criteria needed
    
    def __post_init__(self):
        """Validate module data after initialization"""
        if not self.questions:
            raise ValueError(f"Module {self.id} must have at least one question")
        
        if not 0 <= self.diagnostic_threshold <= 1:
            raise ValueError(f"Diagnostic threshold must be between 0 and 1, got {self.diagnostic_threshold}")
        
        if not 0 <= self.dimensional_threshold <= 100:
            raise ValueError(f"Dimensional threshold must be between 0 and 100, got {self.dimensional_threshold}")
        
        # Validate question IDs are unique
        question_ids = [q.id for q in self.questions]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError(f"Duplicate question IDs found in module {self.id}")
    
    def get_question_by_id(self, question_id: str) -> Optional[SCIDPDQuestion]:
        """Get a specific question by ID"""
        for question in self.questions:
            if question.id == question_id:
                return question
        return None
    
    def get_questions_by_dimension(self, dimension: PersonalityDimensionType) -> List[SCIDPDQuestion]:
        """Get all questions for a specific personality dimension"""
        return [q for q in self.questions if q.dimension_type == dimension]
    
    def get_core_criteria_questions(self) -> List[SCIDPDQuestion]:
        """Get questions that assess core diagnostic criteria"""
        return [q for q in self.questions if q.criteria_weight >= 1.0]
    
    def get_required_questions(self) -> List[SCIDPDQuestion]:
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
        
        # Check response types and validate content
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
            
            elif question.response_type == ResponseType.ONSET_AGE:
                try:
                    age = int(response)
                    if not (0 <= age <= 100):
                        errors.append(f"Invalid age {age} for {question_id}")
                except (ValueError, TypeError):
                    errors.append(f"Invalid age response for {question_id}: {response}")
        
        return errors

@dataclass
class PersonalityProfile:
    """Complete personality assessment profile across all disorders"""
    assessment_date: datetime = field(default_factory=datetime.now)
    module_results: List[PersonalityModuleResult] = field(default_factory=list)
    overall_severity: Optional[Severity] = None
    primary_diagnoses: List[str] = field(default_factory=list)
    secondary_features: List[str] = field(default_factory=list)
    dimensional_scores: Dict[str, float] = field(default_factory=dict)  # PD -> dimensional score
    cluster_summary: Dict[DSMCluster, int] = field(default_factory=dict)  # Cluster -> # positive
    total_assessment_time: int = 0
    clinician_notes: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    def get_positive_diagnoses(self) -> List[PersonalityModuleResult]:
        """Get all modules that met diagnostic criteria"""
        return [result for result in self.module_results if result.criteria_met]
    
    def get_dimensional_summary(self) -> Dict[str, float]:
        """Get dimensional scores for all assessed personality disorders"""
        return {result.module_name: result.dimensional_score or 0.0 
                for result in self.module_results}
    
    def get_cluster_distribution(self) -> Dict[DSMCluster, List[str]]:
        """Get distribution of positive diagnoses by cluster"""
        distribution = {cluster: [] for cluster in DSMCluster}
        
        for result in self.get_positive_diagnoses():
            distribution[result.dsm_cluster].append(result.module_name)
        
        return distribution
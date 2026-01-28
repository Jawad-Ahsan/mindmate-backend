"""
DSM Criteria Analyzer
Real-time analysis of DSM-5 criteria achievement and dynamic insights
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
from collections import defaultdict

# Import SCID components
from .scid_cv.base_types import SCIDModule, SCIDQuestion, ResponseType, ModuleResult
from .scid_pd.base_types import SCIDPDModule, SCIDPDQuestion, PersonalityModuleResult

logger = logging.getLogger(__name__)

class CriteriaStatus(Enum):
    """Status of DSM criteria achievement"""
    NOT_MET = "not_met"
    PARTIALLY_MET = "partially_met"
    MET = "met"
    AMBIGUOUS = "ambiguous"
    NEEDS_FOLLOW_UP = "needs_follow_up"

class AmbiguityType(Enum):
    """Types of response ambiguities"""
    UNCLEAR_SEVERITY = "unclear_severity"
    UNCLEAR_DURATION = "unclear_duration"
    UNCLEAR_FREQUENCY = "unclear_frequency"
    CONTRADICTORY_RESPONSES = "contradictory_responses"
    MISSING_CONTEXT = "missing_context"
    VAGUE_DESCRIPTION = "vague_description"
    NEEDS_EXAMPLES = "needs_examples"

@dataclass
class CriteriaAnalysis:
    """Analysis of a single DSM criterion"""
    criterion_id: str
    criterion_text: str
    status: CriteriaStatus
    confidence: float  # 0-1 scale
    supporting_responses: List[str] = field(default_factory=list)
    contradicting_responses: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    severity_score: float = 0.0
    frequency_score: float = 0.0
    duration_score: float = 0.0
    impairment_score: float = 0.0

@dataclass
class AmbiguityFlag:
    """Flag for ambiguous or unclear responses"""
    question_id: str
    question_text: str
    response: Any
    ambiguity_type: AmbiguityType
    severity: str  # "low", "medium", "high"
    description: str
    suggested_follow_up: str
    confidence: float = 0.0

@dataclass
class RealTimeAnalysis:
    """Real-time analysis results"""
    module_id: str
    module_name: str
    timestamp: datetime
    total_criteria: int
    criteria_met: int
    criteria_partially_met: int
    criteria_not_met: int
    criteria_ambiguous: int
    overall_progress: float  # 0-100
    diagnostic_likelihood: float  # 0-1
    severity_estimate: str
    ambiguities: List[AmbiguityFlag] = field(default_factory=list)
    criteria_analysis: List[CriteriaAnalysis] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    protective_factors: List[str] = field(default_factory=list)

@dataclass
class ComprehensiveInsights:
    """Comprehensive insights from the analysis"""
    diagnostic_summary: str
    key_symptoms: List[str]
    severity_assessment: str
    functional_impairment: str
    differential_considerations: List[str]
    treatment_implications: List[str]
    risk_assessment: str
    follow_up_priorities: List[str]
    clinical_notes: str

class DSMCriteriaAnalyzer:
    """
    Real-time DSM criteria analyzer for SCID modules
    
    Features:
    - Real-time criteria tracking
    - Ambiguity detection and flagging
    - Dynamic progress analysis
    - Comprehensive insights generation
    - Follow-up question suggestions
    """

    def __init__(self):
        """Initialize the DSM criteria analyzer"""
        self.analysis_history: List[RealTimeAnalysis] = []
        self.criteria_mappings = self._build_criteria_mappings()
        self.ambiguity_patterns = self._build_ambiguity_patterns()
        self.severity_keywords = self._build_severity_keywords()
        self.duration_keywords = self._build_duration_keywords()
        self.frequency_keywords = self._build_frequency_keywords()

    def _build_criteria_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Build mappings from questions to DSM criteria"""
        return {
            # MDD Criteria
            "MDD": {
                "A1": {
                    "criterion": "Depressed mood most of the day, nearly every day",
                    "questions": ["MDD_01", "MDD_01A"],
                    "required": True,
                    "weight": 2.0
                },
                "A2": {
                    "criterion": "Markedly diminished interest or pleasure in activities",
                    "questions": ["MDD_02", "MDD_02A"],
                    "required": True,
                    "weight": 2.0
                },
                "A3": {
                    "criterion": "Significant weight loss/gain or appetite changes",
                    "questions": ["MDD_03"],
                    "required": False,
                    "weight": 1.0
                },
                "A4": {
                    "criterion": "Insomnia or hypersomnia nearly every day",
                    "questions": ["MDD_04"],
                    "required": False,
                    "weight": 1.0
                },
                "A5": {
                    "criterion": "Psychomotor agitation or retardation",
                    "questions": ["MDD_05"],
                    "required": False,
                    "weight": 1.0
                },
                "A6": {
                    "criterion": "Fatigue or loss of energy nearly every day",
                    "questions": ["MDD_06"],
                    "required": False,
                    "weight": 1.0
                },
                "A7": {
                    "criterion": "Feelings of worthlessness or inappropriate guilt",
                    "questions": ["MDD_07", "MDD_07A"],
                    "required": False,
                    "weight": 1.0
                },
                "A8": {
                    "criterion": "Diminished ability to think or concentrate",
                    "questions": ["MDD_08"],
                    "required": False,
                    "weight": 1.0
                },
                "A9": {
                    "criterion": "Recurrent thoughts of death or suicidal ideation",
                    "questions": ["MDD_09", "MDD_09A", "MDD_09B"],
                    "required": False,
                    "weight": 1.5
                }
            },
            # BPD Criteria
            "BPD": {
                "A1": {
                    "criterion": "Frantic efforts to avoid real or imagined abandonment",
                    "questions": ["BPD_001", "BPD_002"],
                    "required": False,
                    "weight": 1.0
                },
                "A2": {
                    "criterion": "Unstable and intense interpersonal relationships",
                    "questions": ["BPD_003", "BPD_004"],
                    "required": False,
                    "weight": 1.0
                },
                "A3": {
                    "criterion": "Identity disturbance",
                    "questions": ["BPD_005", "BPD_006"],
                    "required": False,
                    "weight": 1.0
                },
                "A4": {
                    "criterion": "Impulsivity in potentially self-damaging areas",
                    "questions": ["BPD_007", "BPD_008"],
                    "required": False,
                    "weight": 1.0
                },
                "A5": {
                    "criterion": "Recurrent suicidal behavior or self-mutilation",
                    "questions": ["BPD_009", "BPD_010"],
                    "required": False,
                    "weight": 1.5
                },
                "A6": {
                    "criterion": "Affective instability due to marked reactivity of mood",
                    "questions": ["BPD_011", "BPD_012"],
                    "required": False,
                    "weight": 1.0
                },
                "A7": {
                    "criterion": "Chronic feelings of emptiness",
                    "questions": ["BPD_013"],
                    "required": False,
                    "weight": 1.0
                },
                "A8": {
                    "criterion": "Inappropriate, intense anger",
                    "questions": ["BPD_014", "BPD_015"],
                    "required": False,
                    "weight": 1.0
                },
                "A9": {
                    "criterion": "Transient, stress-related paranoid ideation",
                    "questions": ["BPD_016", "BPD_017"],
                    "required": False,
                    "weight": 1.0
                }
            },
            # GAD Criteria
            "GAD": {
                "A1": {
                    "criterion": "Excessive anxiety and worry occurring more days than not",
                    "questions": ["GAD_01", "GAD_02", "GAD_03", "GAD_04"],
                    "required": True,
                    "weight": 2.0
                },
                "A2": {
                    "criterion": "Difficult to control the worry",
                    "questions": ["GAD_02"],
                    "required": True,
                    "weight": 2.0
                },
                "A3": {
                    "criterion": "Associated with three or more symptoms",
                    "questions": ["GAD_05", "GAD_06", "GAD_07", "GAD_08", "GAD_09", "GAD_10"],
                    "required": True,
                    "weight": 1.5
                }
            }
        }

    def _build_ambiguity_patterns(self) -> Dict[AmbiguityType, List[str]]:
        """Build patterns for detecting ambiguities"""
        return {
            AmbiguityType.UNCLEAR_SEVERITY: [
                r"\b(somewhat|kind of|a little|maybe|possibly)\b",
                r"\b(not sure|unsure|don't know)\b",
                r"\b(sometimes|occasionally|rarely)\b"
            ],
            AmbiguityType.UNCLEAR_DURATION: [
                r"\b(recently|lately|for a while|some time)\b",
                r"\b(on and off|off and on|intermittently)\b",
                r"\b(not sure how long|can't remember)\b"
            ],
            AmbiguityType.UNCLEAR_FREQUENCY: [
                r"\b(now and then|every so often|from time to time)\b",
                r"\b(when stressed|when tired|sometimes)\b",
                r"\b(depends|varies|changes)\b"
            ],
            AmbiguityType.VAGUE_DESCRIPTION: [
                r"\b(not good|bad|terrible|awful)\b",
                r"\b(weird|strange|different)\b",
                r"\b(just not right|off|wrong)\b"
            ]
        }

    def _build_severity_keywords(self) -> Dict[str, float]:
        """Build severity scoring keywords"""
        return {
            "severe": 3.0,
            "very": 2.5,
            "extremely": 3.0,
            "intense": 2.5,
            "overwhelming": 3.0,
            "debilitating": 3.0,
            "moderate": 2.0,
            "significant": 2.0,
            "considerable": 2.0,
            "mild": 1.0,
            "slight": 1.0,
            "minor": 1.0,
            "minimal": 0.5
        }

    def _build_duration_keywords(self) -> Dict[str, float]:
        """Build duration scoring keywords"""
        return {
            "years": 3.0,
            "months": 2.0,
            "weeks": 1.5,
            "days": 1.0,
            "hours": 0.5,
            "constantly": 3.0,
            "always": 3.0,
            "never": 0.0,
            "rarely": 0.5,
            "sometimes": 1.0,
            "often": 2.0,
            "frequently": 2.5
        }

    def _build_frequency_keywords(self) -> Dict[str, float]:
        """Build frequency scoring keywords"""
        return {
            "daily": 3.0,
            "every day": 3.0,
            "weekly": 2.0,
            "monthly": 1.0,
            "rarely": 0.5,
            "never": 0.0,
            "sometimes": 1.0,
            "often": 2.0,
            "frequently": 2.5,
            "constantly": 3.0
        }

    def analyze_responses_real_time(
        self,
        module: Union[SCIDModule, SCIDPDModule],
        responses: Dict[str, Any],
        session_id: str
    ) -> RealTimeAnalysis:
        """
        Analyze responses in real-time and provide comprehensive insights
        
        Args:
            module: The SCID module being administered
            responses: Current responses dictionary
            session_id: Session identifier
            
        Returns:
            RealTimeAnalysis object with comprehensive insights
        """
        module_id = module.id
        module_name = module.name
        
        # Get criteria mapping for this module
        criteria_mapping = self.criteria_mappings.get(module_id, {})
        
        # Analyze each criterion
        criteria_analysis = []
        for criterion_id, criterion_info in criteria_mapping.items():
            analysis = self._analyze_criterion(
                criterion_id, criterion_info, responses, module
            )
            criteria_analysis.append(analysis)
        
        # Detect ambiguities
        ambiguities = self._detect_ambiguities(responses, module)
        
        # Calculate overall progress and diagnostic likelihood
        total_criteria = len(criteria_mapping)
        criteria_met = len([c for c in criteria_analysis if c.status == CriteriaStatus.MET])
        criteria_partially_met = len([c for c in criteria_analysis if c.status == CriteriaStatus.PARTIALLY_MET])
        criteria_not_met = len([c for c in criteria_analysis if c.status == CriteriaStatus.NOT_MET])
        criteria_ambiguous = len([c for c in criteria_analysis if c.status == CriteriaStatus.AMBIGUOUS])
        
        # Calculate progress
        total_questions = len(module.questions)
        answered_questions = len(responses)
        overall_progress = (answered_questions / total_questions) * 100 if total_questions > 0 else 0
        
        # Calculate diagnostic likelihood
        diagnostic_likelihood = self._calculate_diagnostic_likelihood(criteria_analysis, module)
        
        # Generate insights and recommendations
        insights = self._generate_insights(criteria_analysis, responses, module)
        recommendations = self._generate_recommendations(criteria_analysis, ambiguities, module)
        risk_factors = self._identify_risk_factors(responses, module)
        protective_factors = self._identify_protective_factors(responses, module)
        
        # Determine severity estimate
        severity_estimate = self._estimate_severity(criteria_analysis, responses)
        
        analysis = RealTimeAnalysis(
            module_id=module_id,
            module_name=module_name,
            timestamp=datetime.now(),
            total_criteria=total_criteria,
            criteria_met=criteria_met,
            criteria_partially_met=criteria_partially_met,
            criteria_not_met=criteria_not_met,
            criteria_ambiguous=criteria_ambiguous,
            overall_progress=overall_progress,
            diagnostic_likelihood=diagnostic_likelihood,
            severity_estimate=severity_estimate,
            ambiguities=ambiguities,
            criteria_analysis=criteria_analysis,
            insights=insights,
            recommendations=recommendations,
            risk_factors=risk_factors,
            protective_factors=protective_factors
        )
        
        # Store in history
        self.analysis_history.append(analysis)
        
        return analysis

    def _analyze_criterion(
        self,
        criterion_id: str,
        criterion_info: Dict[str, Any],
        responses: Dict[str, Any],
        module: Union[SCIDModule, SCIDPDModule]
    ) -> CriteriaAnalysis:
        """Analyze a single DSM criterion"""
        criterion_text = criterion_info["criterion"]
        required_questions = criterion_info["questions"]
        weight = criterion_info.get("weight", 1.0)
        
        # Get responses for this criterion
        criterion_responses = {}
        for question_id in required_questions:
            if question_id in responses:
                criterion_responses[question_id] = responses[question_id]
        
        # Analyze the responses
        status, confidence = self._evaluate_criterion_responses(
            criterion_responses, criterion_info, module
        )
        
        # Calculate scores
        severity_score = self._calculate_severity_score(criterion_responses)
        frequency_score = self._calculate_frequency_score(criterion_responses)
        duration_score = self._calculate_duration_score(criterion_responses)
        impairment_score = self._calculate_impairment_score(criterion_responses)
        
        # Identify supporting and contradicting responses
        supporting_responses = []
        contradicting_responses = []
        missing_information = []
        
        for question_id, response in criterion_responses.items():
            if self._supports_criterion(response, criterion_info):
                supporting_responses.append(f"{question_id}: {response}")
            elif self._contradicts_criterion(response, criterion_info):
                contradicting_responses.append(f"{question_id}: {response}")
        
        # Identify missing information
        for question_id in required_questions:
            if question_id not in responses:
                missing_information.append(question_id)
        
        # Generate follow-up questions
        follow_up_questions = self._generate_follow_up_questions(
            criterion_responses, criterion_info, status
        )
        
        return CriteriaAnalysis(
            criterion_id=criterion_id,
            criterion_text=criterion_text,
            status=status,
            confidence=confidence,
            supporting_responses=supporting_responses,
            contradicting_responses=contradicting_responses,
            missing_information=missing_information,
            follow_up_questions=follow_up_questions,
            severity_score=severity_score,
            frequency_score=frequency_score,
            duration_score=duration_score,
            impairment_score=impairment_score
        )

    def _evaluate_criterion_responses(
        self,
        responses: Dict[str, Any],
        criterion_info: Dict[str, Any],
        module: Union[SCIDModule, SCIDPDModule]
    ) -> Tuple[CriteriaStatus, float]:
        """Evaluate responses for a criterion and determine status"""
        if not responses:
            return CriteriaStatus.NOT_MET, 0.0
        
        # Count positive responses
        positive_count = 0
        total_count = len(responses)
        confidence_scores = []
        
        for question_id, response in responses.items():
            question = module.get_question_by_id(question_id)
            if not question:
                continue
            
            # Evaluate response
            is_positive, confidence = self._evaluate_response(response, question, criterion_info)
            if is_positive:
                positive_count += 1
            confidence_scores.append(confidence)
        
        # Determine status based on positive responses
        if total_count == 0:
            return CriteriaStatus.NOT_MET, 0.0
        
        positive_ratio = positive_count / total_count
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        if positive_ratio >= 0.8:
            return CriteriaStatus.MET, avg_confidence
        elif positive_ratio >= 0.4:
            return CriteriaStatus.PARTIALLY_MET, avg_confidence
        elif positive_ratio > 0:
            return CriteriaStatus.AMBIGUOUS, avg_confidence
        else:
            return CriteriaStatus.NOT_MET, avg_confidence

    def _evaluate_response(
        self,
        response: Any,
        question: Union[SCIDQuestion, SCIDPDQuestion],
        criterion_info: Dict[str, Any]
    ) -> Tuple[bool, float]:
        """Evaluate if a response supports the criterion"""
        if response is None:
            return False, 0.0
        
        # Convert response to string for analysis
        response_str = str(response).lower()
        
        # Check for positive indicators
        positive_indicators = ["yes", "true", "1", "often", "frequently", "always", "severe", "very"]
        negative_indicators = ["no", "false", "0", "never", "rarely", "not"]
        
        # Check for positive response
        is_positive = any(indicator in response_str for indicator in positive_indicators)
        is_negative = any(indicator in response_str for indicator in negative_indicators)
        
        # Calculate confidence based on response clarity
        confidence = 1.0
        if is_positive and is_negative:
            confidence = 0.5  # Contradictory response
        elif not is_positive and not is_negative:
            confidence = 0.7  # Ambiguous response
        
        return is_positive, confidence

    def _supports_criterion(self, response: Any, criterion_info: Dict[str, Any]) -> bool:
        """Check if response supports the criterion"""
        is_positive, _ = self._evaluate_response(response, None, criterion_info)
        return is_positive

    def _contradicts_criterion(self, response: Any, criterion_info: Dict[str, Any]) -> bool:
        """Check if response contradicts the criterion"""
        is_positive, _ = self._evaluate_response(response, None, criterion_info)
        return not is_positive

    def _detect_ambiguities(
        self,
        responses: Dict[str, Any],
        module: Union[SCIDModule, SCIDPDModule]
    ) -> List[AmbiguityFlag]:
        """Detect ambiguous or unclear responses"""
        ambiguities = []
        
        for question_id, response in responses.items():
            question = module.get_question_by_id(question_id)
            if not question:
                continue
            
            # Check for ambiguities
            ambiguity_flags = self._check_response_ambiguity(response, question, question_id)
            ambiguities.extend(ambiguity_flags)
        
        return ambiguities

    def _check_response_ambiguity(
        self,
        response: Any,
        question: Union[SCIDQuestion, SCIDPDQuestion],
        question_id: str
    ) -> List[AmbiguityFlag]:
        """Check a single response for ambiguities"""
        ambiguities = []
        response_str = str(response).lower() if response else ""
        
        # Check for unclear severity
        if any(pattern in response_str for pattern in self.ambiguity_patterns[AmbiguityType.UNCLEAR_SEVERITY]):
            ambiguities.append(AmbiguityFlag(
                question_id=question_id,
                question_text=question.simple_text,
                response=response,
                ambiguity_type=AmbiguityType.UNCLEAR_SEVERITY,
                severity="medium",
                description="Response indicates unclear severity level",
                suggested_follow_up="Can you be more specific about how severe this is?",
                confidence=0.8
            ))
        
        # Check for unclear duration
        if any(pattern in response_str for pattern in self.ambiguity_patterns[AmbiguityType.UNCLEAR_DURATION]):
            ambiguities.append(AmbiguityFlag(
                question_id=question_id,
                question_text=question.simple_text,
                response=response,
                ambiguity_type=AmbiguityType.UNCLEAR_DURATION,
                severity="medium",
                description="Response indicates unclear duration",
                suggested_follow_up="How long have you been experiencing this?",
                confidence=0.8
            ))
        
        # Check for vague descriptions
        if any(pattern in response_str for pattern in self.ambiguity_patterns[AmbiguityType.VAGUE_DESCRIPTION]):
            ambiguities.append(AmbiguityFlag(
                question_id=question_id,
                question_text=question.simple_text,
                response=response,
                ambiguity_type=AmbiguityType.VAGUE_DESCRIPTION,
                severity="low",
                description="Response is vague and needs clarification",
                suggested_follow_up="Can you provide more specific details or examples?",
                confidence=0.7
            ))
        
        return ambiguities

    def _calculate_diagnostic_likelihood(
        self,
        criteria_analysis: List[CriteriaAnalysis],
        module: Union[SCIDModule, SCIDPDModule]
    ) -> float:
        """Calculate the likelihood of meeting diagnostic criteria"""
        if not criteria_analysis:
            return 0.0
        
        # Calculate weighted score
        total_weight = 0.0
        weighted_score = 0.0
        
        for analysis in criteria_analysis:
            weight = 1.0  # Default weight
            if analysis.status == CriteriaStatus.MET:
                weighted_score += weight * analysis.confidence
            elif analysis.status == CriteriaStatus.PARTIALLY_MET:
                weighted_score += weight * analysis.confidence * 0.5
            elif analysis.status == CriteriaStatus.AMBIGUOUS:
                weighted_score += weight * analysis.confidence * 0.3
            
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return min(weighted_score / total_weight, 1.0)

    def _calculate_severity_score(self, responses: Dict[str, Any]) -> float:
        """Calculate severity score from responses"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        count = 0
        
        for response in responses.values():
            response_str = str(response).lower()
            
            # Check for severity keywords
            for keyword, score in self.severity_keywords.items():
                if keyword in response_str:
                    total_score += score
                    count += 1
                    break
        
        return total_score / count if count > 0 else 0.0

    def _calculate_frequency_score(self, responses: Dict[str, Any]) -> float:
        """Calculate frequency score from responses"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        count = 0
        
        for response in responses.values():
            response_str = str(response).lower()
            
            # Check for frequency keywords
            for keyword, score in self.frequency_keywords.items():
                if keyword in response_str:
                    total_score += score
                    count += 1
                    break
        
        return total_score / count if count > 0 else 0.0

    def _calculate_duration_score(self, responses: Dict[str, Any]) -> float:
        """Calculate duration score from responses"""
        if not responses:
            return 0.0
        
        total_score = 0.0
        count = 0
        
        for response in responses.values():
            response_str = str(response).lower()
            
            # Check for duration keywords
            for keyword, score in self.duration_keywords.items():
                if keyword in response_str:
                    total_score += score
                    count += 1
                    break
        
        return total_score / count if count > 0 else 0.0

    def _calculate_impairment_score(self, responses: Dict[str, Any]) -> float:
        """Calculate functional impairment score from responses"""
        if not responses:
            return 0.0
        
        impairment_keywords = {
            "can't work": 3.0,
            "can't function": 3.0,
            "severe impairment": 3.0,
            "significant problems": 2.5,
            "major problems": 2.5,
            "moderate problems": 2.0,
            "some problems": 1.5,
            "mild problems": 1.0,
            "no problems": 0.0
        }
        
        total_score = 0.0
        count = 0
        
        for response in responses.values():
            response_str = str(response).lower()
            
            for keyword, score in impairment_keywords.items():
                if keyword in response_str:
                    total_score += score
                    count += 1
                    break
        
        return total_score / count if count > 0 else 0.0

    def _generate_insights(
        self,
        criteria_analysis: List[CriteriaAnalysis],
        responses: Dict[str, Any],
        module: Union[SCIDModule, SCIDPDModule]
    ) -> List[str]:
        """Generate clinical insights from the analysis"""
        insights = []
        
        # Count criteria status
        met_criteria = [c for c in criteria_analysis if c.status == CriteriaStatus.MET]
        partial_criteria = [c for c in criteria_analysis if c.status == CriteriaStatus.PARTIALLY_MET]
        ambiguous_criteria = [c for c in criteria_analysis if c.status == CriteriaStatus.AMBIGUOUS]
        
        # Generate insights based on criteria status
        if met_criteria:
            insights.append(f"✅ {len(met_criteria)} criteria clearly met with high confidence")
        
        if partial_criteria:
            insights.append(f"⚠️ {len(partial_criteria)} criteria partially met - needs further assessment")
        
        if ambiguous_criteria:
            insights.append(f"❓ {len(ambiguous_criteria)} criteria have ambiguous responses - clarification needed")
        
        return insights

    def _generate_recommendations(
        self,
        criteria_analysis: List[CriteriaAnalysis],
        ambiguities: List[AmbiguityFlag],
        module: Union[SCIDModule, SCIDPDModule]
    ) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = []
        
        # Recommendations based on ambiguities
        if ambiguities:
            recommendations.append(f"📝 {len(ambiguities)} responses need follow-up clarification")
        
        # General recommendations
        recommendations.append("📊 Continue assessment to gather complete diagnostic picture")
        
        return recommendations

    def _identify_risk_factors(self, responses: Dict[str, Any], module: Union[SCIDModule, SCIDPDModule]) -> List[str]:
        """Identify risk factors from responses"""
        risk_factors = []
        
        # Check for suicidal ideation
        suicide_keywords = ["suicide", "kill myself", "end my life", "want to die"]
        for response in responses.values():
            response_str = str(response).lower()
            if any(keyword in response_str for keyword in suicide_keywords):
                risk_factors.append("Suicidal ideation")
                break
        
        return list(set(risk_factors))  # Remove duplicates

    def _identify_protective_factors(self, responses: Dict[str, Any], module: Union[SCIDModule, SCIDPDModule]) -> List[str]:
        """Identify protective factors from responses"""
        protective_factors = []
        
        # Check for social support
        support_keywords = ["family support", "friends", "supportive", "help from others"]
        for response in responses.values():
            response_str = str(response).lower()
            if any(keyword in response_str for keyword in support_keywords):
                protective_factors.append("Social support")
                break
        
        return list(set(protective_factors))  # Remove duplicates

    def _identify_high_risk_indicators(self, responses: Dict[str, Any]) -> List[str]:
        """Identify high-risk indicators from responses"""
        high_risk_indicators = []
        
        # Check for severe symptoms
        severe_keywords = ["severe", "extreme", "overwhelming", "debilitating", "unbearable"]
        for response in responses.values():
            response_str = str(response).lower()
            if any(keyword in response_str for keyword in severe_keywords):
                high_risk_indicators.append("Severe symptom severity")
                break
        
        # Check for functional impairment
        impairment_keywords = ["can't work", "can't function", "can't take care", "unable to"]
        for response in responses.values():
            response_str = str(response).lower()
            if any(keyword in response_str for keyword in impairment_keywords):
                high_risk_indicators.append("Severe functional impairment")
                break
        
        return list(set(high_risk_indicators))  # Remove duplicates

    def _estimate_severity(self, criteria_analysis: List[CriteriaAnalysis], responses: Dict[str, Any]) -> str:
        """Estimate overall severity based on criteria analysis"""
        if not criteria_analysis:
            return "Unknown"
        
        # Calculate average severity scores
        severity_scores = [c.severity_score for c in criteria_analysis if c.severity_score > 0]
        if not severity_scores:
            return "Unknown"
        
        avg_severity = sum(severity_scores) / len(severity_scores)
        
        if avg_severity >= 2.5:
            return "Severe"
        elif avg_severity >= 1.5:
            return "Moderate"
        elif avg_severity >= 0.5:
            return "Mild"
        else:
            return "Minimal"

    def _generate_follow_up_questions(
        self,
        responses: Dict[str, Any],
        criterion_info: Dict[str, Any],
        status: CriteriaStatus
    ) -> List[str]:
        """Generate follow-up questions for ambiguous or partially met criteria"""
        follow_up_questions = []
        
        if status == CriteriaStatus.AMBIGUOUS:
            follow_up_questions.append("Can you provide more specific details about this?")
            follow_up_questions.append("How often does this occur?")
            follow_up_questions.append("How long have you been experiencing this?")
        
        elif status == CriteriaStatus.PARTIALLY_MET:
            follow_up_questions.append("Can you give me examples of when this happens?")
            follow_up_questions.append("How does this affect your daily life?")
            follow_up_questions.append("What makes this better or worse?")
        
        return follow_up_questions

    def get_comprehensive_insights(
        self,
        module: Union[SCIDModule, SCIDPDModule],
        responses: Dict[str, Any]
    ) -> ComprehensiveInsights:
        """Generate comprehensive insights for the complete assessment"""
        
        # Get the latest analysis
        analysis = self.analyze_responses_real_time(module, responses, "comprehensive")
        
        # Generate diagnostic summary
        diagnostic_summary = self._generate_diagnostic_summary(analysis)
        
        # Identify key symptoms
        key_symptoms = self._identify_key_symptoms(analysis, responses)
        
        # Assess severity
        severity_assessment = self._assess_severity(analysis)
        
        # Assess functional impairment
        functional_impairment = self._assess_functional_impairment(analysis, responses)
        
        # Generate differential considerations
        differential_considerations = self._generate_differential_considerations(analysis, module)
        
        # Generate treatment implications
        treatment_implications = self._generate_treatment_implications(analysis)
        
        # Assess risk
        risk_assessment = self._assess_risk(analysis)
        
        # Identify follow-up priorities
        follow_up_priorities = self._identify_follow_up_priorities(analysis)
        
        # Generate clinical notes
        clinical_notes = self._generate_clinical_notes(analysis, responses)
        
        return ComprehensiveInsights(
            diagnostic_summary=diagnostic_summary,
            key_symptoms=key_symptoms,
            severity_assessment=severity_assessment,
            functional_impairment=functional_impairment,
            differential_considerations=differential_considerations,
            treatment_implications=treatment_implications,
            risk_assessment=risk_assessment,
            follow_up_priorities=follow_up_priorities,
            clinical_notes=clinical_notes
        )

    def _generate_diagnostic_summary(self, analysis: RealTimeAnalysis) -> str:
        """Generate diagnostic summary"""
        if analysis.diagnostic_likelihood >= 0.8:
            return f"High likelihood of {analysis.module_name} diagnosis ({analysis.diagnostic_likelihood:.1%})"
        elif analysis.diagnostic_likelihood >= 0.5:
            return f"Moderate likelihood of {analysis.module_name} diagnosis ({analysis.diagnostic_likelihood:.1%})"
        elif analysis.diagnostic_likelihood >= 0.2:
            return f"Low likelihood of {analysis.module_name} diagnosis ({analysis.diagnostic_likelihood:.1%})"
        else:
            return f"Unlikely to meet {analysis.module_name} criteria ({analysis.diagnostic_likelihood:.1%})"

    def _identify_key_symptoms(self, analysis: RealTimeAnalysis, responses: Dict[str, Any]) -> List[str]:
        """Identify key symptoms from the analysis"""
        key_symptoms = []
        
        # Get symptoms from met criteria
        for criteria in analysis.criteria_analysis:
            if criteria.status == CriteriaStatus.MET:
                key_symptoms.append(criteria.criterion_text)
        
        return key_symptoms[:5]  # Return top 5 symptoms

    def _assess_severity(self, analysis: RealTimeAnalysis) -> str:
        """Assess overall severity"""
        return f"{analysis.severity_estimate} severity based on symptom presentation and functional impact"

    def _assess_functional_impairment(self, analysis: RealTimeAnalysis, responses: Dict[str, Any]) -> str:
        """Assess functional impairment"""
        impairment_keywords = ["work", "relationships", "daily activities", "functioning"]
        impairment_count = 0
        
        for response in responses.values():
            response_str = str(response).lower()
            if any(keyword in response_str for keyword in impairment_keywords):
                impairment_count += 1
        
        if impairment_count >= 3:
            return "Significant functional impairment across multiple domains"
        elif impairment_count >= 1:
            return "Moderate functional impairment in some areas"
        else:
            return "Minimal functional impairment reported"

    def _generate_differential_considerations(self, analysis: RealTimeAnalysis, module: Union[SCIDModule, SCIDPDModule]) -> List[str]:
        """Generate differential diagnostic considerations"""
        differentials = []
        
        # Add common differentials based on module type
        if "depression" in analysis.module_name.lower():
            differentials.extend([
                "Bipolar Disorder",
                "Adjustment Disorder",
                "Grief/Bereavement",
                "Medical conditions (e.g., thyroid disorders)"
            ])
        elif "anxiety" in analysis.module_name.lower():
            differentials.extend([
                "Other anxiety disorders",
                "Depression",
                "Medical conditions (e.g., cardiac, respiratory)"
            ])
        elif "personality" in analysis.module_name.lower():
            differentials.extend([
                "Other personality disorders",
                "Mood disorders",
                "Trauma-related disorders"
            ])
        
        return differentials

    def _generate_treatment_implications(self, analysis: RealTimeAnalysis) -> List[str]:
        """Generate treatment implications"""
        implications = []
        
        if analysis.diagnostic_likelihood >= 0.8:
            implications.append("Consider evidence-based treatment for confirmed diagnosis")
            implications.append("Monitor for treatment response and side effects")
        elif analysis.diagnostic_likelihood >= 0.5:
            implications.append("Consider provisional diagnosis and treatment trial")
            implications.append("Continue assessment to clarify diagnosis")
        else:
            implications.append("Focus on symptom management and supportive care")
            implications.append("Consider alternative diagnostic possibilities")
        
        # Add risk-based implications
        if analysis.risk_factors:
            implications.append("Address safety concerns and risk factors")
        
        return implications

    def _assess_risk(self, analysis: RealTimeAnalysis) -> str:
        """Assess overall risk level"""
        if analysis.risk_factors:
            return f"Elevated risk due to: {', '.join(analysis.risk_factors)}"
        else:
            return "Low immediate risk identified"

    def _identify_follow_up_priorities(self, analysis: RealTimeAnalysis) -> List[str]:
        """Identify follow-up assessment priorities"""
        priorities = []
        
        # Prioritize ambiguous criteria
        for criteria in analysis.criteria_analysis:
            if criteria.status == CriteriaStatus.AMBIGUOUS:
                priorities.append(f"Clarify: {criteria.criterion_text}")
        
        # Prioritize high-severity ambiguities
        high_severity_ambiguities = [a for a in analysis.ambiguities if a.severity == "high"]
        for ambiguity in high_severity_ambiguities:
            priorities.append(f"High priority: {ambiguity.suggested_follow_up}")
        
        return priorities[:5]  # Return top 5 priorities

    def _generate_clinical_notes(self, analysis: RealTimeAnalysis, responses: Dict[str, Any]) -> str:
        """Generate clinical notes"""
        notes = []
        
        notes.append(f"Assessment progress: {analysis.overall_progress:.1f}% complete")
        notes.append(f"Diagnostic likelihood: {analysis.diagnostic_likelihood:.1%}")
        notes.append(f"Severity estimate: {analysis.severity_estimate}")
        
        if analysis.ambiguities:
            notes.append(f"Ambiguities detected: {len(analysis.ambiguities)} responses need clarification")
        
        if analysis.risk_factors:
            notes.append(f"Risk factors: {', '.join(analysis.risk_factors)}")
        
        if analysis.protective_factors:
            notes.append(f"Protective factors: {', '.join(analysis.protective_factors)}")
        
        return "; ".join(notes)

    def export_analysis_report(self, analysis: RealTimeAnalysis) -> str:
        """Export analysis as a formatted report"""
        report = []
        
        # Header
        report.append("=" * 80)
        report.append(f"DSM CRITERIA ANALYSIS REPORT")
        report.append(f"Module: {analysis.module_name}")
        report.append(f"Timestamp: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 80)
        
        # Progress Summary
        report.append("\n📊 PROGRESS SUMMARY")
        report.append(f"Overall Progress: {analysis.overall_progress:.1f}%")
        report.append(f"Diagnostic Likelihood: {analysis.diagnostic_likelihood:.1%}")
        report.append(f"Severity Estimate: {analysis.severity_estimate}")
        
        # Criteria Status
        report.append("\n🎯 CRITERIA STATUS")
        report.append(f"Criteria Met: {analysis.criteria_met}/{analysis.total_criteria}")
        report.append(f"Partially Met: {analysis.criteria_partially_met}")
        report.append(f"Not Met: {analysis.criteria_not_met}")
        report.append(f"Ambiguous: {analysis.criteria_ambiguous}")
        
        # Insights
        if analysis.insights:
            report.append("\n💡 INSIGHTS")
            for insight in analysis.insights:
                report.append(f"• {insight}")
        
        # Ambiguities
        if analysis.ambiguities:
            report.append("\n❓ AMBIGUITIES DETECTED")
            for ambiguity in analysis.ambiguities:
                report.append(f"• {ambiguity.question_text}")
                report.append(f"  Response: {ambiguity.response}")
                report.append(f"  Issue: {ambiguity.description}")
                report.append(f"  Follow-up: {ambiguity.suggested_follow_up}")
                report.append("")
        
        # Recommendations
        if analysis.recommendations:
            report.append("\n📋 RECOMMENDATIONS")
            for recommendation in analysis.recommendations:
                report.append(f"• {recommendation}")
        
        return "\n".join(report)

    def get_analysis_history(self) -> List[RealTimeAnalysis]:
        """Get the complete analysis history"""
        return self.analysis_history

    def clear_history(self):
        """Clear the analysis history"""
        self.analysis_history.clear()
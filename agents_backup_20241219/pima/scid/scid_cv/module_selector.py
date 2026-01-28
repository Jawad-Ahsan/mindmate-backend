# scid_cv/module_selector.py
"""
Intelligent SCID-CV Module Selection System
Analyzes patient data to recommend most relevant diagnostic modules
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math

from agents.pima.scid.scid_cv.base_types import SCIDModule, Severity
from agents.llm_client import LLMClient
from . import MODULE_REGISTRY

logger = logging.getLogger(__name__)

class RelevancyReason(Enum):
    """Types of relevancy matching"""
    SYMPTOM_MATCH = "symptom_match"
    DSM_CRITERIA_MATCH = "dsm_criteria_match"
    DEMOGRAPHIC_MATCH = "demographic_match"
    COMORBIDITY_RISK = "comorbidity_risk"
    SEVERITY_MATCH = "severity_match"
    TEMPORAL_MATCH = "temporal_match"
    PRESENTING_CONCERN_MATCH = "presenting_concern_match"
    CLINICAL_HISTORY_MATCH = "clinical_history_match"

@dataclass
class PatientData:
    """Structured patient information"""
    # Demographics
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    religion: Optional[str] = None
    
    # Clinical history
    previous_diagnoses: List[str] = field(default_factory=list)
    current_medications: List[str] = field(default_factory=list)
    family_history: List[str] = field(default_factory=list)
    
    # Presenting concerns
    presenting_concern: str = ""
    chief_complaint: str = ""
    
    # Symptoms data
    symptoms: Dict[str, Any] = field(default_factory=dict)  # symptom_name -> details
    severity_level: Optional[str] = None
    onset_time: Optional[str] = None
    frequency: Optional[str] = None
    triggers: List[str] = field(default_factory=list)
    
    # Additional context
    functional_impairment: Optional[str] = None
    stressors: List[str] = field(default_factory=list)
    support_system: Optional[str] = None

@dataclass
class ModuleRelevancy:
    """Relevancy scoring for a module"""
    module_id: str
    module_name: str
    relevancy_score: float  # 0-1 scale
    reasons: List[Tuple[RelevancyReason, float, str]] = field(default_factory=list)  # (reason_type, score, explanation)
    confidence: float = 0.0
    estimated_administration_time: int = 0
    priority_level: str = "medium"  # low, medium, high, urgent

class SCIDModuleSelector:
    """Intelligent selector for SCID-CV modules based on patient data"""
    
    def __init__(self, use_llm: bool = True, model: str = None):
        """
        Initialize the module selector
        
        Args:
            use_llm: Whether to use LLM for semantic analysis
            model: Specific model to use for LLM analysis
        """
        self.use_llm = use_llm
        self.llm_client = LLMClient(enable_cache=True) if use_llm else None
        
        # Load all available modules
        self.modules = {module_id: creator() for module_id, creator in MODULE_REGISTRY.items()}
        
        # Symptom-to-module mapping
        self.symptom_keywords = self._build_symptom_mapping()
        
        # Demographic risk factors
        self.demographic_risk_factors = self._build_demographic_mapping()
        
        # Comorbidity patterns
        self.comorbidity_patterns = self._build_comorbidity_patterns()
        
        # DSM criteria keywords
        self.dsm_keywords = self._extract_dsm_keywords()
    
    def _build_symptom_mapping(self) -> Dict[str, Dict[str, float]]:
        """Build symptom keyword mapping from modules"""
        mapping = {}
        
        for module_id, module in self.modules.items():
            module_keywords = {}
            
            # Extract keywords from questions
            for question in module.questions:
                # Extract from question text
                keywords = self._extract_keywords_from_text(question.simple_text)
                for keyword in keywords:
                    module_keywords[keyword] = module_keywords.get(keyword, 0) + 0.3
                
                # Extract from examples
                for example in question.examples:
                    keywords = self._extract_keywords_from_text(example)
                    for keyword in keywords:
                        module_keywords[keyword] = module_keywords.get(keyword, 0) + 0.5
                
                # Extract from help text
                if question.help_text:
                    keywords = self._extract_keywords_from_text(question.help_text)
                    for keyword in keywords:
                        module_keywords[keyword] = module_keywords.get(keyword, 0) + 0.2
                
                # Extract from symptom category
                if question.symptom_category:
                    category_keywords = question.symptom_category.replace("_", " ").split()
                    for keyword in category_keywords:
                        if len(keyword) > 2:
                            module_keywords[keyword.lower()] = module_keywords.get(keyword.lower(), 0) + 0.7
            
            mapping[module_id] = module_keywords
        
        return mapping
    
    def _extract_keywords_from_text(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text"""
        # Remove common words and focus on meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that',
            'these', 'those', 'you', 'your', 'they', 'their', 'we', 'our', 'i', 'my', 'me',
            'him', 'her', 'his', 'she', 'he', 'it', 'its'
        }
        
        # Extract words, clean them
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = {word for word in words if word not in stop_words}
        
        # Add phrases for better matching
        phrases = []
        words_list = list(keywords)
        for i in range(len(words_list) - 1):
            phrase = f"{words_list[i]} {words_list[i+1]}"
            phrases.append(phrase)
        
        keywords.update(phrases)
        return keywords
    
    def _build_demographic_mapping(self) -> Dict[str, Dict[str, float]]:
        """Build demographic risk factor mapping"""
        return {
            "MDD": {
                "age_18_25": 0.3, "age_26_45": 0.4, "age_46_65": 0.3,
                "female": 0.6, "male": 0.4,
                "recent_life_changes": 0.5
            },
            "BIPOLAR": {
                "age_18_30": 0.7, "age_31_45": 0.3,
                "family_history_bipolar": 0.8,
                "family_history_mood": 0.5
            },
            "GAD": {
                "age_30_50": 0.5, "female": 0.6,
                "chronic_stress": 0.7
            },
            "PANIC": {
                "age_20_40": 0.6, "female": 0.7,
                "family_history_anxiety": 0.5
            },
            "PTSD": {
                "trauma_history": 0.9,
                "military": 0.6,
                "first_responder": 0.6
            },
            "SOCIAL_ANXIETY": {
                "age_13_25": 0.6,
                "introversion": 0.4
            },
            "OCD": {
                "age_18_35": 0.5,
                "family_history_ocd": 0.7
            },
            "ADHD": {
                "age_6_18": 0.8, "age_18_30": 0.4,
                "male": 0.6, "female": 0.4,
                "family_history_adhd": 0.6
            },
            "EATING_DISORDERS": {
                "age_12_25": 0.7, "female": 0.9,
                "perfectionism": 0.5, "body_image": 0.8
            },
            "ALCOHOL_USE": {
                "age_18_30": 0.5, "male": 0.6,
                "family_history_substance": 0.6
            },
            "SUBSTANCE_USE": {
                "age_18_35": 0.6, "male": 0.6,
                "peer_influence": 0.4
            }
        }
    
    def _build_comorbidity_patterns(self) -> Dict[str, List[Tuple[str, float]]]:
        """Build comorbidity patterns between disorders"""
        return {
            "MDD": [
                ("GAD", 0.7), ("PANIC", 0.5), ("PTSD", 0.6),
                ("EATING_DISORDERS", 0.4), ("ALCOHOL_USE", 0.5)
            ],
            "GAD": [
                ("MDD", 0.7), ("PANIC", 0.8), ("SOCIAL_ANXIETY", 0.6),
                ("SPECIFIC_PHOBIA", 0.4)
            ],
            "PANIC": [
                ("AGORAPHOBIA", 0.9), ("GAD", 0.8), ("MDD", 0.5),
                ("SOCIAL_ANXIETY", 0.4)
            ],
            "BIPOLAR": [
                ("SUBSTANCE_USE", 0.6), ("ALCOHOL_USE", 0.5),
                ("EATING_DISORDERS", 0.3)
            ],
            "PTSD": [
                ("MDD", 0.6), ("SUBSTANCE_USE", 0.7), ("ALCOHOL_USE", 0.6),
                ("PANIC", 0.4)
            ],
            "ADHD": [
                ("SUBSTANCE_USE", 0.4), ("BIPOLAR", 0.3),
                ("GAD", 0.3)
            ],
            "EATING_DISORDERS": [
                ("MDD", 0.4), ("GAD", 0.5), ("OCD", 0.3),
                ("SUBSTANCE_USE", 0.3)
            ]
        }
    
    def _extract_dsm_keywords(self) -> Dict[str, Set[str]]:
        """Extract keywords from DSM criteria"""
        dsm_keywords = {}
        
        for module_id, module in self.modules.items():
            keywords = set()
            for criterion in module.dsm_criteria:
                criterion_keywords = self._extract_keywords_from_text(criterion)
                keywords.update(criterion_keywords)
            dsm_keywords[module_id] = keywords
        
        return dsm_keywords
    
    async def select_modules(
        self,
        patient_data: PatientData,
        max_modules: int = 5,
        min_relevancy_threshold: float = 0.3,
        prioritize_by_severity: bool = True
    ) -> List[ModuleRelevancy]:
        """
        Select most relevant modules for a patient
        
        Args:
            patient_data: Patient information
            max_modules: Maximum number of modules to return
            min_relevancy_threshold: Minimum relevancy score to include
            prioritize_by_severity: Whether to prioritize by severity
            
        Returns:
            List of ModuleRelevancy objects sorted by relevancy
        """
        logger.info(f"Selecting modules for patient with concern: {patient_data.presenting_concern[:100]}...")
        
        module_scores = []
        
        for module_id, module in self.modules.items():
            try:
                relevancy = await self._calculate_module_relevancy(module_id, module, patient_data)
                
                if relevancy.relevancy_score >= min_relevancy_threshold:
                    module_scores.append(relevancy)
            
            except Exception as e:
                logger.error(f"Error calculating relevancy for module {module_id}: {e}")
                continue
        
        # Sort by relevancy score
        module_scores.sort(key=lambda x: x.relevancy_score, reverse=True)
        
        # Apply severity prioritization
        if prioritize_by_severity and patient_data.severity_level:
            module_scores = self._apply_severity_prioritization(module_scores, patient_data.severity_level)
        
        # Limit results
        selected_modules = module_scores[:max_modules]
        
        logger.info(f"Selected {len(selected_modules)} modules with scores: {[(m.module_name, round(m.relevancy_score, 2)) for m in selected_modules]}")
        
        return selected_modules
    
    async def _calculate_module_relevancy(
        self,
        module_id: str,
        module: SCIDModule,
        patient_data: PatientData
    ) -> ModuleRelevancy:
        """Calculate relevancy score for a specific module"""
        relevancy = ModuleRelevancy(
            module_id=module_id,
            module_name=module.name,
            relevancy_score=0.0,
            estimated_administration_time=module.estimated_time_mins
        )
        
        total_score = 0.0
        total_weight = 0.0
        
        # 1. Symptom matching (weight: 0.3)
        symptom_score, symptom_reasons = self._score_symptom_match(module_id, patient_data)
        total_score += symptom_score * 0.3
        total_weight += 0.3
        relevancy.reasons.extend(symptom_reasons)
        
        # 2. DSM criteria matching (weight: 0.25)
        dsm_score, dsm_reasons = self._score_dsm_criteria_match(module_id, patient_data)
        total_score += dsm_score * 0.25
        total_weight += 0.25
        relevancy.reasons.extend(dsm_reasons)
        
        # 3. Presenting concern matching (weight: 0.2)
        concern_score, concern_reasons = await self._score_presenting_concern_match(module_id, module, patient_data)
        total_score += concern_score * 0.2
        total_weight += 0.2
        relevancy.reasons.extend(concern_reasons)
        
        # 4. Demographic matching (weight: 0.1)
        demo_score, demo_reasons = self._score_demographic_match(module_id, patient_data)
        total_score += demo_score * 0.1
        total_weight += 0.1
        relevancy.reasons.extend(demo_reasons)
        
        # 5. Comorbidity risk (weight: 0.1)
        comorbid_score, comorbid_reasons = self._score_comorbidity_risk(module_id, patient_data)
        total_score += comorbid_score * 0.1
        total_weight += 0.1
        relevancy.reasons.extend(comorbid_reasons)
        
        # 6. Temporal/severity matching (weight: 0.05)
        temporal_score, temporal_reasons = self._score_temporal_match(module_id, patient_data)
        total_score += temporal_score * 0.05
        total_weight += 0.05
        relevancy.reasons.extend(temporal_reasons)
        
        # Calculate final score
        relevancy.relevancy_score = total_score / total_weight if total_weight > 0 else 0.0
        relevancy.confidence = self._calculate_confidence(relevancy.reasons)
        relevancy.priority_level = self._determine_priority_level(relevancy.relevancy_score, patient_data)
        
        return relevancy
    
    def _score_symptom_match(self, module_id: str, patient_data: PatientData) -> Tuple[float, List[Tuple[RelevancyReason, float, str]]]:
        """Score symptom keyword matching"""
        if not patient_data.symptoms or module_id not in self.symptom_keywords:
            return 0.0, []
        
        module_keywords = self.symptom_keywords[module_id]
        patient_symptoms = patient_data.symptoms
        
        matches = []
        total_match_score = 0.0
        
        # Check each patient symptom against module keywords
        for symptom_name, symptom_details in patient_symptoms.items():
            symptom_text = f"{symptom_name} {str(symptom_details)}"
            symptom_keywords = self._extract_keywords_from_text(symptom_text)
            
            for keyword in symptom_keywords:
                if keyword in module_keywords:
                    weight = module_keywords[keyword]
                    severity_multiplier = self._get_severity_multiplier(symptom_details)
                    match_score = weight * severity_multiplier
                    total_match_score += match_score
                    matches.append((keyword, match_score))
        
        # Normalize score
        max_possible_score = sum(module_keywords.values())
        normalized_score = min(1.0, total_match_score / max_possible_score) if max_possible_score > 0 else 0.0
        
        # Create explanation
        reasons = []
        if matches:
            top_matches = sorted(matches, key=lambda x: x[1], reverse=True)[:3]
            explanation = f"Symptom keywords match: {', '.join([match[0] for match in top_matches])}"
            reasons.append((RelevancyReason.SYMPTOM_MATCH, normalized_score, explanation))
        
        return normalized_score, reasons
    
    def _score_dsm_criteria_match(self, module_id: str, patient_data: PatientData) -> Tuple[float, List[Tuple[RelevancyReason, float, str]]]:
        """Score DSM-5 criteria matching"""
        if module_id not in self.dsm_keywords:
            return 0.0, []
        
        dsm_keywords = self.dsm_keywords[module_id]
        
        # Extract keywords from all patient text
        all_patient_text = f"{patient_data.presenting_concern} {patient_data.chief_complaint} {' '.join(map(str, patient_data.symptoms.values()))}"
        patient_keywords = self._extract_keywords_from_text(all_patient_text)
        
        # Calculate overlap
        matching_keywords = dsm_keywords.intersection(patient_keywords)
        
        if not dsm_keywords:
            return 0.0, []
        
        overlap_score = len(matching_keywords) / len(dsm_keywords)
        
        reasons = []
        if matching_keywords:
            explanation = f"DSM criteria keywords match: {', '.join(list(matching_keywords)[:5])}"
            reasons.append((RelevancyReason.DSM_CRITERIA_MATCH, overlap_score, explanation))
        
        return overlap_score, reasons
    
    async def _score_presenting_concern_match(self, module_id: str, module: SCIDModule, patient_data: PatientData) -> Tuple[float, List[Tuple[RelevancyReason, float, str]]]:
        """Score presenting concern matching using LLM if available"""
        if not patient_data.presenting_concern:
            return 0.0, []
        
        reasons = []
        
        if self.use_llm and self.llm_client:
            try:
                # Use LLM for semantic analysis
                score = await self._llm_semantic_analysis(module_id, module, patient_data)
                if score > 0:
                    explanation = f"Semantic analysis indicates strong relevance to {module.name}"
                    reasons.append((RelevancyReason.PRESENTING_CONCERN_MATCH, score, explanation))
                return score, reasons
            except Exception as e:
                logger.warning(f"LLM analysis failed for {module_id}: {e}")
        
        # Fallback to keyword matching
        concern_keywords = self._extract_keywords_from_text(patient_data.presenting_concern)
        module_description_keywords = self._extract_keywords_from_text(module.description)
        
        if not module_description_keywords:
            return 0.0, []
        
        overlap = concern_keywords.intersection(module_description_keywords)
        score = len(overlap) / len(module_description_keywords) if module_description_keywords else 0.0
        
        if overlap:
            explanation = f"Presenting concern matches module focus: {', '.join(list(overlap)[:3])}"
            reasons.append((RelevancyReason.PRESENTING_CONCERN_MATCH, score, explanation))
        
        return score, reasons
    
    async def _llm_semantic_analysis(self, module_id: str, module: SCIDModule, patient_data: PatientData) -> float:
        """Use LLM for semantic similarity analysis"""
        prompt = f"""Analyze the relevance between the patient's presenting concern and the diagnostic module:

PATIENT PRESENTING CONCERN:
{patient_data.presenting_concern}

DIAGNOSTIC MODULE: {module.name}
DESCRIPTION: {module.description}
DSM-5 CRITERIA: {'; '.join(module.dsm_criteria[:3])}

PATIENT SYMPTOMS: {'; '.join([f"{k}: {v}" for k, v in list(patient_data.symptoms.items())[:5]])}

Rate the relevance on a scale of 0.0 to 1.0 where:
- 0.0-0.2: Not relevant or unrelated
- 0.3-0.5: Somewhat relevant, possible connection
- 0.6-0.8: Quite relevant, strong indication
- 0.9-1.0: Highly relevant, clear match

Consider:
1. Symptom alignment with diagnostic criteria
2. Severity and functional impact
3. Temporal patterns
4. Clinical presentation patterns

Respond with only a number between 0.0 and 1.0."""
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                max_tokens=50,
                temperature=0.1
            )
            
            # Extract score from response
            score_match = re.search(r'([0-1]\.?\d*)', response)
            if score_match:
                score = float(score_match.group(1))
                return min(1.0, max(0.0, score))
            
        except Exception as e:
            logger.error(f"LLM semantic analysis error: {e}")
        
        return 0.0
    
    def _score_demographic_match(self, module_id: str, patient_data: PatientData) -> Tuple[float, List[Tuple[RelevancyReason, float, str]]]:
        """Score demographic risk factor matching"""
        if module_id not in self.demographic_risk_factors:
            return 0.0, []
        
        risk_factors = self.demographic_risk_factors[module_id]
        matches = []
        
        # Age matching
        if patient_data.age:
            age_ranges = {
                "age_6_18": (6, 18), "age_13_25": (13, 25), "age_18_25": (18, 25),
                "age_18_30": (18, 30), "age_20_40": (20, 40), "age_26_45": (26, 45),
                "age_30_50": (30, 50), "age_31_45": (31, 45), "age_46_65": (46, 65)
            }
            
            for age_key, (min_age, max_age) in age_ranges.items():
                if age_key in risk_factors and min_age <= patient_data.age <= max_age:
                    matches.append((age_key, risk_factors[age_key]))
        
        # Gender matching
        if patient_data.gender:
            gender_key = patient_data.gender.lower()
            if gender_key in risk_factors:
                matches.append((gender_key, risk_factors[gender_key]))
        
        # Family history matching
        for diagnosis in patient_data.family_history:
            family_keys = [f"family_history_{key}" for key in ["mood", "anxiety", "bipolar", "adhd", "ocd", "substance"]]
            for key in family_keys:
                if key in risk_factors and key.split("_")[-1] in diagnosis.lower():
                    matches.append((key, risk_factors[key]))
        
        # Calculate total score
        total_score = sum(score for _, score in matches) / len(risk_factors) if risk_factors else 0.0
        normalized_score = min(1.0, total_score)
        
        reasons = []
        if matches:
            top_matches = sorted(matches, key=lambda x: x[1], reverse=True)[:2]
            explanation = f"Demographic risk factors: {', '.join([match[0].replace('_', ' ') for match in top_matches])}"
            reasons.append((RelevancyReason.DEMOGRAPHIC_MATCH, normalized_score, explanation))
        
        return normalized_score, reasons
    
    def _score_comorbidity_risk(self, module_id: str, patient_data: PatientData) -> Tuple[float, List[Tuple[RelevancyReason, float, str]]]:
        """Score based on comorbidity patterns"""
        if not patient_data.previous_diagnoses:
            return 0.0, []
        
        total_risk = 0.0
        comorbid_modules = []
        
        for diagnosis in patient_data.previous_diagnoses:
            # Find matching modules for previous diagnoses
            for pattern_module, comorbidities in self.comorbidity_patterns.items():
                if any(keyword in diagnosis.lower() for keyword in pattern_module.lower().split("_")):
                    for comorbid_module, risk in comorbidities:
                        if comorbid_module == module_id:
                            total_risk += risk
                            comorbid_modules.append((pattern_module, risk))
        
        reasons = []
        if comorbid_modules:
            explanation = f"Comorbidity risk from: {', '.join([module for module, _ in comorbid_modules])}"
            reasons.append((RelevancyReason.COMORBIDITY_RISK, total_risk, explanation))
        
        return min(1.0, total_risk), reasons
    
    def _score_temporal_match(self, module_id: str, patient_data: PatientData) -> Tuple[float, List[Tuple[RelevancyReason, float, str]]]:
        """Score based on temporal patterns and severity"""
        score = 0.0
        reasons = []
        
        # Onset time matching
        if patient_data.onset_time:
            onset_keywords = patient_data.onset_time.lower()
            if "sudden" in onset_keywords or "acute" in onset_keywords:
                if module_id in ["PANIC", "PTSD", "ADJUSTMENT"]:
                    score += 0.5
                    reasons.append((RelevancyReason.TEMPORAL_MATCH, 0.5, "Acute onset matches disorder pattern"))
            
            elif "gradual" in onset_keywords or "chronic" in onset_keywords:
                if module_id in ["MDD", "GAD", "SOCIAL_ANXIETY"]:
                    score += 0.5
                    reasons.append((RelevancyReason.TEMPORAL_MATCH, 0.5, "Gradual onset matches disorder pattern"))
        
        # Severity matching
        if patient_data.severity_level:
            severity_lower = patient_data.severity_level.lower()
            if "severe" in severity_lower and module_id in ["MDD", "BIPOLAR", "PTSD"]:
                score += 0.3
                reasons.append((RelevancyReason.SEVERITY_MATCH, 0.3, "High severity indicates serious mood/trauma disorder"))
        
        return min(1.0, score), reasons
    
    def _get_severity_multiplier(self, symptom_details: Any) -> float:
        """Get multiplier based on symptom severity"""
        if isinstance(symptom_details, dict) and "severity" in symptom_details:
            severity = str(symptom_details["severity"]).lower()
            if "severe" in severity:
                return 1.5
            elif "moderate" in severity:
                return 1.2
            elif "mild" in severity:
                return 1.0
        return 1.0
    
    def _calculate_confidence(self, reasons: List[Tuple[RelevancyReason, float, str]]) -> float:
        """Calculate confidence based on number and strength of reasons"""
        if not reasons:
            return 0.0
        
        # More reasons and higher scores = higher confidence
        avg_score = sum(score for _, score, _ in reasons) / len(reasons)
        reason_count_factor = min(1.0, len(reasons) / 5)  # Max at 5 reasons
        
        return (avg_score * 0.7) + (reason_count_factor * 0.3)
    
    def _determine_priority_level(self, relevancy_score: float, patient_data: PatientData) -> str:
        """Determine priority level for module administration"""
        # Check for urgent indicators
        urgent_indicators = ["suicidal", "self-harm", "psychosis", "mania", "severe", "crisis"]
        all_text = f"{patient_data.presenting_concern} {patient_data.chief_complaint}".lower()
        
        if any(indicator in all_text for indicator in urgent_indicators):
            return "urgent"
        
        if relevancy_score >= 0.8:
            return "high"
        elif relevancy_score >= 0.6:
            return "medium"
        else:
            return "low"
    
    def _apply_severity_prioritization(self, modules: List[ModuleRelevancy], severity_level: str) -> List[ModuleRelevancy]:
        """Apply severity-based prioritization"""
        if not severity_level:
            return modules
        
        severity_boost = {
            "mild": 0.05,
            "moderate": 0.1,
            "severe": 0.15,
            "extreme": 0.2
        }
        
        boost = severity_boost.get(severity_level.lower(), 0.0)
        
        for module in modules:
            if module.module_id in ["MDD", "BIPOLAR", "PTSD", "PANIC"]:  # High-impact disorders
                module.relevancy_score = min(1.0, module.relevancy_score + boost)
                module.reasons.append((
                    RelevancyReason.SEVERITY_MATCH, 
                    boost, 
                    f"Priority boost for {severity_level} severity and high-impact disorder"
                ))
        
        return sorted(modules, key=lambda x: x.relevancy_score, reverse=True)
    
    def generate_selection_report(self, selected_modules: List[ModuleRelevancy], patient_data: PatientData) -> str:
        """Generate human-readable selection report"""
        if not selected_modules:
            return "No relevant modules identified for this patient."
        
        report_lines = [
            "=" * 60,
            "SCID-CV MODULE SELECTION REPORT",
            "=" * 60,
            "",
            f"Patient Profile:",
            f"  • Age: {patient_data.age or 'Not specified'}",
            f"  • Gender: {patient_data.gender or 'Not specified'}",
            f"  • Presenting Concern: {patient_data.presenting_concern[:100]}{'...' if len(patient_data.presenting_concern) > 100 else ''}",
            f"  • Severity Level: {patient_data.severity_level or 'Not specified'}",
            f"  • Number of Symptoms: {len(patient_data.symptoms)}",
            "",
            f"RECOMMENDED MODULES ({len(selected_modules)} total):",
            "-" * 40
        ]
        
        total_estimated_time = sum(m.estimated_administration_time for m in selected_modules)
        
        for i, module in enumerate(selected_modules, 1):
            report_lines.extend([
                f"{i}. {module.module_name} [{module.priority_level.upper()}]",
                f"   Relevancy Score: {module.relevancy_score:.2f} (Confidence: {module.confidence:.2f})",
                f"   Estimated Time: {module.estimated_administration_time} minutes",
                ""
            ])
            
            # Add reasons
            if module.reasons:
                report_lines.append("   Reasons for Recommendation:")
                for reason_type, score, explanation in module.reasons[:3]:  # Top 3 reasons
                    reason_name = reason_type.value.replace("_", " ").title()
                    report_lines.append(f"   • {reason_name} ({score:.2f}): {explanation}")
                report_lines.append("")
        
        report_lines.extend([
            f"Total Estimated Administration Time: {total_estimated_time} minutes",
            "",
            "ADMINISTRATION RECOMMENDATIONS:",
            "-" * 30
        ])
        
        # Priority-based recommendations
        urgent_modules = [m for m in selected_modules if m.priority_level == "urgent"]
        high_modules = [m for m in selected_modules if m.priority_level == "high"]
        
        if urgent_modules:
            report_lines.append("URGENT - Administer immediately:")
            for module in urgent_modules:
                report_lines.append(f"  • {module.module_name}")
            report_lines.append("")
        
        if high_modules:
            report_lines.append("HIGH PRIORITY - Administer in first session:")
            for module in high_modules:
                report_lines.append(f"  • {module.module_name}")
            report_lines.append("")
        
        medium_modules = [m for m in selected_modules if m.priority_level == "medium"]
        if medium_modules:
            report_lines.append("MEDIUM PRIORITY - Consider for comprehensive assessment:")
            for module in medium_modules:
                report_lines.append(f"  • {module.module_name}")
        
        report_lines.extend([
            "",
            "=" * 60,
            f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60
        ])
        
        return "\n".join(report_lines)
    
    def get_module_by_id(self, module_id: str) -> Optional[SCIDModule]:
        """Get module instance by ID"""
        return self.modules.get(module_id)
    
    def get_selection_statistics(self, selected_modules: List[ModuleRelevancy]) -> Dict[str, Any]:
        """Get statistics about the selection"""
        if not selected_modules:
            return {}
        
        scores = [m.relevancy_score for m in selected_modules]
        priority_counts = {}
        for module in selected_modules:
            priority_counts[module.priority_level] = priority_counts.get(module.priority_level, 0) + 1
        
        return {
            "total_modules": len(selected_modules),
            "average_relevancy": sum(scores) / len(scores),
            "highest_relevancy": max(scores),
            "lowest_relevancy": min(scores),
            "priority_distribution": priority_counts,
            "total_estimated_time": sum(m.estimated_administration_time for m in selected_modules),
            "high_confidence_modules": len([m for m in selected_modules if m.confidence >= 0.7])
        }


# Usage example and utility functions
def create_patient_data_from_dict(data: Dict[str, Any]) -> PatientData:
    """Create PatientData from dictionary"""
    return PatientData(
        age=data.get("age"),
        gender=data.get("gender"),
        location=data.get("location"),
        religion=data.get("religion"),
        previous_diagnoses=data.get("previous_diagnoses", []),
        current_medications=data.get("current_medications", []),
        family_history=data.get("family_history", []),
        presenting_concern=data.get("presenting_concern", ""),
        chief_complaint=data.get("chief_complaint", ""),
        symptoms=data.get("symptoms", {}),
        severity_level=data.get("severity_level"),
        onset_time=data.get("onset_time"),
        frequency=data.get("frequency"),
        triggers=data.get("triggers", []),
        functional_impairment=data.get("functional_impairment"),
        stressors=data.get("stressors", []),
        support_system=data.get("support_system")
    )


async def select_modules_for_patient(
    patient_info: Dict[str, Any],
    max_modules: int = 5,
    use_llm: bool = True,
    model: str = None
) -> Tuple[List[ModuleRelevancy], str]:
    """
    Convenience function to select modules for a patient
    
    Args:
        patient_info: Dictionary with patient information
        max_modules: Maximum modules to return
        use_llm: Whether to use LLM for analysis
        model: LLM model to use
    
    Returns:
        Tuple of (selected_modules, selection_report)
    """
    # Create patient data object
    patient_data = create_patient_data_from_dict(patient_info)
    
    # Initialize selector 
    selector = SCIDModuleSelector(use_llm=use_llm)
    
    # Select modules
    selected_modules = await selector.select_modules(
        patient_data=patient_data,
        max_modules=max_modules,
        min_relevancy_threshold=0.2
    )
    
    # Generate report
    report = selector.generate_selection_report(selected_modules, patient_data)
    
    return selected_modules, report


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Example patient data
    example_patient = {
        "age": 28,
        "gender": "female",
        "presenting_concern": "I've been feeling very sad and hopeless for the past month. I can't sleep well, I've lost interest in things I used to enjoy, and I'm having trouble concentrating at work. Sometimes I feel like everything is my fault.",
        "symptoms": {
            "persistent_sadness": {"severity": "severe", "duration": "1 month"},
            "sleep_problems": {"severity": "moderate", "type": "insomnia"},
            "loss_of_interest": {"severity": "severe", "activities": "hobbies, socializing"},
            "concentration_problems": {"severity": "moderate", "impact": "work performance"},
            "guilt_feelings": {"severity": "moderate"}
        },
        "severity_level": "moderate",
        "onset_time": "gradual over past month",
        "functional_impairment": "significant impact on work and relationships",
        "previous_diagnoses": [],
        "family_history": ["depression in mother"]
    }
    
    async def main():
        try:
            selected_modules, report = await select_modules_for_patient(
                patient_info=example_patient,
                max_modules=3,
                use_llm=True
            )
            
            print("SELECTED MODULES:")
            for module in selected_modules:
                print(f"- {module.module_name}: {module.relevancy_score:.2f}")
            
            print("\n" + report)
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Run example
    asyncio.run(main())
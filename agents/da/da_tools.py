"""
DA Diagnosis Agent Tools
Specialized tools for the Diagnosis Agent ReAct system
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime
from dataclasses import dataclass, field

# Import DSM criteria bank
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pima.scid.dsm_criteria_bank import dsm_criteria_bank, DisorderCriteria, DSMCriterion

@dataclass
class DiagnosisResult:
    """Result from diagnosis analysis"""
    diagnosis: str = ""
    confidence: float = 0.0
    severity: str = ""
    reasoning: str = ""
    matched_criteria: List[str] = field(default_factory=list)
    missing_criteria: List[str] = field(default_factory=list)
    flagged_criteria: List[str] = field(default_factory=list)  # New field for flagged missing criteria

class DSMCriteriaChecker:
    """Tool for checking DSM-5 criteria against patient symptoms"""

    def __init__(self):
        self.criteria_bank = dsm_criteria_bank

    def check_criteria_match(self, symptoms: List[str], disorder_id: str) -> DiagnosisResult:
        """
        Check if patient symptoms match DSM criteria for a specific disorder

        Args:
            symptoms: List of patient symptoms
            disorder_id: DSM disorder ID (e.g., 'MDD', 'GAD', 'PANIC')

        Returns:
            DiagnosisResult with match analysis
        """
        disorder = self.criteria_bank.get_disorder_criteria(disorder_id)
        if not disorder:
            return DiagnosisResult(
                diagnosis=f"Unknown disorder: {disorder_id}",
                confidence=0.0,
                severity="unknown",
                reasoning=f"Disorder ID '{disorder_id}' not found in DSM criteria bank"
            )

        # Normalize symptoms for matching
        normalized_symptoms = [s.lower().strip() for s in symptoms]

        matched_criteria = []
        missing_criteria = []

        # Check each criterion
        for criterion in disorder.criteria:
            criterion_text = criterion.text.lower()

            # Check if any symptom matches this criterion
            matches = any(
                self._symptom_matches_criterion(symptom, criterion_text)
                for symptom in normalized_symptoms
            )

            if matches:
                matched_criteria.append(criterion.criterion_id)
            else:
                missing_criteria.append(criterion.criterion_id)

        # Calculate match percentage
        total_criteria = len(disorder.criteria)
        matched_count = len(matched_criteria)
        match_percentage = matched_count / total_criteria if total_criteria > 0 else 0

        # Determine if criteria threshold is met
        meets_threshold = matched_count >= disorder.minimum_criteria_count

        # Calculate confidence and severity
        confidence = self._calculate_confidence(match_percentage, meets_threshold)
        severity = self._determine_severity(matched_count, disorder)

        # Build reasoning
        reasoning = self._build_reasoning(
            disorder, matched_criteria, missing_criteria,
            match_percentage, meets_threshold
        )

        return DiagnosisResult(
            diagnosis=disorder.disorder_name if meets_threshold else f"Subthreshold {disorder.disorder_name}",
            confidence=confidence,
            severity=severity,
            reasoning=reasoning,
            matched_criteria=matched_criteria,
            missing_criteria=missing_criteria
        )

    def _symptom_matches_criterion(self, symptom: str, criterion_text: str) -> bool:
        """Check if a symptom matches a criterion using keyword matching"""
        symptom_words = set(symptom.lower().split())
        criterion_words = set(criterion_text.lower().split())

        # Direct word overlap
        overlap = symptom_words.intersection(criterion_words)

        # Partial word matching (e.g., "depressed" matches "depression")
        partial_matches = 0
        for symptom_word in symptom_words:
            for criterion_word in criterion_words:
                if symptom_word in criterion_word or criterion_word in symptom_word:
                    if len(symptom_word) > 3 and len(criterion_word) > 3:  # Avoid short words
                        partial_matches += 1

        # Consider it a match if there's significant overlap
        return len(overlap) > 0 or partial_matches > 0

    def _calculate_confidence(self, match_percentage: float, meets_threshold: bool) -> float:
        """Calculate confidence score based on match percentage and threshold"""
        if not meets_threshold:
            return match_percentage * 0.7  # Reduce confidence if below threshold

        # Boost confidence based on match percentage
        if match_percentage >= 0.8:
            return 0.9 + (match_percentage - 0.8) * 0.5
        elif match_percentage >= 0.6:
            return 0.7 + (match_percentage - 0.6) * 0.5
        else:
            return match_percentage * 0.8

    def _determine_severity(self, matched_count: int, disorder: DisorderCriteria) -> str:
        """Determine severity level based on matched criteria count"""
        severity_levels = disorder.severity_levels

        if "severe" in severity_levels and matched_count >= disorder.minimum_criteria_count + 4:
            return "severe"
        elif "moderate" in severity_levels and matched_count >= disorder.minimum_criteria_count + 2:
            return "moderate"
        elif "mild" in severity_levels:
            return "mild"
        else:
            return "unknown"

    def _build_reasoning(self, disorder: DisorderCriteria, matched: List[str],
                        missing: List[str], match_pct: float, meets_threshold: bool) -> str:
        """Build detailed reasoning for the diagnosis"""
        reasoning_parts = []

        if meets_threshold:
            reasoning_parts.append(f"Patient meets DSM-5 criteria for {disorder.disorder_name}.")
        else:
            reasoning_parts.append(f"Patient shows symptoms of {disorder.disorder_name} but does not meet full criteria.")

        reasoning_parts.append(f"Matched {len(matched)} out of {len(disorder.criteria)} criteria ({match_pct:.1%} match rate).")
        reasoning_parts.append(f"Minimum required criteria: {disorder.minimum_criteria_count}.")

        if matched:
            reasoning_parts.append(f"Matched criteria: {', '.join(matched)}.")

        if missing and len(missing) <= 5:  # Don't list too many missing criteria
            reasoning_parts.append(f"Missing criteria: {', '.join(missing)}.")

        if disorder.duration_requirement:
            reasoning_parts.append(f"Duration requirement: {disorder.duration_requirement}.")

        if disorder.clinical_notes:
            reasoning_parts.append(f"Clinical notes: {disorder.clinical_notes}.")

        return " ".join(reasoning_parts)

class SymptomAnalyzer:
    """Tool for analyzing and categorizing patient symptoms"""

    def __init__(self):
        self.criteria_bank = dsm_criteria_bank

    def analyze_symptoms(self, symptoms: List[str]) -> Dict[str, Any]:
        """
        Analyze patient symptoms and suggest potential disorders

        Args:
            symptoms: List of patient symptoms

        Returns:
            Analysis results with potential disorders and scores
        """
        potential_disorders = {}
        symptom_categories = self._categorize_symptoms(symptoms)

        # Check each disorder in the criteria bank
        for disorder_id, disorder in self.criteria_bank.get_all_disorders().items():
            checker = DSMCriteriaChecker()
            result = checker.check_criteria_match(symptoms, disorder_id)

            if result.confidence > 0.3:  # Only include disorders with some confidence
                potential_disorders[disorder_id] = {
                    "disorder_name": disorder.disorder_name,
                    "confidence": result.confidence,
                    "severity": result.severity,
                    "matched_criteria": result.matched_criteria,
                    "category": disorder.category.value
                }

        # Sort by confidence
        sorted_disorders = dict(sorted(
            potential_disorders.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        ))

        return {
            "symptom_count": len(symptoms),
            "symptom_categories": symptom_categories,
            "potential_disorders": sorted_disorders,
            "top_diagnosis": list(sorted_disorders.keys())[0] if sorted_disorders else None
        }

    def _categorize_symptoms(self, symptoms: List[str]) -> Dict[str, List[str]]:
        """Categorize symptoms by type"""
        categories = {
            "mood": [],
            "anxiety": [],
            "cognitive": [],
            "physical": [],
            "behavioral": [],
            "other": []
        }

        mood_keywords = ["depressed", "sad", "happy", "irritable", "mood", "emotion"]
        anxiety_keywords = ["anxious", "worried", "fear", "panic", "nervous", "tense"]
        cognitive_keywords = ["concentration", "memory", "thinking", "focus", "attention"]
        physical_keywords = ["sleep", "appetite", "energy", "fatigue", "pain", "headache"]
        behavioral_keywords = ["avoid", "withdraw", "social", "work", "activity"]

        for symptom in symptoms:
            symptom_lower = symptom.lower()

            if any(keyword in symptom_lower for keyword in mood_keywords):
                categories["mood"].append(symptom)
            elif any(keyword in symptom_lower for keyword in anxiety_keywords):
                categories["anxiety"].append(symptom)
            elif any(keyword in symptom_lower for keyword in cognitive_keywords):
                categories["cognitive"].append(symptom)
            elif any(keyword in symptom_lower for keyword in physical_keywords):
                categories["physical"].append(symptom)
            elif any(keyword in symptom_lower for keyword in behavioral_keywords):
                categories["behavioral"].append(symptom)
            else:
                categories["other"].append(symptom)

        return categories

class ConfidenceCalculator:
    """Tool for calculating diagnostic confidence and severity"""

    def __init__(self):
        self.criteria_bank = dsm_criteria_bank

    def calculate_overall_confidence(self, symptom_analysis: Dict[str, Any],
                                   primary_diagnosis: str) -> Dict[str, Any]:
        """
        Calculate overall diagnostic confidence considering multiple factors

        Args:
            symptom_analysis: Results from symptom analysis
            primary_diagnosis: The primary disorder being considered

        Returns:
            Confidence analysis with detailed breakdown
        """
        if not symptom_analysis.get("potential_disorders"):
            return {
                "overall_confidence": 0.0,
                "severity": "unknown",
                "confidence_factors": {},
                "recommendations": ["Insufficient symptoms for confident diagnosis"]
            }

        primary_disorder_data = symptom_analysis["potential_disorders"].get(primary_diagnosis, {})
        if not primary_disorder_data:
            return {
                "overall_confidence": 0.0,
                "severity": "unknown",
                "confidence_factors": {},
                "recommendations": ["Primary diagnosis not found in analysis"]
            }

        # Calculate various confidence factors
        confidence_factors = {}

        # Base confidence from criteria matching
        base_confidence = primary_disorder_data.get("confidence", 0.0)
        confidence_factors["criteria_match"] = base_confidence

        # Symptom consistency factor
        symptom_categories = symptom_analysis.get("symptom_categories", {})
        consistency_score = self._calculate_symptom_consistency(symptom_categories)
        confidence_factors["symptom_consistency"] = consistency_score

        # Disorder specificity factor
        specificity_score = self._calculate_disorder_specificity(
            primary_diagnosis,
            symptom_analysis["potential_disorders"]
        )
        confidence_factors["disorder_specificity"] = specificity_score

        # Symptom count factor
        symptom_count = symptom_analysis.get("symptom_count", 0)
        count_factor = min(symptom_count / 10, 1.0)  # Max at 10 symptoms
        confidence_factors["symptom_count"] = count_factor

        # Calculate weighted overall confidence
        weights = {
            "criteria_match": 0.4,
            "symptom_consistency": 0.2,
            "disorder_specificity": 0.2,
            "symptom_count": 0.2
        }

        overall_confidence = sum(
            confidence_factors[factor] * weights[factor]
            for factor in confidence_factors
        )

        # Determine severity with confidence adjustment
        severity = primary_disorder_data.get("severity", "unknown")
        if overall_confidence < 0.5:
            severity = "uncertain"

        # Generate recommendations
        recommendations = self._generate_recommendations(
            overall_confidence, confidence_factors, symptom_analysis
        )

        return {
            "overall_confidence": overall_confidence,
            "severity": severity,
            "confidence_factors": confidence_factors,
            "recommendations": recommendations,
            "primary_diagnosis": primary_diagnosis
        }

    def _calculate_symptom_consistency(self, symptom_categories: Dict[str, List[str]]) -> float:
        """Calculate how consistent symptoms are within categories"""
        total_symptoms = sum(len(symptoms) for symptoms in symptom_categories.values())

        if total_symptoms == 0:
            return 0.0

        # Calculate entropy-like measure of symptom distribution
        category_counts = [len(symptoms) for symptoms in symptom_categories.values()]
        category_probs = [count / total_symptoms for count in category_counts if count > 0]

        # Lower entropy (more focused symptoms) = higher consistency
        if len(category_probs) <= 1:
            return 1.0

        entropy = -sum(p * (p ** 0.5) for p in category_probs)  # Simplified entropy
        consistency = 1.0 - (entropy / len(category_probs))

        return max(0.0, min(1.0, consistency))

    def _calculate_disorder_specificity(self, primary_diagnosis: str,
                                      potential_disorders: Dict[str, Any]) -> float:
        """Calculate how specific the diagnosis is compared to alternatives"""
        if len(potential_disorders) <= 1:
            return 1.0

        primary_confidence = potential_disorders[primary_diagnosis].get("confidence", 0.0)

        # Calculate average confidence of alternative diagnoses
        alt_confidences = [
            data.get("confidence", 0.0)
            for disorder_id, data in potential_disorders.items()
            if disorder_id != primary_diagnosis
        ]

        if not alt_confidences:
            return 1.0

        avg_alt_confidence = sum(alt_confidences) / len(alt_confidences)

        # Specificity is higher when primary confidence is much higher than alternatives
        specificity = primary_confidence - avg_alt_confidence

        return max(0.0, min(1.0, specificity + 0.5))  # Shift to make it more balanced

    def _generate_recommendations(self, confidence: float,
                                confidence_factors: Dict[str, float],
                                symptom_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on confidence analysis"""
        recommendations = []

        if confidence >= 0.8:
            recommendations.append("High confidence diagnosis - proceed with treatment planning")
        elif confidence >= 0.6:
            recommendations.append("Moderate confidence - consider additional assessment")
        else:
            recommendations.append("Low confidence - recommend comprehensive evaluation")

        # Check specific factors
        if confidence_factors.get("criteria_match", 0.0) < 0.5:
            recommendations.append("Consider differential diagnosis - criteria match is low")

        if confidence_factors.get("symptom_consistency", 0.0) < 0.5:
            recommendations.append("Symptoms appear inconsistent - review patient history")

        if confidence_factors.get("symptom_count", 0.0) < 0.5:
            recommendations.append("Limited symptoms reported - gather more information")

        return recommendations


class DifferentialDiagnosisTool:
    """Tool for performing differential diagnosis between multiple disorders"""

    def __init__(self):
        self.criteria_bank = dsm_criteria_bank

    def perform_differential_diagnosis(self, symptoms: List[str],
                                     candidate_disorders: List[str]) -> Dict[str, Any]:
        """
        Perform differential diagnosis by comparing multiple disorders

        Args:
            symptoms: List of patient symptoms
            candidate_disorders: List of disorder IDs to compare

        Returns:
            Differential diagnosis analysis
        """
        if not candidate_disorders:
            return {"error": "No candidate disorders provided"}

        disorder_comparisons = {}

        for disorder_id in candidate_disorders:
            checker = DSMCriteriaChecker()
            result = checker.check_criteria_match(symptoms, disorder_id)

            disorder_comparisons[disorder_id] = {
                "disorder_name": result.diagnosis,
                "confidence": result.confidence,
                "severity": result.severity,
                "matched_count": len(result.matched_criteria),
                "missing_count": len(result.missing_criteria),
                "matched_criteria": result.matched_criteria,
                "missing_criteria": result.missing_criteria
            }

        # Sort by confidence (highest first)
        sorted_disorders = dict(sorted(
            disorder_comparisons.items(),
            key=lambda x: x[1]["confidence"],
            reverse=True
        ))

        # Calculate differential factors
        top_disorder = list(sorted_disorders.keys())[0]
        top_confidence = sorted_disorders[top_disorder]["confidence"]

        differential_factors = {}
        if len(sorted_disorders) > 1:
            second_disorder = list(sorted_disorders.keys())[1]
            confidence_diff = top_confidence - sorted_disorders[second_disorder]["confidence"]
            differential_factors = {
                "top_diagnosis": top_disorder,
                "confidence_difference": confidence_diff,
                "second_candidate": second_disorder,
                "recommendation": "Strong differential" if confidence_diff > 0.2 else "Close differential - consider additional assessment"
            }

        return {
            "differential_analysis": sorted_disorders,
            "top_diagnosis": top_disorder,
            "differential_factors": differential_factors,
            "total_candidates": len(candidate_disorders)
        }

class ClinicalReasoningTool:
    """Tool for advanced clinical reasoning and criteria flagging"""

    def __init__(self):
        self.criteria_bank = dsm_criteria_bank

    def perform_clinical_reasoning(self, symptoms: List[str], primary_diagnosis: str,
                                 dsm_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform advanced clinical reasoning and flag critical missing criteria

        Args:
            symptoms: Patient symptoms
            primary_diagnosis: Primary diagnosis ID
            dsm_result: DSM criteria check result

        Returns:
            Clinical reasoning analysis with flagged criteria
        """
        disorder = self.criteria_bank.get_disorder_criteria(primary_diagnosis)
        if not disorder:
            return {"error": f"Disorder {primary_diagnosis} not found"}

        # Categorize missing criteria by importance
        critical_missing = []
        important_missing = []
        optional_missing = []

        for criterion_id in dsm_result.get('missing_criteria', []):
            criterion = self._get_criterion_by_id(disorder, criterion_id)
            if criterion:
                # Flag critical criteria (required for diagnosis)
                if criterion.required:
                    critical_missing.append(criterion.text)
                else:
                    optional_missing.append(criterion.text)

        # Build detailed reasoning
        matched_descriptions = []
        for criterion_id in dsm_result.get('matched_criteria', []):
            criterion = self._get_criterion_by_id(disorder, criterion_id)
            if criterion:
                matched_descriptions.append(criterion.text)

        reasoning_parts = []

        if matched_descriptions:
            reasoning_parts.append(f"Patient meets criteria for {disorder.disorder_name} because:")
            for desc in matched_descriptions[:3]:  # Limit to top 3
                reasoning_parts.append(f"  • {desc}")
            if len(matched_descriptions) > 3:
                reasoning_parts.append(f"  • And {len(matched_descriptions) - 3} additional criteria")

        if critical_missing:
            reasoning_parts.append(f"\nHowever, the following critical criteria are missing:")
            for crit in critical_missing[:3]:  # Limit to top 3
                reasoning_parts.append(f"  ⚠️  {crit}")

        # Calculate clinical significance
        meets_threshold = len(dsm_result.get('matched_criteria', [])) >= disorder.minimum_criteria_count

        clinical_assessment = {
            "diagnosis": disorder.disorder_name,
            "meets_criteria": meets_threshold,
            "matched_criteria_count": len(dsm_result.get('matched_criteria', [])),
            "missing_criteria_count": len(dsm_result.get('missing_criteria', [])),
            "critical_missing_count": len(critical_missing),
            "important_missing_count": len(important_missing),
            "optional_missing_count": len(optional_missing),
            "clinical_reasoning": "\n".join(reasoning_parts),
            "flagged_criteria": critical_missing + important_missing,
            "recommendations": self._generate_clinical_recommendations(
                meets_threshold, critical_missing, disorder
            )
        }

        return clinical_assessment

    def _get_criterion_by_id(self, disorder: DisorderCriteria, criterion_id: str) -> Optional[DSMCriterion]:
        """Get criterion object by ID"""
        for criterion in disorder.criteria:
            if criterion.criterion_id == criterion_id:
                return criterion
        return None

    def _generate_clinical_recommendations(self, meets_threshold: bool,
                                         critical_missing: List[str],
                                         disorder: DisorderCriteria) -> List[str]:
        """Generate clinical recommendations based on analysis"""
        recommendations = []

        if not meets_threshold:
            recommendations.append("Does not meet minimum criteria for full diagnosis")
            if critical_missing:
                recommendations.append("Consider differential diagnosis or subthreshold condition")

        if critical_missing:
            recommendations.append("Additional assessment recommended for missing critical criteria")
            recommendations.append(f"Duration requirement: {disorder.duration_requirement}")

        if disorder.clinical_notes:
            recommendations.append(f"Clinical consideration: {disorder.clinical_notes}")

        return recommendations


# Global instances for easy access
dsm_checker = DSMCriteriaChecker()
symptom_analyzer = SymptomAnalyzer()
confidence_calculator = ConfidenceCalculator()
differential_diagnosis_tool = DifferentialDiagnosisTool()
clinical_reasoning_tool = ClinicalReasoningTool()

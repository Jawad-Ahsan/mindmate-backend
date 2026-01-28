from typing import List, Dict, Any, Optional
from .tpa_schemas import (
    TreatmentPlan, 
    Intervention, 
    SymptomSeverity, 
    TPAInput,
    PatientPreferences
)
from .treatment_guidelines import TreatmentGuidelines
import logging

logger = logging.getLogger(__name__)

class TreatmentPlanValidator:
    """
    Validates treatment plans for safety, appropriateness, and best practices.
    Ensures plans meet clinical standards and patient safety requirements.
    """
    
    def __init__(self):
        self.guidelines = TreatmentGuidelines()
        self.safety_red_flags = self._initialize_safety_red_flags()
        self.contraindication_patterns = self._initialize_contraindication_patterns()
    
    def _initialize_safety_red_flags(self) -> List[str]:
        """Initialize list of safety red flags that require immediate attention"""
        return [
            "suicidal ideation", "suicidal thoughts", "suicide plan", "suicide attempt",
            "homicidal ideation", "homicidal thoughts", "homicide plan", "homicide attempt",
            "active psychosis", "delusions", "hallucinations", "paranoia",
            "mania", "hypomania", "severe dissociation", "severe self-harm",
            "severe substance abuse", "severe eating disorder", "severe personality disorder",
            "severe trauma", "severe anxiety", "severe depression", "severe ocd",
            "severe ptsd", "severe adhd", "severe bipolar", "severe schizophrenia"
        ]
    
    def _initialize_contraindication_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns that indicate contraindications"""
        return {
            "cbt_exposure": ["severe depression", "suicidal ideation", "unstable medical conditions"],
            "journaling": ["severe dissociation", "trauma triggers", "overwhelming emotions"],
            "mindfulness": ["active psychosis", "severe dissociation", "severe trauma"],
            "dbt_skills": ["severe cognitive impairment", "active substance abuse"],
            "exercise": ["unstable medical conditions", "severe physical limitations"]
        }
    
    def validate_treatment_plan(
        self, 
        treatment_plan: TreatmentPlan, 
        tpa_input: TPAInput
    ) -> Dict[str, Any]:
        """Comprehensive validation of treatment plan"""
        validation_result = {
            "is_valid": True,
            "safety_score": 1.0,
            "appropriateness_score": 1.0,
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "requires_human_review": False,
            "review_reasons": []
        }
        
        try:
            # Safety validation
            safety_validation = self._validate_safety(treatment_plan, tpa_input)
            validation_result.update(safety_validation)
            
            # Appropriateness validation
            appropriateness_validation = self._validate_appropriateness(treatment_plan, tpa_input)
            validation_result.update(appropriateness_validation)
            
            # Clinical validation
            clinical_validation = self._validate_clinical_standards(treatment_plan, tpa_input)
            validation_result.update(clinical_validation)
            
            # Patient preference validation
            preference_validation = self._validate_patient_preferences(treatment_plan, tpa_input)
            validation_result.update(preference_validation)
            
            # Determine if human review is required
            validation_result["requires_human_review"] = self._determine_human_review_needed(validation_result)
            
            # Overall validation result
            validation_result["is_valid"] = (
                validation_result["safety_score"] >= 0.7 and
                validation_result["appropriateness_score"] >= 0.7 and
                len(validation_result["errors"]) == 0
            )
            
        except Exception as e:
            logger.error(f"Error during treatment plan validation: {e}")
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["is_valid"] = False
            validation_result["requires_human_review"] = True
        
        return validation_result
    
    def _validate_safety(self, treatment_plan: TreatmentPlan, tpa_input: TPAInput) -> Dict[str, Any]:
        """Validate safety aspects of the treatment plan"""
        safety_result = {
            "safety_score": 1.0,
            "safety_warnings": [],
            "safety_errors": []
        }
        
        # Check for red flags in input data
        red_flags_found = []
        for red_flag in tpa_input.red_flags:
            if any(flag.lower() in red_flag.lower() for flag in self.safety_red_flags):
                red_flags_found.append(red_flag)
        
        if red_flags_found:
            safety_result["safety_score"] = 0.3
            safety_result["safety_errors"].append(f"Safety red flags detected: {', '.join(red_flags_found)}")
        
        # Check for contraindications in interventions
        contraindications_found = []
        for intervention in [treatment_plan.primary_approach] + treatment_plan.complementary_strategies:
            contraindications = self._check_intervention_contraindications(intervention, tpa_input)
            if contraindications:
                contraindications_found.extend(contraindications)
        
        if contraindications_found:
            safety_result["safety_score"] = max(0.5, safety_result["safety_score"])
            safety_result["safety_warnings"].append(f"Contraindications found: {', '.join(contraindications_found)}")
        
        return safety_result
    
    def _validate_appropriateness(self, treatment_plan: TreatmentPlan, tpa_input: TPAInput) -> Dict[str, Any]:
        """Validate appropriateness of interventions for the patient's condition"""
        appropriateness_result = {
            "appropriateness_score": 1.0,
            "appropriateness_warnings": [],
            "appropriateness_errors": []
        }
        
        # Check if interventions match symptom clusters
        symptom_clusters = [cluster.name.lower() for cluster in tpa_input.symptom_clusters]
        recommended_interventions = self.guidelines.get_interventions_for_symptoms(
            symptom_clusters, 
            tpa_input.provisional_diagnosis.severity
        )
        
        # Check primary approach appropriateness
        primary_appropriate = any(
            intervention.name.lower() in [rec.name.lower() for rec in recommended_interventions]
            for intervention in [treatment_plan.primary_approach]
        )
        
        if not primary_appropriate:
            appropriateness_result["appropriateness_score"] = 0.6
            appropriateness_result["appropriateness_warnings"].append(
                "Primary intervention may not be optimal for identified symptoms"
            )
        
        return appropriateness_result
    
    def _validate_clinical_standards(self, treatment_plan: TreatmentPlan, tpa_input: TPAInput) -> Dict[str, Any]:
        """Validate clinical standards and best practices"""
        clinical_result = {
            "clinical_warnings": [],
            "clinical_errors": []
        }
        
        # Check for evidence-based interventions
        evidence_based_count = 0
        total_interventions = 1 + len(treatment_plan.complementary_strategies)
        
        for intervention in [treatment_plan.primary_approach] + treatment_plan.complementary_strategies:
            if "strong evidence" in intervention.evidence_level.lower() or "moderate evidence" in intervention.evidence_level.lower():
                evidence_based_count += 1
        
        evidence_ratio = evidence_based_count / total_interventions
        if evidence_ratio < 0.7:
            clinical_result["clinical_warnings"].append(
                f"Only {evidence_ratio:.1%} of interventions have strong/moderate evidence base"
            )
        
        return clinical_result
    
    def _validate_patient_preferences(self, treatment_plan: TreatmentPlan, tpa_input: TPAInput) -> Dict[str, Any]:
        """Validate alignment with patient preferences"""
        preference_result = {
            "preference_warnings": [],
            "preference_errors": []
        }
        
        preferences = tpa_input.patient_preferences
        
        # Check time commitment alignment
        total_weekly_time = self._estimate_weekly_time_commitment(treatment_plan)
        if total_weekly_time > preferences.weekly_time_commitment:
            preference_result["preference_warnings"].append(
                f"Treatment plan requires {total_weekly_time}h/week, but patient can only commit {preferences.weekly_time_commitment}h/week"
            )
        
        return preference_result
    
    def _check_intervention_contraindications(self, intervention: Intervention, tpa_input: TPAInput) -> List[str]:
        """Check if intervention has contraindications for this patient"""
        contraindications = []
        
        # Check intervention-specific contraindications
        intervention_name = intervention.name.lower()
        for pattern, contraindication_list in self.contraindication_patterns.items():
            if pattern in intervention_name:
                for contraindication in contraindication_list:
                    if self._check_contraindication_present(contraindication, tpa_input):
                        contraindications.append(f"{intervention.name}: {contraindication}")
        
        return contraindications
    
    def _check_contraindication_present(self, contraindication: str, tpa_input: TPAInput) -> bool:
        """Check if a specific contraindication is present in the patient data"""
        contraindication_lower = contraindication.lower()
        
        # Check diagnosis
        if contraindication_lower in tpa_input.provisional_diagnosis.primary_diagnosis.lower():
            return True
        
        # Check symptom clusters
        for cluster in tpa_input.symptom_clusters:
            if contraindication_lower in cluster.name.lower():
                return True
        
        # Check red flags
        for red_flag in tpa_input.red_flags:
            if contraindication_lower in red_flag.lower():
                return True
        
        return False
    
    def _estimate_weekly_time_commitment(self, treatment_plan: TreatmentPlan) -> int:
        """Estimate weekly time commitment for the treatment plan"""
        total_time = 0
        
        # Primary approach time
        primary_time = self._extract_time_from_frequency(treatment_plan.primary_approach.frequency)
        total_time += primary_time
        
        # Complementary strategies time
        for strategy in treatment_plan.complementary_strategies:
            strategy_time = self._extract_time_from_frequency(strategy.frequency)
            total_time += strategy_time
        
        # Self-help resources time (estimate)
        total_time += len(treatment_plan.self_help_resources) * 2  # 2 hours per resource per week
        
        return total_time
    
    def _extract_time_from_frequency(self, frequency: str) -> int:
        """Extract weekly time commitment from frequency description"""
        frequency_lower = frequency.lower()
        
        if "daily" in frequency_lower:
            if "10-20 minute" in frequency_lower:
                return 2  # 15 minutes average daily = ~2 hours/week
            else:
                return 3  # Default daily estimate
        elif "weekly" in frequency_lower:
            return 2  # Weekly session estimate
        elif "bi-weekly" in frequency_lower:
            return 1  # Bi-weekly estimate
        else:
            return 1  # Default estimate
    
    def _determine_human_review_needed(self, validation_result: Dict[str, Any]) -> bool:
        """Determine if human specialist review is required"""
        # Safety concerns require review
        if validation_result["safety_score"] < 0.7:
            return True
        
        # Multiple errors require review
        if len(validation_result["errors"]) > 2:
            return True
        
        # Severe appropriateness issues require review
        if validation_result["appropriateness_score"] < 0.6:
            return True
        
        return False
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary"""
        summary = []
        
        if validation_result["is_valid"]:
            summary.append("✅ Treatment plan is VALID and safe to implement")
        else:
            summary.append("❌ Treatment plan has VALIDATION ISSUES")
        
        summary.append(f"Safety Score: {validation_result['safety_score']:.1%}")
        summary.append(f"Appropriateness Score: {validation_result['appropriateness_score']:.1%}")
        
        if validation_result["warnings"]:
            summary.append("\n⚠️  Warnings:")
            for warning in validation_result["warnings"][:5]:
                summary.append(f"  • {warning}")
        
        if validation_result["errors"]:
            summary.append("\n❌ Errors:")
            for error in validation_result["errors"][:5]:
                summary.append(f"  • {error}")
        
        if validation_result["requires_human_review"]:
            summary.append("\n🔴 HUMAN SPECIALIST REVIEW REQUIRED")
        
        return "\n".join(summary)

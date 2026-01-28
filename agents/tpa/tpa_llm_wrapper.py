from typing import List, Dict, Any, Optional
from .tpa_schemas import (
    TPAInput, TPAOutput, TreatmentPlan, Intervention, SymptomSeverity,
    PatientPreferences, SymptomCluster, ProvisionalDiagnosis
)
from .tpa_tools import TPATools
from .treatment_plan_validator import TreatmentPlanValidator
import logging
import json

logger = logging.getLogger(__name__)

class TPALLMWrapper:
    """
    LLM wrapper for Treatment Planning Agent (TPA).
    Integrates with LLM client to generate and refine treatment plans.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.tools = TPATools()
        self.validator = TreatmentPlanValidator()
    
    def generate_treatment_plan(self, tpa_input: TPAInput) -> TPAOutput:
        """Generate a comprehensive treatment plan using LLM and TPA tools"""
        try:
            logger.info(f"Generating treatment plan for patient with {len(tpa_input.symptom_clusters)} symptom clusters")
            
            # Step 1: Analyze symptom patterns
            symptom_analysis = self.tools.analyze_symptom_patterns(tpa_input.symptom_clusters)
            
            # Step 2: Select primary intervention
            primary_intervention = self.tools.select_primary_intervention(
                symptom_analysis, 
                tpa_input.provisional_diagnosis, 
                tpa_input.patient_preferences
            )
            
            # Step 3: Select complementary interventions
            complementary_interventions = self.tools.select_complementary_interventions(
                primary_intervention,
                symptom_analysis,
                tpa_input.provisional_diagnosis,
                tpa_input.patient_preferences
            )
            
            # Step 4: Generate self-help resources
            self_help_resources = self.tools.generate_self_help_resources(
                [primary_intervention] + complementary_interventions,
                tpa_input.patient_preferences
            )
            
            # Step 5: Determine follow-up schedule
            follow_up_schedule, reassessment_timeline = self.tools.determine_follow_up_schedule(
                tpa_input.provisional_diagnosis,
                symptom_analysis["complexity_score"],
                symptom_analysis["risk_factors"]
            )
            
            # Step 6: Generate specialist recommendations
            specialist_recommendations = self.tools.generate_specialist_recommendations(
                tpa_input.provisional_diagnosis,
                [primary_intervention] + complementary_interventions,
                tpa_input.patient_preferences
            )
            
            # Step 7: Create the final treatment plan
            treatment_plan = TreatmentPlan(
                patient_id=str(hash(str(tpa_input.patient_demographics.age) + tpa_input.patient_demographics.gender)),
                primary_approach=primary_intervention,
                complementary_strategies=complementary_interventions,
                self_help_resources=self_help_resources,
                follow_up_schedule=follow_up_schedule,
                reassessment_timeline=reassessment_timeline,
                suggested_specialists=specialist_recommendations,
                safety_notes=self._generate_safety_notes(symptom_analysis, tpa_input),
                expected_outcomes=self._generate_expected_outcomes(primary_intervention),
                risk_level=self._determine_risk_level(symptom_analysis, tpa_input),
                escalation_criteria=self._generate_escalation_criteria(symptom_analysis, tpa_input)
            )
            
            # Step 8: Validate the treatment plan
            validation_result = self.validator.validate_treatment_plan(treatment_plan, tpa_input)
            
            # Step 9: Generate reasoning and confidence score
            reasoning = self._generate_reasoning(symptom_analysis, primary_intervention, tpa_input)
            confidence_score = self._calculate_confidence_score(symptom_analysis, validation_result, tpa_input)
            
            # Step 10: Create TPA output
            tpa_output = TPAOutput(
                treatment_plan=treatment_plan,
                confidence_score=confidence_score,
                reasoning=reasoning,
                alternatives_considered=self._generate_alternatives_considered(tpa_input),
                requires_human_review=validation_result["requires_human_review"],
                review_reasons=validation_result.get("review_reasons", [])
            )
            
            logger.info(f"Treatment plan generated successfully. Confidence: {confidence_score:.2f}")
            return tpa_output
            
        except Exception as e:
            logger.error(f"Error generating treatment plan: {e}")
            return self._generate_fallback_plan(tpa_input)
    
    def _generate_safety_notes(self, symptom_analysis: Dict[str, Any], tpa_input: TPAInput) -> List[str]:
        """Generate safety notes for the treatment plan"""
        safety_notes = [
            "Monitor for any worsening of symptoms",
            "Contact healthcare provider if experiencing thoughts of self-harm"
        ]
        
        if tpa_input.provisional_diagnosis.severity == SymptomSeverity.SEVERE:
            safety_notes.append("Close monitoring required due to severe symptoms")
            safety_notes.append("Immediate escalation if symptoms worsen")
        
        if any("suicide" in factor.lower() for factor in symptom_analysis.get("risk_factors", [])):
            safety_notes.append("Enhanced safety monitoring for suicide risk")
        
        return safety_notes
    
    def _generate_expected_outcomes(self, primary_intervention: Intervention) -> List[str]:
        """Generate expected outcomes for the treatment plan"""
        return [
            "Reduction in symptom severity",
            "Improved daily functioning",
            "Enhanced coping skills",
            "Better quality of life"
        ]
    
    def _determine_risk_level(self, symptom_analysis: Dict[str, Any], tpa_input: TPAInput) -> str:
        """Determine the risk level of the treatment plan"""
        if tpa_input.provisional_diagnosis.severity == SymptomSeverity.SEVERE:
            return "high"
        elif tpa_input.provisional_diagnosis.severity == SymptomSeverity.MODERATE:
            return "medium"
        else:
            return "low"
    
    def _generate_escalation_criteria(self, symptom_analysis: Dict[str, Any], tpa_input: TPAInput) -> List[str]:
        """Generate escalation criteria for the treatment plan"""
        criteria = [
            "No improvement after 4 weeks",
            "Worsening of symptoms",
            "Difficulty implementing interventions"
        ]
        
        if tpa_input.provisional_diagnosis.severity == SymptomSeverity.SEVERE:
            criteria.insert(0, "Immediate safety concerns")
            criteria.insert(1, "No improvement after 2 weeks")
        
        return criteria
    
    def _generate_reasoning(self, symptom_analysis: Dict[str, Any], primary_intervention: Intervention, tpa_input: TPAInput) -> str:
        """Generate reasoning for the treatment plan choices"""
        reasoning_parts = []
        
        primary_concerns = symptom_analysis.get("primary_concerns", [])
        reasoning_parts.append(
            f"The primary intervention '{primary_intervention.name}' was selected because it has strong evidence "
            f"for treating {', '.join(primary_concerns)} and is appropriate for {tpa_input.provisional_diagnosis.severity.value} severity."
        )
        
        preferences = tpa_input.patient_preferences
        reasoning_parts.append(
            f"The plan aligns with patient preferences: {preferences.preferred_approach} approach, "
            f"{preferences.mode_preference} delivery, and {preferences.budget_level} budget level."
        )
        
        return " ".join(reasoning_parts)
    
    def _calculate_confidence_score(self, symptom_analysis: Dict[str, Any], validation_result: Dict[str, Any], tpa_input: TPAInput) -> float:
        """Calculate confidence score for the treatment plan"""
        base_score = 0.7
        
        if symptom_analysis.get("primary_concerns"):
            base_score += 0.1
        
        if validation_result.get("safety_score", 1.0) > 0.8:
            base_score += 0.1
        
        if tpa_input.provisional_diagnosis.confidence_level > 0.8:
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score))
    
    def _generate_alternatives_considered(self, tpa_input: TPAInput) -> List[str]:
        """Generate list of alternatives considered"""
        return [
            "Medication-based treatment (patient preference: non-medication)",
            "Inpatient treatment (not indicated for current severity)",
            "Alternative therapy approaches (less evidence-based)"
        ]
    
    def _generate_fallback_plan(self, tpa_input: TPAInput) -> TPAOutput:
        """Generate a safe fallback plan when the main process fails"""
        logger.warning("Generating fallback treatment plan due to processing errors")
        
        fallback_intervention = self.tools._get_fallback_intervention(
            tpa_input.provisional_diagnosis.severity
        )
        
        treatment_plan = TreatmentPlan(
            patient_id="fallback",
            primary_approach=fallback_intervention,
            complementary_strategies=[],
            self_help_resources=[],
            follow_up_schedule="Weekly check-ins",
            reassessment_timeline="2 weeks",
            suggested_specialists=[],
            safety_notes=["This is a fallback plan - requires immediate human review"],
            expected_outcomes=["Stabilization of symptoms"],
            risk_level="medium",
            escalation_criteria=["Immediate human specialist review required"]
        )
        
        return TPAOutput(
            treatment_plan=treatment_plan,
            confidence_score=0.3,
            reasoning="Fallback plan generated due to processing errors. Requires immediate human review.",
            alternatives_considered=[],
            requires_human_review=True,
            review_reasons=["Processing error occurred", "Fallback plan generated"]
        )

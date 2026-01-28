from typing import List, Dict, Any, Optional
from .tpa_schemas import (
    TPAInput, TPAOutput, TreatmentPlan, Intervention, SymptomSeverity,
    PatientPreferences, SymptomCluster, ProvisionalDiagnosis, PatientDemographics, PatientGoals, 
    SimpleTreatmentPlan, SimpleTreatmentStep, TreatmentPlanSimple, PlanMetadata, TrackingSchema
)
from .tpa_llm_wrapper import TPALLMWrapper
from .tpa_tools import TPATools
from .treatment_plan_validator import TreatmentPlanValidator
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class TreatmentPlanningAgent:
    """
    Treatment Planning Agent (TPA) - Creates simple, actionable, step-by-step non-medication treatment plans.
    
    Purpose: Produce a simple, actionable, step-by-step non-medication treatment plan 
    (therapy + skills + lifestyle + resources) the patient can follow and report on.
    
    Assumptions:
    - Inputs are structured (DA diagnosis + SRA symptoms + patient preferences)
    - Plans are non-medication only
    - Plans must be human-readable, small steps, and easily tracked/reminded
    - Risk assessment and urgent flags are handled elsewhere
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the Treatment Planning Agent
        
        Args:
            llm_client: Optional LLM client for enhanced plan generation
        """
        self.tools = TPATools()
        self.validator = TreatmentPlanValidator()
        self.llm_wrapper = TPALLMWrapper(llm_client) if llm_client else None
        
        logger.info("Treatment Planning Agent initialized successfully")
    
    def create_treatment_plan(
        self,
        patient_demographics: PatientDemographics,
        patient_goals: PatientGoals,
        symptom_clusters: List[SymptomCluster],
        provisional_diagnosis: ProvisionalDiagnosis,
        patient_preferences: PatientPreferences,
        red_flags: List[str] = None
    ) -> TPAOutput:
        """
        Create a comprehensive treatment plan based on all available patient data
        
        Args:
            patient_demographics: Patient demographic information from PIMA
            patient_goals: Patient's stated goals and preferences
            symptom_clusters: Recognized symptom clusters from SRA
            provisional_diagnosis: Provisional diagnosis from DA
            patient_preferences: Patient's treatment preferences
            red_flags: Any safety concerns or red flags
            
        Returns:
            TPAOutput containing the complete treatment plan and metadata
        """
        try:
            logger.info(f"Creating treatment plan for patient (Age: {patient_demographics.age}, Gender: {patient_demographics.gender})")
            
            # Create TPA input
            tpa_input = TPAInput(
                patient_demographics=patient_demographics,
                patient_goals=patient_goals,
                symptom_clusters=symptom_clusters,
                provisional_diagnosis=provisional_diagnosis,
                patient_preferences=patient_preferences,
                red_flags=red_flags or []
            )
            
            # Generate treatment plan
            if self.llm_wrapper:
                tpa_output = self.llm_wrapper.generate_treatment_plan(tpa_input)
            else:
                tpa_output = self._generate_plan_without_llm(tpa_input)
            
            # Log the generated plan
            self._log_treatment_plan(tpa_output)
            
            return tpa_output
            
        except Exception as e:
            logger.error(f"Error creating treatment plan: {e}")
            return self._create_error_output(str(e), tpa_input)
    
    def create_simple_treatment_plan(
        self,
        patient_demographics: PatientDemographics,
        patient_goals: PatientGoals,
        symptom_clusters: List[SymptomCluster],
        provisional_diagnosis: ProvisionalDiagnosis,
        patient_preferences: PatientPreferences,
        red_flags: List[str] = None
    ) -> TreatmentPlanSimple:
        """
        Create a simple, actionable, step-by-step non-medication treatment plan
        
        This is the main method that produces the patient-friendly plan according to guidelines.
        
        Args:
            patient_demographics: Patient demographic information from PIMA
            patient_goals: Patient's stated goals and preferences
            symptom_clusters: Recognized symptom clusters from SRA
            provisional_diagnosis: Provisional diagnosis from DA
            patient_preferences: Patient's treatment preferences
            red_flags: Any safety concerns or red flags
            
        Returns:
            TreatmentPlanSimple containing the patient-friendly, step-by-step treatment plan
        """
        try:
            logger.info(f"Creating simple treatment plan for patient (Age: {patient_demographics.age}, Gender: {patient_demographics.gender})")
            
            # Create TPA input
            tpa_input = TPAInput(
                patient_demographics=patient_demographics,
                patient_goals=patient_goals,
                symptom_clusters=symptom_clusters,
                provisional_diagnosis=provisional_diagnosis,
                patient_preferences=patient_preferences,
                red_flags=red_flags or []
            )
            
            # Step 1: Map diagnosis/symptoms → evidence-based interventions
            interventions = self.tools.map_symptoms_to_interventions(
                symptom_clusters, 
                provisional_diagnosis, 
                patient_preferences
            )
            
            # Step 2: Prioritize interventions (limit to 3-6 items)
            prioritized_interventions = self.tools.prioritize_interventions(
                interventions, 
                patient_preferences, 
                max_count=4
            )
            
            # Step 3: Decompose interventions into trackable micro-tasks
            micro_tasks = self.tools.decompose_to_micro_tasks(
                prioritized_interventions, 
                patient_preferences
            )
            
            # Step 4: Create plain-English plan with numbered steps
            plan_steps = self.tools.create_plain_english_steps(
                micro_tasks, 
                patient_preferences, 
                provisional_diagnosis
            )
            
            # Step 5: Create tracking schema
            tracking_schema = self.tools.create_tracking_schema(
                plan_steps, 
                patient_preferences
            )
            
            # Step 6: Create reminder schedule
            reminder_schedule = self.tools.create_reminder_schedule(
                plan_steps, 
                patient_preferences
            )
            
            # Step 7: Create plan metadata
            plan_metadata = self.tools.create_plan_metadata(
                plan_steps, 
                provisional_diagnosis, 
                patient_preferences
            )
            
            # Step 8: Create simple treatment plan
            simple_plan = TreatmentPlanSimple(
                patient_id=str(hash(str(patient_demographics.age) + patient_demographics.gender)),
                title=self._create_plan_title(provisional_diagnosis, patient_preferences),
                goal=self._create_plan_goal(patient_goals, provisional_diagnosis),
                top_actions=self._create_top_actions(prioritized_interventions),
                step_by_step=plan_steps,
                weekly_plan=self._create_weekly_plan(plan_steps, patient_preferences),
                safety_note=self._create_safety_note(provisional_diagnosis),
                plan_metadata=plan_metadata,
                tracking_schema=tracking_schema,
                reminder_schedule=reminder_schedule
            )
            
            logger.info(f"Simple treatment plan generated with {len(plan_steps)} steps")
            
            return simple_plan
            
        except Exception as e:
            logger.error(f"Error creating simple treatment plan: {e}")
            # Return a minimal fallback plan
            return self._create_simple_fallback_plan(patient_demographics, provisional_diagnosis)
    
    def _create_plan_title(self, diagnosis: ProvisionalDiagnosis, preferences: PatientPreferences) -> str:
        """Create a simple, clear plan title"""
        severity = diagnosis.severity.value
        duration = "8-week" if severity == "moderate" else "4-week" if severity == "mild" else "12-week"
        
        if "anxiety" in diagnosis.primary_diagnosis.lower():
            return f"{duration} plan to reduce anxiety & improve daily life"
        elif "depression" in diagnosis.primary_diagnosis.lower():
            return f"{duration} plan to improve mood & energy"
        elif "insomnia" in diagnosis.primary_diagnosis.lower():
            return f"{duration} plan to improve sleep & rest"
        else:
            return f"{duration} plan to improve mental health & well-being"
    
    def _create_plan_goal(self, goals: PatientGoals, diagnosis: ProvisionalDiagnosis) -> str:
        """Create a simple, clear goal statement"""
        if goals.primary_goals:
            # Use the first primary goal if available
            return f"Goal: {goals.primary_goals[0].lower()}"
        
        # Fallback based on diagnosis
        if "anxiety" in diagnosis.primary_diagnosis.lower():
            return "Goal: Feel calmer and more in control of daily life"
        elif "depression" in diagnosis.primary_diagnosis.lower():
            return "Goal: Feel more positive and motivated to enjoy life"
        elif "insomnia" in diagnosis.primary_diagnosis.lower():
            return "Goal: Sleep better and feel more rested during the day"
        else:
            return "Goal: Feel better and more in control of your mental health"
    
    def _create_top_actions(self, interventions: List[Intervention]) -> List[str]:
        """Create top 3 actions in simple language"""
        top_actions = []
        
        for i, intervention in enumerate(interventions[:3]):
            if "CBT" in intervention.name:
                action = f"Weekly CBT sessions ({intervention.duration}) — focus on {intervention.description.lower()}"
            elif "Mindfulness" in intervention.name:
                action = f"Daily {intervention.frequency} relaxation (guided breathing or mindfulness)"
            elif "Sleep" in intervention.name:
                action = f"Sleep routine: go to bed at the same time, avoid screens 30 min before bed"
            elif "Exercise" in intervention.name:
                action = f"Regular physical activity: {intervention.frequency} for {intervention.duration}"
            else:
                action = f"{intervention.name}: {intervention.description}"
            
            top_actions.append(action)
        
        return top_actions
    
    def _create_weekly_plan(self, steps: List[Dict], preferences: PatientPreferences) -> Dict[str, List[str]]:
        """Create weekly breakdown of the plan"""
        weekly_plan = {
            "Week 1": ["Onboarding + first steps + start daily routine"],
            "Weeks 2-7": ["Continue skills + weekly check-ins + homework"],
            "Week 8": ["Review & plan next steps"]
        }
        
        # Adjust based on patient preferences
        if preferences.preferred_approach == "self_help":
            weekly_plan["Week 1"] = ["Start daily routine + first skill practice"]
            weekly_plan["Weeks 2-7"] = ["Continue daily practice + weekly progress review"]
            weekly_plan["Week 8"] = ["Review progress & plan maintenance"]
        
        return weekly_plan
    
    def _create_safety_note(self, diagnosis: ProvisionalDiagnosis) -> str:
        """Create simple safety note"""
        return (
            "If your mood drops quickly or you have thoughts of self-harm, please use the emergency button "
            "or contact local services. (Risk assessment is handled separately by PIMA.)"
        )
    
    def _create_plan_title(self, diagnosis: ProvisionalDiagnosis, preferences: PatientPreferences) -> str:
        """Create a simple, clear plan title"""
        severity = diagnosis.severity.value
        duration = "8-week" if severity == "moderate" else "4-week" if severity == "mild" else "12-week"
        
        if "anxiety" in diagnosis.primary_diagnosis.lower():
            return f"{duration} plan to reduce anxiety & improve daily life"
        elif "depression" in diagnosis.primary_diagnosis.lower():
            return f"{duration} plan to improve mood & energy"
        elif "insomnia" in diagnosis.primary_diagnosis.lower():
            return f"{duration} plan to improve sleep & rest"
        else:
            return f"{duration} plan to improve mental health & well-being"
    
    def _create_plan_goal(self, goals: PatientGoals, diagnosis: ProvisionalDiagnosis) -> str:
        """Create a simple, clear goal statement"""
        if goals.primary_goals:
            # Use the first primary goal if available
            return f"Goal: {goals.primary_goals[0].lower()}"
        
        # Fallback based on diagnosis
        if "anxiety" in diagnosis.primary_diagnosis.lower():
            return "Goal: Feel calmer and more in control of daily life"
        elif "depression" in diagnosis.primary_diagnosis.lower():
            return "Goal: Feel more positive and motivated to enjoy life"
        elif "insomnia" in diagnosis.primary_diagnosis.lower():
            return "Goal: Sleep better and feel more rested during the day"
        else:
            return "Goal: Feel better and more in control of your mental health"
    
    def _create_top_actions(self, interventions: List[Intervention]) -> List[str]:
        """Create top 3 actions in simple language"""
        top_actions = []
        
        for i, intervention in enumerate(interventions[:3]):
            if "CBT" in intervention.name:
                action = f"Weekly CBT sessions ({intervention.duration}) — focus on {intervention.description.lower()}"
            elif "Mindfulness" in intervention.name:
                action = f"Daily {intervention.frequency} relaxation (guided breathing or mindfulness)"
            elif "Sleep" in intervention.name:
                action = f"Sleep routine: go to bed at the same time, avoid screens 30 min before bed"
            elif "Exercise" in intervention.name:
                action = f"Regular physical activity: {intervention.frequency} for {intervention.duration}"
            else:
                action = f"{intervention.name}: {intervention.description}"
            
            top_actions.append(action)
        
        return top_actions
    
    def _create_weekly_plan(self, steps: List[Dict], preferences: PatientPreferences) -> Dict[str, List[str]]:
        """Create weekly breakdown of the plan"""
        weekly_plan = {
            "Week 1": ["Onboarding + first steps + start daily routine"],
            "Weeks 2-7": ["Continue skills + weekly check-ins + homework"],
            "Week 8": ["Review & plan next steps"]
        }
        
        # Adjust based on patient preferences
        if preferences.preferred_approach == "self_help":
            weekly_plan["Week 1"] = ["Start daily routine + first skill practice"]
            weekly_plan["Weeks 2-7"] = ["Continue daily practice + weekly progress review"]
            weekly_plan["Week 8"] = ["Review progress & plan maintenance"]
        
        return weekly_plan
    
    def _create_safety_note(self, diagnosis: ProvisionalDiagnosis) -> str:
        """Create simple safety note"""
        return (
            "If your mood drops quickly or you have thoughts of self-harm, please use the emergency button "
            "or contact local services. (Risk assessment is handled separately by PIMA.)"
        )
    
    def _create_simple_fallback_plan(self, demographics: PatientDemographics, diagnosis: ProvisionalDiagnosis) -> TreatmentPlanSimple:
        """Create a simple fallback plan when the main process fails"""
        fallback_step = {
            "step_number": 1,
            "title": "Start with Basic Self-Care",
            "description": "Focus on getting enough sleep, eating regular meals, and staying hydrated",
            "when": "Daily",
            "how_long": "5-10 minutes",
            "why": "Basic self-care helps stabilize your mood and energy",
            "how_to_track": "Rate your mood (0-10) and note if you completed basic self-care"
        }
        
        return TreatmentPlanSimple(
            patient_id=str(hash(str(demographics.age) + demographics.gender)),
            title="Basic Self-Care Plan",
            goal="Goal: Feel more stable and grounded through basic self-care",
            top_actions=["Daily basic self-care routine", "Regular sleep schedule", "Simple mood tracking"],
            step_by_step=[fallback_step],
            weekly_plan={
                "Week 1": ["Start basic routine"],
                "Week 2": ["Continue routine + add mood tracking"],
                "Week 3": ["Review progress & adjust"]
            },
            safety_note="If you're having thoughts of harming yourself, please contact emergency services immediately.",
            plan_metadata=PlanMetadata(
                total_duration="3 weeks",
                total_steps=1,
                estimated_time_per_day="5-10 minutes",
                frequency="Daily"
            ),
            tracking_schema=TrackingSchema(
                daily_tasks=["mood_rating", "basic_care_completed"],
                weekly_summary=["mood_trend", "adherence_rate"],
                progress_rules=["If mood drops by 2+ points for 2+ days, contact support"]
            ),
            reminder_schedule="Daily reminders at 9 AM"
        )

    def _generate_plan_without_llm(self, tpa_input: TPAInput) -> TPAOutput:
        """Generate treatment plan without LLM enhancement"""
        try:
            # Analyze symptom patterns
            symptom_analysis = self.tools.analyze_symptom_patterns(tpa_input.symptom_clusters)
            
            # Select primary intervention
            primary_intervention = self.tools.select_primary_intervention(
                symptom_analysis, 
                tpa_input.provisional_diagnosis, 
                tpa_input.patient_preferences
            )
            
            # Select complementary interventions
            complementary_interventions = self.tools.select_complementary_interventions(
                primary_intervention,
                symptom_analysis,
                tpa_input.provisional_diagnosis,
                tpa_input.patient_preferences
            )
            
            # Generate self-help resources
            self_help_resources = self.tools.generate_self_help_resources(
                [primary_intervention] + complementary_interventions,
                tpa_input.patient_preferences
            )
            
            # Determine follow-up schedule
            follow_up_schedule, reassessment_timeline = self.tools.determine_follow_up_schedule(
                tpa_input.provisional_diagnosis,
                symptom_analysis["complexity_score"],
                symptom_analysis["risk_factors"]
            )
            
            # Generate specialist recommendations
            specialist_recommendations = self.tools.generate_specialist_recommendations(
                tpa_input.provisional_diagnosis,
                [primary_intervention] + complementary_interventions,
                tpa_input.patient_preferences
            )
            
            # Create treatment plan
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
            
            # Validate plan
            validation_result = self.validator.validate_treatment_plan(treatment_plan, tpa_input)
            
            # Generate reasoning and confidence
            reasoning = self._generate_reasoning(symptom_analysis, primary_intervention, tpa_input)
            confidence_score = self._calculate_confidence_score(symptom_analysis, validation_result, tpa_input)
            
            return TPAOutput(
                treatment_plan=treatment_plan,
                confidence_score=confidence_score,
                reasoning=reasoning,
                alternatives_considered=self._generate_alternatives_considered(tpa_input),
                requires_human_review=validation_result["requires_human_review"],
                review_reasons=validation_result.get("review_reasons", [])
            )
            
        except Exception as e:
            logger.error(f"Error in non-LLM plan generation: {e}")
            return self._create_error_output(str(e))
    
    def validate_existing_plan(self, treatment_plan: TreatmentPlan, tpa_input: TPAInput) -> Dict[str, Any]:
        """
        Validate an existing treatment plan
        
        Args:
            treatment_plan: The treatment plan to validate
            tpa_input: Original TPA input data
            
        Returns:
            Validation results
        """
        try:
            validation_result = self.validator.validate_treatment_plan(treatment_plan, tpa_input)
            return validation_result
        except Exception as e:
            logger.error(f"Error validating treatment plan: {e}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "requires_human_review": True
            }
    
    def get_plan_summary(self, tpa_output: TPAOutput) -> Dict[str, Any]:
        """
        Get a summary of the treatment plan for reporting purposes
        
        Args:
            tpa_output: The TPA output to summarize
            
        Returns:
            Summary of the treatment plan
        """
        plan = tpa_output.treatment_plan
        
        summary = {
            "patient_id": plan.patient_id,
            "created_at": plan.created_at.isoformat(),
            "primary_intervention": {
                "name": plan.primary_approach.name,
                "type": plan.primary_approach.type.value,
                "duration": plan.primary_approach.duration
            },
            "complementary_interventions": [
                {
                    "name": intervention.name,
                    "type": intervention.type.value,
                    "duration": intervention.duration
                }
                for intervention in plan.complementary_strategies
            ],
            "follow_up_schedule": plan.follow_up_schedule,
            "reassessment_timeline": plan.reassessment_timeline,
            "risk_level": plan.risk_level,
            "confidence_score": tpa_output.confidence_score,
            "requires_human_review": tpa_output.requires_human_review
        }
        
        return summary
    
    def export_plan_to_json(self, tpa_output: TPAOutput) -> str:
        """
        Export the treatment plan to JSON format
        
        Args:
            tpa_output: The TPA output to export
            
        Returns:
            JSON string representation of the plan
        """
        try:
            # Convert to dict for JSON serialization
            plan_dict = {
                "treatment_plan": tpa_output.treatment_plan.dict(),
                "confidence_score": tpa_output.confidence_score,
                "reasoning": tpa_output.reasoning,
                "alternatives_considered": tpa_output.alternatives_considered,
                "requires_human_review": tpa_output.requires_human_review,
                "review_reasons": tpa_output.review_reasons,
                "exported_at": datetime.now().isoformat()
            }
            
            return json.dumps(plan_dict, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"Error exporting plan to JSON: {e}")
            return json.dumps({"error": f"Export failed: {str(e)}"})
    
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
    
    def _create_error_output(self, error_message: str, tpa_input: TPAInput = None) -> TPAOutput:
        """Create an error output when plan generation fails"""
        from .tpa_tools import TPATools
        tools = TPATools()
        
        # Create minimal safe plan
        fallback_intervention = tools._get_fallback_intervention(SymptomSeverity.MILD)
        
        # Generate patient ID if input is available, otherwise use fallback
        if tpa_input:
            patient_id = str(hash(str(tpa_input.patient_demographics.age) + tpa_input.patient_demographics.gender))
        else:
            patient_id = "error_fallback"
        
        from .tpa_schemas import TreatmentPlan
        treatment_plan = TreatmentPlan(
            patient_id=patient_id,
            primary_approach=fallback_intervention,
            complementary_strategies=[],
            self_help_resources=[],
            follow_up_schedule="Immediate human review required",
            reassessment_timeline="1 week",
            suggested_specialists=[],
            safety_notes=["Error occurred during plan generation - requires human review"],
            expected_outcomes=["Plan review and correction"],
            risk_level="medium",
            escalation_criteria=["Immediate human specialist review required"]
        )
        
        return TPAOutput(
            treatment_plan=treatment_plan,
            confidence_score=0.1,
            reasoning=f"Error occurred during plan generation: {error_message}",
            alternatives_considered=[],
            requires_human_review=True,
            review_reasons=["Plan generation error", error_message]
        )
    
    def _log_treatment_plan(self, tpa_output: TPAOutput):
        """Log the generated treatment plan for monitoring purposes"""
        plan = tpa_output.treatment_plan
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "patient_id": plan.patient_id,
            "primary_intervention": plan.primary_approach.name,
            "confidence_score": tpa_output.confidence_score,
            "requires_human_review": tpa_output.requires_human_review,
            "risk_level": plan.risk_level
        }
        
        logger.info(f"Treatment plan generated: {json.dumps(log_entry)}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get the current status of the TPA agent"""
        return {
            "agent_name": "Treatment Planning Agent (TPA)",
            "status": "active",
            "version": "2.0.0",
            "capabilities": [
                "Simple, actionable treatment plan generation",
                "Step-by-step non-medication interventions",
                "Plain-English patient communication",
                "Trackable micro-tasks",
                "Progress monitoring and reminders",
                "Export to JSON and printable formats"
            ],
            "llm_enhanced": self.llm_wrapper is not None,
            "last_activity": datetime.now().isoformat()
        }

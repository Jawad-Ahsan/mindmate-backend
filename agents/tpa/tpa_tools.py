from typing import List, Dict, Any, Optional, Tuple
from .tpa_schemas import (
    TPAInput, TPAOutput, TreatmentPlan, Intervention, SymptomSeverity,
    PatientPreferences, SymptomCluster, ProvisionalDiagnosis, SimpleTreatmentPlan, SimpleTreatmentStep
)
from .treatment_guidelines import TreatmentGuidelines
from .treatment_plan_validator import TreatmentPlanValidator
import logging
import uuid
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TPATools:
    """
    Core tools for Treatment Planning Agent (TPA).
    Handles symptom analysis, intervention selection, and treatment plan generation.
    """
    
    def __init__(self):
        self.guidelines = TreatmentGuidelines()
        self.validator = TreatmentPlanValidator()
    
    def analyze_symptom_patterns(self, symptom_clusters: List[SymptomCluster]) -> Dict[str, Any]:
        """
        Analyze symptom patterns to identify primary concerns and intervention priorities
        
        Args:
            symptom_clusters: List of symptom clusters from SRA
            
        Returns:
            Analysis results including primary concerns and intervention priorities
        """
        analysis = {
            "primary_concerns": [],
            "intervention_priorities": [],
            "complexity_score": 0.0,
            "risk_factors": [],
            "comorbidity_patterns": []
        }
        
        if not symptom_clusters:
            return analysis
        
        # Calculate complexity score based on number and severity of clusters
        total_severity = sum(
            1 if cluster.severity == SymptomSeverity.MILD else
            2 if cluster.severity == SymptomSeverity.MODERATE else 3
            for cluster in symptom_clusters
        )
        analysis["complexity_score"] = min(1.0, total_severity / (len(symptom_clusters) * 3))
        
        # Identify primary concerns (clusters with highest severity)
        severe_clusters = [cluster for cluster in symptom_clusters if cluster.severity == SymptomSeverity.SEVERE]
        moderate_clusters = [cluster for cluster in symptom_clusters if cluster.severity == SymptomSeverity.MODERATE]
        
        if severe_clusters:
            analysis["primary_concerns"] = [cluster.name for cluster in severe_clusters]
            analysis["risk_factors"].extend([cluster.name for cluster in severe_clusters])
        elif moderate_clusters:
            analysis["primary_concerns"] = [cluster.name for cluster in moderate_clusters]
        else:
            analysis["primary_concerns"] = [cluster.name for cluster in symptom_clusters[:2]]
        
        # Identify comorbidity patterns
        if len(symptom_clusters) > 1:
            cluster_names = [cluster.name.lower() for cluster in symptom_clusters]
            
            # Common comorbidity patterns
            if "depression" in cluster_names and "anxiety" in cluster_names:
                analysis["comorbidity_patterns"].append("Depression-Anxiety Comorbidity")
            if "adhd" in cluster_names and ("anxiety" in cluster_names or "depression" in cluster_names):
                analysis["comorbidity_patterns"].append("ADHD with Mood Disorder")
            if "ptsd" in cluster_names and ("anxiety" in cluster_names or "depression" in cluster_names):
                analysis["comorbidity_patterns"].append("PTSD with Mood Disorder")
        
        # Set intervention priorities based on primary concerns
        analysis["intervention_priorities"] = analysis["primary_concerns"][:3]
        
        return analysis
    
    def select_primary_intervention(
        self, 
        symptom_analysis: Dict[str, Any],
        diagnosis: ProvisionalDiagnosis,
        preferences: PatientPreferences
    ) -> Intervention:
        """
        Select the primary intervention based on symptoms, diagnosis, and preferences
        
        Args:
            symptom_analysis: Results from symptom pattern analysis
            diagnosis: Provisional diagnosis from DA
            preferences: Patient preferences
            
        Returns:
            Selected primary intervention
        """
        # Get evidence-based interventions for primary concerns
        primary_concerns = symptom_analysis.get("primary_concerns", [])
        if not primary_concerns:
            primary_concerns = [diagnosis.primary_diagnosis.lower()]
        
        # Get interventions for the primary concern
        available_interventions = []
        for concern in primary_concerns:
            interventions = self.guidelines.get_evidence_based_interventions(concern)
            available_interventions.extend(interventions)
        
        if not available_interventions:
            # Fallback to general interventions
            available_interventions = self.guidelines.get_all_interventions()
        
        # Filter by severity appropriateness
        severity_guidelines = self.guidelines.get_severity_guidelines(diagnosis.severity)
        appropriate_interventions = []
        
        for intervention in available_interventions:
            if self._is_intervention_appropriate_for_severity(intervention, diagnosis.severity):
                appropriate_interventions.append(intervention)
        
        if not appropriate_interventions:
            appropriate_interventions = available_interventions
        
        # Score interventions based on preferences and evidence
        scored_interventions = []
        for intervention in appropriate_interventions:
            score = self._score_intervention_for_preferences(intervention, preferences)
            scored_interventions.append((intervention, score))
        
        # Sort by score and return the best match
        scored_interventions.sort(key=lambda x: x[1], reverse=True)
        
        if scored_interventions:
            return scored_interventions[0][0]
        else:
            # Fallback to a safe default
            return self._get_fallback_intervention(diagnosis.severity)
    
    def select_complementary_interventions(
        self,
        primary_intervention: Intervention,
        symptom_analysis: Dict[str, Any],
        diagnosis: ProvisionalDiagnosis,
        preferences: PatientPreferences,
        max_count: int = 3
    ) -> List[Intervention]:
        """
        Select complementary interventions to support the primary approach
        
        Args:
            primary_intervention: The primary intervention already selected
            symptom_analysis: Results from symptom pattern analysis
            diagnosis: Provisional diagnosis
            preferences: Patient preferences
            max_count: Maximum number of complementary interventions
            
        Returns:
            List of complementary interventions
        """
        complementary_interventions = []
        
        # Get interventions for remaining symptoms not addressed by primary
        primary_symptoms = self._get_intervention_symptoms(primary_intervention)
        remaining_symptoms = [
            concern for concern in symptom_analysis.get("primary_concerns", [])
            if concern.lower() not in primary_symptoms
        ]
        
        # Add interventions for remaining symptoms
        for symptom in remaining_symptoms[:2]:  # Limit to 2 additional symptoms
            interventions = self.guidelines.get_evidence_based_interventions(symptom)
            for intervention in interventions:
                if (intervention.name != primary_intervention.name and
                    intervention not in complementary_interventions and
                    len(complementary_interventions) < max_count):
                    complementary_interventions.append(intervention)
        
        # Add lifestyle/support interventions if space allows
        if len(complementary_interventions) < max_count:
            lifestyle_interventions = self._get_lifestyle_interventions(preferences)
            for intervention in lifestyle_interventions:
                if (intervention not in complementary_interventions and
                    len(complementary_interventions) < max_count):
                    complementary_interventions.append(intervention)
        
        return complementary_interventions[:max_count]
    
    def generate_self_help_resources(
        self,
        interventions: List[Intervention],
        preferences: PatientPreferences
    ) -> List[Dict[str, str]]:
        """
        Generate appropriate self-help resources based on interventions and preferences
        
        Args:
            interventions: Selected interventions
            preferences: Patient preferences
            
        Returns:
            List of self-help resources
        """
        resources = []
        
        # CBT resources
        if any(intervention.type.value == "CBT" for intervention in interventions):
            resources.append({
                "type": "workbook",
                "title": "CBT Thought Record Worksheet",
                "description": "Daily worksheet for identifying and challenging negative thoughts",
                "format": "PDF" if preferences.mode_preference == "online" else "Printable",
                "estimated_time": "15 minutes daily"
            })
        
        # Mindfulness resources
        if any(intervention.type.value == "Mindfulness" for intervention in interventions):
            resources.append({
                "type": "app",
                "title": "Mindfulness Meditation App",
                "description": "Guided meditation sessions for beginners",
                "format": "Mobile app",
                "estimated_time": "10-20 minutes daily"
            })
        
        # Sleep hygiene resources
        if any(intervention.type.value == "Sleep Hygiene" for intervention in interventions):
            resources.append({
                "type": "guide",
                "title": "Sleep Hygiene Checklist",
                "description": "Daily checklist for improving sleep quality",
                "format": "Digital checklist",
                "estimated_time": "5 minutes daily"
            })
        
        # Exercise resources
        if any(intervention.type.value == "Exercise" for intervention in interventions):
            resources.append({
                "type": "plan",
                "title": "Exercise Routine Plan",
                "description": "Simple exercise routine for mental health benefits",
                "format": "Printable plan",
                "estimated_time": "30 minutes 3-5 times per week"
            })
        
        # Journaling resources
        if any(intervention.type.value == "Journaling" for intervention in interventions):
            resources.append({
                "type": "prompts",
                "title": "Therapeutic Journaling Prompts",
                "description": "Daily writing prompts for emotional processing",
                "format": "Digital prompts",
                "estimated_time": "10-15 minutes daily"
            })
        
        return resources
    
    def determine_follow_up_schedule(
        self,
        diagnosis: ProvisionalDiagnosis,
        complexity_score: float,
        risk_factors: List[str]
    ) -> Tuple[str, str]:
        """
        Determine appropriate follow-up schedule and reassessment timeline
        
        Args:
            diagnosis: Provisional diagnosis
            complexity_score: Complexity score from symptom analysis
            risk_factors: Identified risk factors
            
        Returns:
            Tuple of (follow_up_schedule, reassessment_timeline)
        """
        severity = diagnosis.severity
        
        if severity == SymptomSeverity.SEVERE or complexity_score > 0.7:
            follow_up = "Weekly check-ins for first 4 weeks, then bi-weekly"
            reassessment = "4 weeks"
        elif severity == SymptomSeverity.MODERATE or complexity_score > 0.4:
            follow_up = "Bi-weekly check-ins for first 6 weeks, then monthly"
            reassessment = "6 weeks"
        else:
            follow_up = "Monthly check-ins"
            reassessment = "8 weeks"
        
        # Adjust for risk factors
        if any("suicide" in factor.lower() or "self-harm" in factor.lower() for factor in risk_factors):
            follow_up = "Weekly check-ins with safety monitoring"
            reassessment = "2 weeks"
        
        return follow_up, reassessment
    
    def generate_specialist_recommendations(
        self,
        diagnosis: ProvisionalDiagnosis,
        interventions: List[Intervention],
        preferences: PatientPreferences
    ) -> List[Dict[str, str]]:
        """
        Generate specialist recommendations if therapy is needed
        
        Args:
            diagnosis: Provisional diagnosis
            interventions: Selected interventions
            preferences: Patient preferences
            
        Returns:
            List of specialist recommendations
        """
        specialists = []
        
        # Determine if therapy is needed based on severity and interventions
        needs_therapy = (
            diagnosis.severity == SymptomSeverity.SEVERE or
            any(intervention.type.value in ["CBT", "DBT", "ACT"] for intervention in interventions)
        )
        
        if needs_therapy:
            # CBT specialists
            if any(intervention.type.value == "CBT" for intervention in interventions):
                specialists.append({
                    "type": "CBT Therapist",
                    "specialization": "Cognitive Behavioral Therapy",
                    "credentials": "Licensed Clinical Psychologist or LCSW",
                    "modality": preferences.mode_preference,
                    "estimated_cost": "Low-cost" if preferences.budget_level == "low_cost" else "Standard"
                })
            
            # DBT specialists
            if any(intervention.type.value == "DBT" for intervention in interventions):
                specialists.append({
                    "type": "DBT Therapist",
                    "specialization": "Dialectical Behavior Therapy",
                    "credentials": "Licensed DBT Therapist",
                    "modality": "Group therapy + individual sessions",
                    "estimated_cost": "Standard to Premium"
                })
            
            # General mental health specialists
            specialists.append({
                "type": "Mental Health Counselor",
                "specialization": "General mental health and wellness",
                "credentials": "Licensed Professional Counselor or LCSW",
                "modality": preferences.mode_preference,
                "estimated_cost": "Low-cost to Standard"
            })
        
        return specialists
    
    def _is_intervention_appropriate_for_severity(
        self, 
        intervention: Intervention, 
        severity: SymptomSeverity
    ) -> bool:
        """Check if intervention is appropriate for given severity level"""
        if severity == SymptomSeverity.SEVERE:
            # Some interventions require professional supervision for severe cases
            contraindicated_for_severe = [
                "journaling", "cbt_exposure", "dbt_skills"
            ]
            if any(contraindicated in intervention.name.lower() for contraindicated in contraindicated_for_severe):
                return False
        
        return True
    
    def _score_intervention_for_preferences(
        self, 
        intervention: Intervention, 
        preferences: PatientPreferences
    ) -> float:
        """Score intervention based on patient preferences"""
        score = 0.0
        
        # Time commitment alignment
        estimated_time = self._estimate_intervention_time(intervention)
        if estimated_time <= preferences.weekly_time_commitment:
            score += 0.3
        elif estimated_time <= preferences.weekly_time_commitment * 1.5:
            score += 0.2
        else:
            score -= 0.1
        
        # Mode preference alignment
        if preferences.mode_preference == "online" and "app" in intervention.resources_needed:
            score += 0.2
        elif preferences.mode_preference == "in_person" and "therapist" in intervention.resources_needed:
            score += 0.2
        
        # Budget alignment
        if preferences.budget_level == "free" and "free" in str(intervention.resources_needed).lower():
            score += 0.2
        elif preferences.budget_level == "low_cost" and "low-cost" in str(intervention.resources_needed).lower():
            score += 0.2
        
        # Evidence base
        if "strong evidence" in intervention.evidence_level.lower():
            score += 0.3
        elif "moderate evidence" in intervention.evidence_level.lower():
            score += 0.2
        
        return min(1.0, max(0.0, score))
    
    def _estimate_intervention_time(self, intervention: Intervention) -> int:
        """Estimate weekly time commitment for an intervention"""
        frequency = intervention.frequency.lower()
        
        if "daily" in frequency:
            if "10-20 minute" in frequency:
                return 2  # 15 minutes average daily
            else:
                return 3  # Default daily estimate
        elif "weekly" in frequency:
            return 2  # Weekly session
        elif "bi-weekly" in frequency:
            return 1  # Bi-weekly
        else:
            return 1  # Default
    
    def _get_intervention_symptoms(self, intervention: Intervention) -> List[str]:
        """Get symptoms that an intervention addresses"""
        # This is a simplified mapping - in practice, this would be more comprehensive
        intervention_name = intervention.name.lower()
        
        if "cbt" in intervention_name:
            return ["depression", "anxiety", "ptsd", "ocd"]
        elif "mindfulness" in intervention_name:
            return ["anxiety", "depression", "stress"]
        elif "sleep" in intervention_name:
            return ["insomnia", "sleep disorders"]
        elif "exercise" in intervention_name:
            return ["depression", "anxiety", "adhd"]
        elif "journaling" in intervention_name:
            return ["depression", "anxiety", "ptsd"]
        else:
            return []
    
    def _get_lifestyle_interventions(self, preferences: PatientPreferences) -> List[Intervention]:
        """Get lifestyle and support interventions"""
        lifestyle_interventions = []
        
        # Exercise therapy
        exercise = self.guidelines.get_intervention_by_name("exercise_therapy")
        if exercise:
            lifestyle_interventions.append(exercise)
        
        # Social support
        social_support = self.guidelines.get_intervention_by_name("social_support")
        if social_support:
            lifestyle_interventions.append(social_support)
        
        # Sleep hygiene
        sleep_hygiene = self.guidelines.get_intervention_by_name("sleep_hygiene")
        if sleep_hygiene:
            lifestyle_interventions.append(sleep_hygiene)
        
        return lifestyle_interventions
    
    def _get_fallback_intervention(self, severity: SymptomSeverity) -> Intervention:
        """Get a safe fallback intervention"""
        if severity == SymptomSeverity.SEVERE:
            return self.guidelines.get_intervention_by_name("psychoeducation")
        else:
            return self.guidelines.get_intervention_by_name("mindfulness_meditation")

    def map_symptoms_to_interventions(
        self,
        symptom_clusters: List[SymptomCluster],
        diagnosis: ProvisionalDiagnosis,
        preferences: PatientPreferences
    ) -> List[Intervention]:
        """Map diagnosis/symptoms to evidence-based interventions"""
        interventions = []
        
        for cluster in symptom_clusters:
            cluster_interventions = self.guidelines.get_evidence_based_interventions(cluster.name)
            interventions.extend(cluster_interventions)
        
        # Remove duplicates
        seen_names = set()
        unique_interventions = []
        for intervention in interventions:
            if intervention.name not in seen_names:
                seen_names.add(intervention.name)
                unique_interventions.append(intervention)
        
        return unique_interventions
    
    def prioritize_interventions(
        self,
        interventions: List[Intervention],
        preferences: PatientPreferences,
        max_count: int = 4
    ) -> List[Intervention]:
        """Prioritize interventions by severity and patient preferences (limit to 3-6 items)"""
        if len(interventions) <= max_count:
            return interventions
        
        # Score interventions based on preferences and evidence
        scored_interventions = []
        for intervention in interventions:
            score = self._score_intervention_for_preferences(intervention, preferences)
            scored_interventions.append((intervention, score))
        
        # Sort by score and return top interventions
        scored_interventions.sort(key=lambda x: x[1], reverse=True)
        return [intervention for intervention, score in scored_interventions[:max_count]]
    
    def decompose_to_micro_tasks(
        self,
        interventions: List[Intervention],
        preferences: PatientPreferences
    ) -> List[Dict[str, Any]]:
        """Decompose interventions into trackable micro-tasks (small, time-boxed steps)"""
        micro_tasks = []
        
        for intervention in interventions:
            if "CBT" in intervention.name:
                micro_tasks.extend(self._create_cbt_micro_tasks(intervention, preferences))
            elif "Mindfulness" in intervention.name:
                micro_tasks.extend(self._create_mindfulness_micro_tasks(intervention, preferences))
            elif "Sleep" in intervention.name:
                micro_tasks.extend(self._create_sleep_micro_tasks(intervention, preferences))
            elif "Exercise" in intervention.name:
                micro_tasks.extend(self._create_exercise_micro_tasks(intervention, preferences))
            else:
                micro_tasks.extend(self._create_generic_micro_tasks(intervention, preferences))
        
        return micro_tasks
    
    def create_plain_english_steps(
        self,
        micro_tasks: List[Dict[str, Any]],
        preferences: PatientPreferences,
        diagnosis: ProvisionalDiagnosis
    ) -> List[Dict[str, Any]]:
        """Create plain-English plan with numbered steps"""
        steps = []
        
        for i, task in enumerate(micro_tasks, 1):
            step = {
                "step_number": i,
                "title": task["title"],
                "description": task["description"],
                "when": task["when"],
                "how_long": task["how_long"],
                "why": task["why"],
                "how_to_track": task["how_to_track"]
            }
            steps.append(step)
        
        return steps
    
    def create_tracking_schema(
        self,
        plan_steps: List[Dict[str, Any]],
        preferences: PatientPreferences
    ) -> 'TrackingSchema':
        """Create tracking schema for patient progress"""
        from .tpa_schemas import TrackingSchema
        
        daily_tasks = ["mood_rating", "task_completed"]
        weekly_summary = ["mood_trend", "adherence_rate", "sleep_quality"]
        progress_rules = [
            "If mean_mood drops by ≥2 points week-over-week OR adherence_rate < 30% for 2 consecutive weeks → flag for clinician review"
        ]
        
        return TrackingSchema(
            daily_tasks=daily_tasks,
            weekly_summary=weekly_summary,
            progress_rules=progress_rules
        )
    
    def create_reminder_schedule(
        self,
        plan_steps: List[Dict[str, Any]],
        preferences: PatientPreferences
    ) -> str:
        """Create reminder schedule for the plan"""
        if preferences.preferred_approach == "self_help":
            return "Daily reminders at 9 AM for daily tasks, weekly reminders for progress review"
        else:
            return "Daily reminders at 9 AM for daily tasks, weekly reminders for therapy sessions"
    
    def create_plan_metadata(
        self,
        plan_steps: List[Dict[str, Any]],
        diagnosis: ProvisionalDiagnosis,
        preferences: PatientPreferences
    ) -> 'PlanMetadata':
        """Create plan metadata"""
        from .tpa_schemas import PlanMetadata
        
        # Determine duration based on severity
        if diagnosis.severity == SymptomSeverity.SEVERE:
            total_duration = "12 weeks"
        elif diagnosis.severity == SymptomSeverity.MODERATE:
            total_duration = "8 weeks"
        else:
            total_duration = "4 weeks"
        
        estimated_time = "15-30 minutes" if preferences.weekly_time_commitment <= 5 else "30-60 minutes"
        frequency = "Daily" if preferences.preferred_approach == "self_help" else "Weekly"
        
        return PlanMetadata(
            total_duration=total_duration,
            total_steps=len(plan_steps),
            estimated_time_per_day=estimated_time,
            frequency=frequency
        )
    
    def _create_cbt_micro_tasks(self, intervention: Intervention, preferences: PatientPreferences) -> List[Dict[str, Any]]:
        """Create micro-tasks for CBT interventions"""
        tasks = []
        
        # Weekly therapy session
        tasks.append({
            "title": "Attend CBT session",
            "description": f"Weekly {intervention.duration} CBT session focusing on {intervention.description.lower()}",
            "when": "Weekly",
            "how_long": intervention.duration,
            "why": "Professional guidance helps you learn and practice new skills effectively",
            "how_to_track": "Mark session as completed and note key insights"
        })
        
        # Daily practice
        tasks.append({
            "title": "Practice CBT techniques",
            "description": "Daily practice of cognitive restructuring and thought challenging",
            "when": "Daily",
            "how_long": "10-15 minutes",
            "why": "Regular practice helps build new thinking patterns",
            "how_to_track": "Complete thought record worksheet and rate mood before/after"
        })
        
        return tasks
    
    def _create_mindfulness_micro_tasks(self, intervention: Intervention, preferences: PatientPreferences) -> List[Dict[str, Any]]:
        """Create micro-tasks for mindfulness interventions"""
        return [{
            "title": "Mindfulness practice",
            "description": f"Daily {intervention.frequency} mindfulness or breathing exercise",
            "when": "Daily",
            "how_long": "10-20 minutes",
            "why": "Regular mindfulness practice reduces stress and improves emotional regulation",
            "how_to_track": "Rate stress level before/after practice (0-10 scale)"
        }]
    
    def _create_sleep_micro_tasks(self, intervention: Intervention, preferences: PatientPreferences) -> List[Dict[str, Any]]:
        """Create micro-tasks for sleep interventions"""
        return [{
            "title": "Sleep routine",
            "description": "Follow consistent bedtime routine and avoid screens before bed",
            "when": "Daily",
            "how_long": "30 minutes",
            "why": "Consistent sleep routine improves sleep quality and mood",
            "how_to_track": "Note bedtime, screen time before bed, and hours slept"
        }]
    
    def _create_exercise_micro_tasks(self, intervention: Intervention, preferences: PatientPreferences) -> List[Dict[str, Any]]:
        """Create micro-tasks for exercise interventions"""
        return [{
            "title": "Physical activity",
            "description": f"Regular physical activity {intervention.frequency}",
            "when": intervention.frequency,
            "how_long": "30-60 minutes",
            "why": "Exercise improves mood, reduces anxiety, and boosts energy",
            "how_to_track": "Log activity type, duration, and mood improvement"
        }]
    
    def _create_generic_micro_tasks(self, intervention: Intervention, preferences: PatientPreferences) -> List[Dict[str, Any]]:
        """Create generic micro-tasks for other interventions"""
        return [{
            "title": intervention.name,
            "description": intervention.description,
            "when": intervention.frequency,
            "how_long": intervention.duration,
            "why": f"Evidence-based intervention for improving mental health",
            "how_to_track": "Mark as completed and note any benefits or challenges"
        }]

    def generate_simple_treatment_plan(
        self,
        primary_intervention: Intervention,
        complementary_interventions: List[Intervention],
        symptom_analysis: Dict[str, Any],
        diagnosis: ProvisionalDiagnosis,
        preferences: PatientPreferences
    ) -> 'SimpleTreatmentPlan':
        """Generate a simple, patient-friendly treatment plan"""
        
        # Create simple condition summary
        condition_summary = self._create_simple_condition_summary(diagnosis, symptom_analysis)
        
        # Create overall goal
        overall_goal = self._create_overall_goal(preferences, diagnosis)
        
        # Generate treatment steps
        treatment_steps = self._create_treatment_steps(
            primary_intervention, 
            complementary_interventions, 
            preferences
        )
        
        # Create progress tracking questions
        progress_questions = self._create_progress_questions(treatment_steps)
        
        # Create simple treatment plan
        simple_plan = SimpleTreatmentPlan(
            patient_id=str(hash(str(preferences.weekly_time_commitment) + preferences.mode_preference)),
            condition_summary=condition_summary,
            overall_goal=overall_goal,
            treatment_steps=treatment_steps,
            tracking_frequency="Daily for first week, then weekly",
            progress_questions=progress_questions,
            reminder_schedule="Daily reminders at 9 AM",
            email_reminders=True,
            when_to_contact_help=self._create_help_guidelines(diagnosis),
            emergency_contacts=self._create_emergency_contacts()
        )
        
        return simple_plan
    
    def _create_simple_condition_summary(self, diagnosis: ProvisionalDiagnosis, symptom_analysis: Dict[str, Any]) -> str:
        """Create simple explanation of the condition"""
        severity = diagnosis.severity.value
        
        if "anxiety" in diagnosis.primary_diagnosis.lower():
            if severity == "mild":
                return "You're experiencing some anxiety that makes daily life a bit challenging, but it's manageable."
            elif severity == "moderate":
                return "You're dealing with anxiety that significantly affects your daily activities and well-being."
            else:
                return "You're experiencing intense anxiety that makes it very difficult to function normally."
        
        elif "depression" in diagnosis.primary_diagnosis.lower():
            if severity == "mild":
                return "You're feeling down and less motivated than usual, but you can still manage daily tasks."
            elif severity == "moderate":
                return "You're experiencing persistent low mood that makes it hard to enjoy life and stay motivated."
            else:
                return "You're dealing with deep sadness and lack of energy that makes daily life very difficult."
        
        elif "insomnia" in diagnosis.primary_diagnosis.lower():
            return "You're having trouble sleeping, which is affecting your energy and mood during the day."
        
        else:
            return f"You're experiencing {diagnosis.primary_diagnosis.lower()} that's affecting your daily life."
    
    def _create_overall_goal(self, preferences: PatientPreferences, diagnosis: ProvisionalDiagnosis) -> str:
        """Create simple overall goal"""
        if "anxiety" in diagnosis.primary_diagnosis.lower():
            return "Feel calmer and more in control of your thoughts and feelings"
        elif "depression" in diagnosis.primary_diagnosis.lower():
            return "Feel more positive and motivated to enjoy life again"
        elif "insomnia" in diagnosis.primary_diagnosis.lower():
            return "Sleep better and feel more rested during the day"
        else:
            return "Feel better and more in control of your mental health"
    
    def _create_treatment_steps(
        self, 
        primary_intervention: Intervention, 
        complementary_interventions: List[Intervention],
        preferences: PatientPreferences
    ) -> List['SimpleTreatmentStep']:
        """Create simple, step-by-step treatment process"""
        
        steps = []
        step_number = 1
        
        # Primary intervention step
        steps.append(self._create_intervention_step(primary_intervention, step_number, "Primary"))
        step_number += 1
        
        # Complementary intervention steps
        for intervention in complementary_interventions[:3]:  # Limit to 3 complementary steps
            steps.append(self._create_intervention_step(intervention, step_number, "Support"))
            step_number += 1
        
        # Add lifestyle and tracking steps
        steps.append(self._create_lifestyle_step(step_number))
        step_number += 1
        
        steps.append(self._create_progress_tracking_step(step_number))
        
        return steps
    
    def _create_intervention_step(self, intervention: Intervention, step_number: int, step_type: str) -> 'SimpleTreatmentStep':
        """Create a simple step for an intervention"""
        
        # Create simple title
        if "CBT" in intervention.name:
            title = "Practice New Thinking Patterns"
            description = "Learn to identify negative thoughts and replace them with more helpful ones"
            tips = [
                "Start with one thought per day",
                "Write down your thoughts in a simple way",
                "Be patient with yourself - this takes practice"
            ]
        elif "Mindfulness" in intervention.name:
            title = "Practice Mindful Breathing"
            description = "Take a few minutes each day to focus on your breath and be present"
            tips = [
                "Start with just 2-3 minutes",
                "Find a quiet spot where you won't be interrupted",
                "Don't worry if your mind wanders - that's normal"
            ]
        elif "Exercise" in intervention.name:
            title = "Move Your Body Daily"
            description = "Do some form of physical activity that you enjoy, even if it's just a short walk"
            tips = [
                "Start with 10-15 minutes",
                "Choose activities you actually like",
                "Don't worry about intensity - movement is movement"
            ]
        elif "Sleep" in intervention.name:
            title = "Create a Better Sleep Routine"
            description = "Set up a consistent bedtime routine to help your body know it's time to sleep"
            tips = [
                "Go to bed at the same time each night",
                "Avoid screens 1 hour before bed",
                "Create a relaxing bedtime ritual"
            ]
        else:
            title = intervention.name
            description = intervention.description
            tips = [
                "Start small and build up gradually",
                "Be consistent with your practice",
                "Celebrate small wins"
            ]
        
        return SimpleTreatmentStep(
            step_number=step_number,
            title=title,
            description=description,
            duration=intervention.duration,
            frequency=intervention.frequency,
            reminder_text=f"Time for your {title.lower()} practice!",
            tracking_question=f"Did you complete your {title.lower()} today?",
            expected_progress=f"After {intervention.duration}, you should notice feeling more {self._get_progress_indicator(intervention)}",
            tips=tips
        )
    
    def _create_lifestyle_step(self, step_number: int) -> 'SimpleTreatmentStep':
        """Create a lifestyle improvement step"""
        
        return SimpleTreatmentStep(
            step_number=step_number,
            title="Take Care of Your Basic Needs",
            description="Make sure you're eating regular meals, staying hydrated, and getting some fresh air each day",
            duration="Ongoing",
            frequency="Daily",
            reminder_text="Remember to take care of your basic needs today!",
            tracking_question="Did you eat regular meals and get some fresh air today?",
            expected_progress="You should feel more stable and grounded when your basic needs are met",
            tips=[
                "Set reminders for meal times",
                "Keep a water bottle nearby",
                "Open a window or step outside for a few minutes"
            ]
        )
    
    def _create_progress_tracking_step(self, step_number: int) -> 'SimpleTreatmentStep':
        """Create a progress tracking step"""
        
        return SimpleTreatmentStep(
            step_number=step_number,
            title="Track Your Progress",
            description="Take a few minutes each week to reflect on how you're feeling and what's working",
            duration="Ongoing",
            frequency="Weekly",
            reminder_text="Time to check in on your progress this week!",
            tracking_question="How are you feeling compared to last week?",
            expected_progress="You should notice gradual improvements in your mood and daily functioning",
            tips=[
                "Use simple rating scales (1-10)",
                "Focus on small improvements",
                "Don't get discouraged by setbacks - they're normal"
            ]
        )
    
    def _get_progress_indicator(self, intervention: Intervention) -> str:
        """Get simple progress indicator for an intervention"""
        if "CBT" in intervention.name:
            return "in control of your thoughts"
        elif "Mindfulness" in intervention.name:
            return "calm and present"
        elif "Exercise" in intervention.name:
            return "energized and positive"
        elif "Sleep" in intervention.name:
            return "rested and refreshed"
        else:
            return "better overall"
    
    def _create_progress_questions(self, treatment_steps: List['SimpleTreatmentStep']) -> List[str]:
        """Create simple progress tracking questions"""
        questions = [
            "How are you feeling today? (1-10 scale)",
            "Did you complete your treatment steps today?",
            "What was the hardest part today?",
            "What went well today?",
            "How confident do you feel about tomorrow? (1-10 scale)"
        ]
        
        # Add step-specific questions
        for step in treatment_steps[:3]:  # Limit to first 3 steps
            questions.append(f"Did you practice {step.title.lower()} today?")
        
        return questions
    
    def _create_help_guidelines(self, diagnosis: ProvisionalDiagnosis) -> List[str]:
        """Create simple guidelines for when to get help"""
        guidelines = [
            "If you're having thoughts of harming yourself",
            "If you're feeling overwhelmed and can't function",
            "If your symptoms are getting worse instead of better",
            "If you're not seeing any improvement after 2 weeks"
        ]
        
        if diagnosis.severity == SymptomSeverity.SEVERE:
            guidelines.insert(0, "If you're experiencing severe symptoms that interfere with daily life")
        
        return guidelines
    
    def _create_emergency_contacts(self) -> List[str]:
        """Create emergency contact information"""
        return [
            "National Suicide Prevention Lifeline: 988 (24/7)",
            "Crisis Text Line: Text HOME to 741741",
            "Emergency Services: 911",
            "Your healthcare provider's emergency number"
        ]

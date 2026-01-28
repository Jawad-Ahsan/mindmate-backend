#!/usr/bin/env python3
"""
Simplified TPA Utility - Easy Treatment Plan Creation and Export

This module provides a simple interface to create and export treatment plans
without the complexity of tracking mechanisms.

Usage:
    from utilize_tpa import TPAUtil

    # Create treatment plan
    tpa = TPAUtil()
    plan = tpa.get_treatment_plan(patient_data)

    # Export to different formats
    tpa.export_plan(plan, format='json')
    tpa.export_plan(plan, format='text')
    tpa.export_plan(plan, format='markdown')
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

# ============================================================================
# MINIMAL SCHEMAS FOR STANDALONE USAGE
# ============================================================================

class SymptomSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"

class TherapyType(str, Enum):
    CBT = "CBT"
    DBT = "DBT"
    ACT = "ACT"
    MINDFULNESS = "Mindfulness"
    PSYCHOEDUCATION = "Psychoeducation"
    JOURNALING = "Journaling"
    SLEEP_HYGIENE = "Sleep Hygiene"
    EXERCISE = "Exercise"
    DIET = "Diet"
    SOCIAL_SUPPORT = "Social Support"
    EXPOSURE_THERAPY = "Exposure Therapy"
    RELAXATION_TECHNIQUES = "Relaxation Techniques"

@dataclass
class PatientDemographics:
    age: int
    gender: str
    occupation: Optional[str] = None
    cultural_background: Optional[str] = None
    living_situation: Optional[str] = None
    support_system: Optional[str] = None

@dataclass
class PatientGoals:
    primary_goals: List[str]
    treatment_preferences: List[str] = None
    previous_treatments: List[str] = None
    success_metrics: Optional[List[str]] = None

    def __post_init__(self):
        if self.treatment_preferences is None:
            self.treatment_preferences = []
        if self.previous_treatments is None:
            self.previous_treatments = []

@dataclass
class SymptomCluster:
    name: str
    severity: SymptomSeverity
    symptoms: List[str]
    triggers: Optional[List[str]] = None
    impact_on_daily_life: Optional[str] = None

@dataclass
class ProvisionalDiagnosis:
    primary_diagnosis: str
    severity: SymptomSeverity
    comorbidities: List[str] = None
    confidence_level: float = 0.8
    risk_factors: List[str] = None

    def __post_init__(self):
        if self.comorbidities is None:
            self.comorbidities = []
        if self.risk_factors is None:
            self.risk_factors = []

@dataclass
class PatientPreferences:
    preferred_approach: str = "self_help"
    weekly_time_commitment: int = 10
    mode_preference: str = "online"
    budget_level: str = "low_cost"
    cultural_considerations: Optional[str] = None

@dataclass
class Intervention:
    name: str
    type: TherapyType
    description: str
    evidence_level: str
    duration: str
    frequency: str
    resources_needed: List[str]
    contraindications: List[str] = None

    def __post_init__(self):
        if self.contraindications is None:
            self.contraindications = []

@dataclass
class TreatmentPlan:
    patient_id: str
    primary_approach: Intervention
    complementary_strategies: List[Intervention]
    self_help_resources: List[Dict[str, str]]
    follow_up_schedule: str
    reassessment_timeline: str
    suggested_specialists: List[Dict[str, str]]
    safety_notes: List[str]
    expected_outcomes: List[str]
    risk_level: str
    escalation_criteria: List[str]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class TPAInput:
    patient_demographics: PatientDemographics
    patient_goals: PatientGoals
    symptom_clusters: List[SymptomCluster]
    provisional_diagnosis: ProvisionalDiagnosis
    patient_preferences: PatientPreferences
    red_flags: List[str] = None

    def __post_init__(self):
        if self.red_flags is None:
            self.red_flags = []

@dataclass
class TPAOutput:
    treatment_plan: TreatmentPlan
    confidence_score: float
    reasoning: str
    alternatives_considered: List[str]
    requires_human_review: bool
    review_reasons: List[str] = None

    def __post_init__(self):
        if self.review_reasons is None:
            self.review_reasons = []

@dataclass
class PlanMetadata:
    total_duration: str
    total_steps: int
    estimated_time_per_day: str
    frequency: str

@dataclass
class TrackingSchema:
    daily_tasks: List[str]
    weekly_summary: List[str]
    progress_rules: List[str]

@dataclass
class TreatmentPlanSimple:
    patient_id: str
    title: str
    goal: str
    top_actions: List[str]
    step_by_step: List[Dict[str, Any]]
    weekly_plan: Dict[str, List[str]]
    safety_note: str
    plan_metadata: PlanMetadata
    tracking_schema: TrackingSchema
    reminder_schedule: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class PatientData:
    """Simple patient data structure for easy TPA usage"""
    # Required fields first (no defaults)
    age: int
    gender: str
    primary_diagnosis: str

    # Optional fields with defaults
    occupation: Optional[str] = None
    cultural_background: Optional[str] = None
    living_situation: Optional[str] = None
    support_system: Optional[str] = None
    severity: str = "moderate"  # mild, moderate, severe
    symptoms: Optional[List[str]] = None
    symptom_clusters: Optional[List[Dict[str, Any]]] = None
    primary_goals: Optional[List[str]] = None
    treatment_preferences: Optional[List[str]] = None
    previous_treatments: Optional[List[str]] = None
    weekly_time_commitment: int = 10  # hours per week
    preferred_approach: str = "self_help"  # self_help, therapy, hybrid
    mode_preference: str = "online"  # online, in_person, hybrid
    budget_level: str = "low_cost"  # free, low_cost, premium
    red_flags: Optional[List[str]] = None

    def __post_init__(self):
        if self.symptoms is None:
            self.symptoms = []
        if self.primary_goals is None:
            self.primary_goals = []
        if self.treatment_preferences is None:
            self.treatment_preferences = []
        if self.previous_treatments is None:
            self.previous_treatments = []
        if self.red_flags is None:
            self.red_flags = []

class TPAUtil:
    """
    Simplified TPA Utility for easy treatment plan creation and export
    """

    def __init__(self):
        """Initialize TPA utility"""
        logger.info("TPA Utility initialized")

    def get_treatment_plan(self, data: Union[PatientData, Dict[str, Any]]) -> TreatmentPlanSimple:
        """
        Create a treatment plan from patient data

        Args:
            data: PatientData object or dictionary with patient information

        Returns:
            TreatmentPlanSimple: Patient-friendly treatment plan
        """
        try:
            # Convert data to PatientData format
            if isinstance(data, dict):
                patient_data = PatientData(**data)
            else:
                patient_data = data

            # Generate treatment plan based on diagnosis
            plan = self._generate_simple_plan(patient_data)

            logger.info(f"Treatment plan created for patient with diagnosis: {patient_data.primary_diagnosis}")
            return plan

        except Exception as e:
            logger.error(f"Error creating treatment plan: {e}")
            raise

    def _generate_simple_plan(self, data: PatientData) -> TreatmentPlanSimple:
        """Generate a simple treatment plan based on patient data"""
        patient_id = f"patient_{data.age}_{data.gender}_{hash(str(data.primary_diagnosis))}"

        # Generate plan components based on diagnosis
        title = self._generate_plan_title(data)
        goal = self._generate_plan_goal(data)
        top_actions = self._generate_top_actions(data)
        step_by_step = self._generate_steps(data)
        weekly_plan = self._generate_weekly_plan(data)
        safety_note = self._generate_safety_note(data)
        plan_metadata = self._generate_plan_metadata(data)
        tracking_schema = self._generate_tracking_schema()
        reminder_schedule = "Daily reminders at 9 AM"

        return TreatmentPlanSimple(
            patient_id=patient_id,
            title=title,
            goal=goal,
            top_actions=top_actions,
            step_by_step=step_by_step,
            weekly_plan=weekly_plan,
            safety_note=safety_note,
            plan_metadata=plan_metadata,
            tracking_schema=tracking_schema,
            reminder_schedule=reminder_schedule
        )

    def _generate_plan_title(self, data: PatientData) -> str:
        """Generate plan title based on diagnosis and severity"""
        severity = data.severity
        diagnosis = data.primary_diagnosis.lower()

        duration = "8-week" if severity == "moderate" else "4-week" if severity == "mild" else "12-week"

        if "anxiety" in diagnosis:
            return f"{duration} plan to reduce anxiety & improve daily life"
        elif "depression" in diagnosis:
            return f"{duration} plan to improve mood & energy"
        elif "insomnia" in diagnosis or "sleep" in diagnosis:
            return f"{duration} plan to improve sleep & rest"
        elif "ptsd" in diagnosis:
            return f"{duration} plan to manage trauma & rebuild safety"
        elif "ocd" in diagnosis:
            return f"{duration} plan to manage obsessions & compulsions"
        else:
            return f"{duration} plan to improve mental health & well-being"

    def _generate_plan_goal(self, data: PatientData) -> str:
        """Generate plan goal"""
        if data.primary_goals:
            return f"Goal: {data.primary_goals[0].lower()}"

        diagnosis = data.primary_diagnosis.lower()
        if "anxiety" in diagnosis:
            return "Goal: Feel calmer and more in control of daily life"
        elif "depression" in diagnosis:
            return "Goal: Feel more positive and motivated to enjoy life"
        elif "insomnia" in diagnosis or "sleep" in diagnosis:
            return "Goal: Sleep better and feel more rested during the day"
        elif "ptsd" in diagnosis:
            return "Goal: Feel safer and more in control of daily life"
        elif "ocd" in diagnosis:
            return "Goal: Reduce obsessions and compulsions to manageable levels"
        else:
            return "Goal: Feel better and more in control of your mental health"

    def _generate_top_actions(self, data: PatientData) -> List[str]:
        """Generate top 3 actions"""
        diagnosis = data.primary_diagnosis.lower()
        actions = []

        if "anxiety" in diagnosis:
            actions = [
                "Daily mindfulness practice (10 minutes) — reduce racing thoughts",
                "Weekly CBT sessions (50 minutes) — learn coping skills",
                "Regular physical activity — reduce physical tension"
            ]
        elif "depression" in diagnosis:
            actions = [
                "Daily mood tracking — monitor progress",
                "Regular physical activity — boost mood naturally",
                "Weekly therapy sessions — learn new coping strategies"
            ]
        elif "insomnia" in diagnosis or "sleep" in diagnosis:
            actions = [
                "Consistent bedtime routine — signal body it's time to sleep",
                "Limit screen time 1 hour before bed — improve sleep quality",
                "Daily morning sunlight exposure — regulate sleep cycle"
            ]
        elif "ptsd" in diagnosis:
            actions = [
                "Grounding exercises daily — stay present in the moment",
                "Weekly trauma-focused therapy — process traumatic experiences",
                "Build safety plan — identify coping strategies"
            ]
        elif "ocd" in diagnosis:
            actions = [
                "Daily exposure practice — face fears gradually",
                "Weekly CBT sessions — learn response prevention",
                "Mindfulness meditation — observe thoughts without judgment"
            ]
        else:
            actions = [
                "Daily self-care routine — build healthy habits",
                "Weekly therapy sessions — get professional support",
                "Regular physical activity — improve overall well-being"
            ]

        return actions[:3]

    def _generate_steps(self, data: PatientData) -> List[Dict[str, Any]]:
        """Generate step-by-step plan"""
        diagnosis = data.primary_diagnosis.lower()
        steps = []

        if "anxiety" in diagnosis:
            steps = [
                {
                    "step_number": 1,
                    "title": "Learn Breathing Techniques",
                    "description": "Practice deep breathing exercises to calm your nervous system",
                    "when": "Daily",
                    "how_long": "5-10 minutes",
                    "why": "Helps reduce physical symptoms of anxiety",
                    "how_to_track": "Rate anxiety before/after (0-10 scale)"
                },
                {
                    "step_number": 2,
                    "title": "Challenge Negative Thoughts",
                    "description": "Identify and replace anxious thoughts with more realistic ones",
                    "when": "Daily",
                    "how_long": "10-15 minutes",
                    "why": "Breaks the cycle of anxious thinking patterns",
                    "how_to_track": "Write down 1-2 thought challenges per day"
                },
                {
                    "step_number": 3,
                    "title": "Build Coping Skills",
                    "description": "Learn specific techniques for managing panic attacks and worry",
                    "when": "As needed",
                    "how_long": "15-20 minutes",
                    "why": "Provides tools to use during difficult moments",
                    "how_to_track": "Note which coping skills work best"
                },
                {
                    "step_number": 4,
                    "title": "Gradual Exposure Practice",
                    "description": "Slowly face feared situations in a controlled way",
                    "when": "Weekly",
                    "how_long": "30-45 minutes",
                    "why": "Reduces avoidance and builds confidence",
                    "how_to_track": "Rate comfort level before/after exposure"
                }
            ]
        elif "depression" in diagnosis:
            steps = [
                {
                    "step_number": 1,
                    "title": "Establish Daily Routine",
                    "description": "Set regular times for waking up, meals, and activities",
                    "when": "Daily",
                    "how_long": "Ongoing",
                    "why": "Structure helps combat depression's disruptive effects",
                    "how_to_track": "Check off completed routine items"
                },
                {
                    "step_number": 2,
                    "title": "Physical Activity",
                    "description": "Engage in light exercise like walking or stretching",
                    "when": "Daily",
                    "how_long": "20-30 minutes",
                    "why": "Exercise releases endorphins and improves mood",
                    "how_to_track": "Note energy level and mood after activity"
                },
                {
                    "step_number": 3,
                    "title": "Pleasant Activities",
                    "description": "Schedule one enjoyable activity each day",
                    "when": "Daily",
                    "how_long": "30-60 minutes",
                    "why": "Counteracts anhedonia and builds positive experiences",
                    "how_to_track": "Rate enjoyment level (0-10)"
                },
                {
                    "step_number": 4,
                    "title": "Social Connection",
                    "description": "Reach out to one friend or family member",
                    "when": "Daily",
                    "how_long": "15-30 minutes",
                    "why": "Combat isolation which worsens depression",
                    "how_to_track": "Note how the interaction made you feel"
                }
            ]
        else:
            # Generic steps for other conditions
            steps = [
                {
                    "step_number": 1,
                    "title": "Daily Self-Care",
                    "description": "Practice basic self-care like regular meals and sleep",
                    "when": "Daily",
                    "how_long": "Ongoing",
                    "why": "Strong foundation for mental health",
                    "how_to_track": "Mark completed self-care items"
                },
                {
                    "step_number": 2,
                    "title": "Skill Building",
                    "description": "Learn and practice coping skills for your condition",
                    "when": "Daily",
                    "how_long": "15-20 minutes",
                    "why": "Builds resilience and coping abilities",
                    "how_to_track": "Note which skills help most"
                },
                {
                    "step_number": 3,
                    "title": "Weekly Review",
                    "description": "Reflect on progress and adjust approach as needed",
                    "when": "Weekly",
                    "how_long": "20 minutes",
                    "why": "Ensures plan remains effective and relevant",
                    "how_to_track": "Write one thing that went well and one to improve"
                }
            ]

        return steps

    def _generate_weekly_plan(self, data: PatientData) -> Dict[str, List[str]]:
        """Generate weekly plan breakdown"""
        return {
            "Week 1": ["Start with basic self-care routine", "Learn first coping skill", "Establish daily practice"],
            "Weeks 2-3": ["Continue daily practice", "Add second coping skill", "Weekly progress check-in"],
            "Weeks 4-6": ["Build on existing skills", "Face more challenging situations", "Regular practice sessions"],
            "Weeks 7-8": ["Consolidate gains", "Plan for maintenance", "Final assessment and next steps"]
        }

    def _generate_safety_note(self, data: PatientData) -> str:
        """Generate safety note"""
        return (
            "If your mood drops quickly or you have thoughts of self-harm, please use the emergency button "
            "or contact local services. If symptoms worsen significantly or you experience suicidal thoughts, "
            "seek immediate professional help. This plan is designed for gradual improvement and should be "
            "monitored by a healthcare professional."
        )

    def _generate_plan_metadata(self, data: PatientData) -> PlanMetadata:
        """Generate plan metadata"""
        severity = data.severity

        if severity == "severe":
            duration = "12 weeks"
            steps = 6
            time_per_day = "30-45 minutes"
        elif severity == "moderate":
            duration = "8 weeks"
            steps = 4
            time_per_day = "20-30 minutes"
        else:
            duration = "4 weeks"
            steps = 3
            time_per_day = "15-20 minutes"

        return PlanMetadata(
            total_duration=duration,
            total_steps=steps,
            estimated_time_per_day=time_per_day,
            frequency="Daily"
        )

    def _generate_tracking_schema(self) -> TrackingSchema:
        """Generate tracking schema"""
        return TrackingSchema(
            daily_tasks=["mood_rating", "practice_completed", "symptom_intensity"],
            weekly_summary=["overall_progress", "challenges_faced", "skills_improved"],
            progress_rules=[
                "If symptoms worsen for 3+ consecutive days, consult healthcare provider",
                "If no improvement after 2 weeks, consider adjusting approach",
                "Celebrate small wins and progress made"
            ]
        )

    def export_plan(self, plan: TreatmentPlanSimple, format: str = 'json', filepath: Optional[str] = None) -> str:
        """
        Export treatment plan to different formats

        Args:
            plan: TreatmentPlanSimple object
            format: Export format ('json', 'text', 'markdown', 'html')
            filepath: Optional file path to save to

        Returns:
            str: Exported plan content
        """
        if format.lower() == 'json':
            return self._export_json(plan, filepath)
        elif format.lower() == 'text':
            return self._export_text(plan, filepath)
        elif format.lower() == 'markdown':
            return self._export_markdown(plan, filepath)
        elif format.lower() == 'html':
            return self._export_html(plan, filepath)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _export_json(self, plan: TreatmentPlanSimple, filepath: Optional[str] = None) -> str:
        """Export plan as JSON"""
        plan_dict = {
            "patient_id": plan.patient_id,
            "title": plan.title,
            "goal": plan.goal,
            "created_at": plan.created_at.isoformat(),
            "top_actions": plan.top_actions,
            "step_by_step": plan.step_by_step,
            "weekly_plan": plan.weekly_plan,
            "safety_note": plan.safety_note,
            "plan_metadata": {
                "total_duration": plan.plan_metadata.total_duration,
                "total_steps": plan.plan_metadata.total_steps,
                "estimated_time_per_day": plan.plan_metadata.estimated_time_per_day,
                "frequency": plan.plan_metadata.frequency
            },
            "reminder_schedule": plan.reminder_schedule
        }

        json_str = json.dumps(plan_dict, indent=2, default=str)

        if filepath:
            with open(filepath, 'w') as f:
                f.write(json_str)
            logger.info(f"Plan exported to {filepath}")

        return json_str

    def _export_text(self, plan: TreatmentPlanSimple, filepath: Optional[str] = None) -> str:
        """Export plan as readable text"""
        lines = [
            "=" * 80,
            plan.title.center(80),
            "=" * 80,
            "",
            f"Goal: {plan.goal}",
            "",
            "TOP ACTIONS:",
            "-" * 20
        ]

        for i, action in enumerate(plan.top_actions, 1):
            lines.append(f"{i}. {action}")

        lines.extend([
            "",
            "STEP-BY-STEP PLAN:",
            "-" * 20
        ])

        for step in plan.step_by_step:
            step_num = step.get('step_number', '')
            title = step.get('title', 'Untitled')
            lines.extend([
                f"\nStep {step_num}: {title}",
                f"When: {step.get('when', 'N/A')}",
                f"How long: {step.get('how_long', 'N/A')}",
                f"Why: {step.get('why', 'N/A')}",
                f"How to track: {step.get('how_to_track', 'N/A')}"
            ])

        lines.extend([
            "",
            "WEEKLY PLAN:",
            "-" * 20
        ])

        for week, activities in plan.weekly_plan.items():
            lines.append(f"\n{week}:")
            for activity in activities:
                lines.append(f"  • {activity}")

        lines.extend([
            "",
            "PLAN DETAILS:",
            "-" * 20,
            f"Duration: {plan.plan_metadata.total_duration}",
            f"Steps: {plan.plan_metadata.total_steps}",
            f"Time per day: {plan.plan_metadata.estimated_time_per_day}",
            f"Frequency: {plan.plan_metadata.frequency}",
            f"Reminders: {plan.reminder_schedule}",
            "",
            "SAFETY NOTE:",
            "-" * 20,
            plan.safety_note,
            "",
            "=" * 80
        ])

        text_content = "\n".join(lines)

        if filepath:
            with open(filepath, 'w') as f:
                f.write(text_content)
            logger.info(f"Plan exported to {filepath}")

        return text_content

    def _export_markdown(self, plan: TreatmentPlanSimple, filepath: Optional[str] = None) -> str:
        """Export plan as Markdown"""
        lines = [
            "# " + plan.title,
            "",
            f"**Goal:** {plan.goal}",
            "",
            "## Top Actions",
            ""
        ]

        for i, action in enumerate(plan.top_actions, 1):
            lines.append(f"{i}. {action}")

        lines.extend([
            "",
            "## Step-by-Step Plan",
            ""
        ])

        for step in plan.step_by_step:
            step_num = step.get('step_number', '')
            title = step.get('title', 'Untitled')
            lines.extend([
                f"### Step {step_num}: {title}",
                f"- **When:** {step.get('when', 'N/A')}",
                f"- **How long:** {step.get('how_long', 'N/A')}",
                f"- **Why:** {step.get('why', 'N/A')}",
                f"- **How to track:** {step.get('how_to_track', 'N/A')}",
                ""
            ])

        lines.extend([
            "## Weekly Plan",
            ""
        ])

        for week, activities in plan.weekly_plan.items():
            lines.append(f"### {week}")
            for activity in activities:
                lines.append(f"- {activity}")
            lines.append("")

        lines.extend([
            "## Plan Details",
            "",
            f"- **Duration:** {plan.plan_metadata.total_duration}",
            f"- **Steps:** {plan.plan_metadata.total_steps}",
            f"- **Time per day:** {plan.plan_metadata.estimated_time_per_day}",
            f"- **Frequency:** {plan.plan_metadata.frequency}",
            f"- **Reminders:** {plan.reminder_schedule}",
            "",
            "## Safety Note",
            "",
            plan.safety_note
        ])

        markdown_content = "\n".join(lines)

        if filepath:
            with open(filepath, 'w') as f:
                f.write(markdown_content)
            logger.info(f"Plan exported to {filepath}")

        return markdown_content

    def _export_html(self, plan: TreatmentPlanSimple, filepath: Optional[str] = None) -> str:
        """Export plan as HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{plan.title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; border-bottom: 2px solid #eee; padding-bottom: 5px; }}
        .step {{ margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }}
        .metadata {{ background: #e8f4fd; padding: 15px; border-radius: 5px; }}
        .safety {{ background: #ffeaa7; padding: 15px; border-radius: 5px; border-left: 4px solid #d63031; }}
    </style>
</head>
<body>
    <h1>{plan.title}</h1>
    <p><strong>Goal:</strong> {plan.goal}</p>

    <h2>Top Actions</h2>
    <ol>
"""

        for action in plan.top_actions:
            html += f"        <li>{action}</li>\n"

        html += """
    </ol>

    <h2>Step-by-Step Plan</h2>
"""

        for step in plan.step_by_step:
            step_num = step.get('step_number', '')
            title = step.get('title', 'Untitled')
            html += f"""
    <div class="step">
        <h3>Step {step_num}: {title}</h3>
        <p><strong>When:</strong> {step.get('when', 'N/A')}</p>
        <p><strong>How long:</strong> {step.get('how_long', 'N/A')}</p>
        <p><strong>Why:</strong> {step.get('why', 'N/A')}</p>
        <p><strong>How to track:</strong> {step.get('how_to_track', 'N/A')}</p>
    </div>
"""

        html += """
    <h2>Weekly Plan</h2>
"""

        for week, activities in plan.weekly_plan.items():
            html += f"    <h3>{week}</h3>\n    <ul>\n"
            for activity in activities:
                html += f"        <li>{activity}</li>\n"
            html += "    </ul>\n"

        html += f"""
    <div class="metadata">
        <h2>Plan Details</h2>
        <p><strong>Duration:</strong> {plan.plan_metadata.total_duration}</p>
        <p><strong>Steps:</strong> {plan.plan_metadata.total_steps}</p>
        <p><strong>Time per day:</strong> {plan.plan_metadata.estimated_time_per_day}</p>
        <p><strong>Frequency:</strong> {plan.plan_metadata.frequency}</p>
        <p><strong>Reminders:</strong> {plan.reminder_schedule}</p>
    </div>

    <div class="safety">
        <h2>Safety Note</h2>
        <p>{plan.safety_note}</p>
    </div>

    <p><small>Generated on: {plan.created_at.strftime('%Y-%m-%d %H:%M:%S')}</small></p>
</body>
</html>
"""

        if filepath:
            with open(filepath, 'w') as f:
                f.write(html)
            logger.info(f"Plan exported to {filepath}")

        return html

    def quick_plan_from_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a treatment plan from dictionary data and return as dictionary

        Args:
            data: Dictionary with patient data

        Returns:
            Dictionary representation of the treatment plan
        """
        plan = self.get_treatment_plan(data)
        return {
            "patient_id": plan.patient_id,
            "title": plan.title,
            "goal": plan.goal,
            "top_actions": plan.top_actions,
            "steps": plan.step_by_step,
            "weekly_plan": plan.weekly_plan,
            "safety_note": plan.safety_note,
            "duration": plan.plan_metadata.total_duration,
            "total_steps": plan.plan_metadata.total_steps,
            "time_per_day": plan.plan_metadata.estimated_time_per_day,
            "frequency": plan.plan_metadata.frequency,
            "reminders": plan.reminder_schedule,
            "created_at": plan.created_at.isoformat()
        }


# Convenience functions
def get_treatment_plan(data: Union[PatientData, Dict[str, Any]]) -> TreatmentPlanSimple:
    """
    Convenience function to create a treatment plan

    Args:
        data: Patient data as PatientData object or dictionary

    Returns:
        TreatmentPlanSimple: Patient-friendly treatment plan
    """
    tpa = TPAUtil()
    return tpa.get_treatment_plan(data)


def export_plan(plan: TreatmentPlanSimple, format: str = 'json', filepath: Optional[str] = None) -> str:
    """
    Convenience function to export a treatment plan

    Args:
        plan: Treatment plan to export
        format: Export format ('json', 'text', 'markdown', 'html')
        filepath: Optional file path to save to

    Returns:
        str: Exported plan content
    """
    tpa = TPAUtil()
    return tpa.export_plan(plan, format, filepath)


# Example usage
if __name__ == "__main__":
    # Example patient data
    patient_data = {
        "age": 32,
        "gender": "female",
        "occupation": "marketing manager",
        "primary_diagnosis": "Generalized Anxiety Disorder",
        "severity": "moderate",
        "symptoms": [
            "frequent panic attacks (2-3 times per week)",
            "constant worry about work and relationships",
            "physical tension and muscle tightness",
            "difficulty concentrating at work",
            "irritability and mood swings"
        ],
        "primary_goals": [
            "Reduce anxiety and panic attacks",
            "Improve sleep quality and reduce insomnia",
            "Better manage work-related stress"
        ],
        "treatment_preferences": ["CBT-based approaches", "Mindfulness and meditation"],
        "weekly_time_commitment": 10,
        "preferred_approach": "self_help",
        "red_flags": []
    }

    # Create treatment plan
    print("Creating treatment plan...")
    tpa = TPAUtil()
    plan = tpa.get_treatment_plan(patient_data)

    # Export in different formats
    print("Exporting plans...")

    # JSON export
    json_plan = tpa.export_plan(plan, 'json')
    print(f"JSON plan length: {len(json_plan)} characters")

    # Text export
    text_plan = tpa.export_plan(plan, 'text')
    print("Text plan preview:")
    print(text_plan[:500] + "...")

    # Markdown export
    markdown_plan = tpa.export_plan(plan, 'markdown')
    print("Markdown plan preview:")
    print(markdown_plan[:300] + "...")

    print("\nTreatment plan created successfully!")
    print(f"Title: {plan.title}")
    print(f"Goal: {plan.goal}")
    print(f"Number of steps: {len(plan.step_by_step)}")
    print(f"Duration: {plan.plan_metadata.total_duration}")

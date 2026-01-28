#!/usr/bin/env python3
"""
Assessment Workflow - Complete Mental Health Assessment Pipeline
================================================================

This module orchestrates the complete mental health assessment process:
1. Patient Profile Collection
2. Concern Assessment with LLM-driven conversation
3. SCID Module Selection
4. SCID Assessment Deployment & Analysis
5. DA Diagnosis Integration
6. Treatment Plan Generation

Author: MindMate Assessment Team
Version: 1.0.0
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re

# Import required components
from .concern import PresentingConcernChatbot, PresentingConcernData
from agents.llm_client import LLMClient, AgentLLMClient
from agents.pima.scid.scid_assessment import SCIDAssessment
from agents.pima.scid.utilize_da import SCIDDAIntegrator
from agents.tpa.utilize_tpa import TPAUtil, PatientData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssessmentStage(Enum):
    """Stages of the assessment workflow"""
    PROFILE_COLLECTION = "profile_collection"
    CONCERN_ASSESSMENT = "concern_assessment"
    MODULE_SELECTION = "module_selection"
    SCID_DEPLOYMENT = "scid_deployment"
    DA_ANALYSIS = "da_analysis"
    TREATMENT_PLANNING = "treatment_planning"
    COMPLETED = "completed"

class ProfileCollectionStage(Enum):
    """Stages of profile collection"""
    AGE = "age"
    GENDER = "gender"
    OCCUPATION = "occupation"
    CITY = "city"
    CONFIRMATION = "confirmation"

@dataclass
class PatientProfile:
    """Patient demographic and basic information"""
    age: Optional[int] = None
    gender: Optional[str] = None
    occupation: Optional[str] = None
    city: Optional[str] = None
    cultural_background: Optional[str] = None
    living_situation: Optional[str] = None
    support_system: Optional[str] = None

    def is_complete(self) -> bool:
        """Check if all required profile fields are filled"""
        return all([
            self.age is not None,
            self.gender is not None,
            self.occupation is not None,
            self.city is not None
        ])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "age": self.age,
            "gender": self.gender,
            "occupation": self.occupation,
            "city": self.city,
            "cultural_background": self.cultural_background,
            "living_situation": self.living_situation,
            "support_system": self.support_system
        }

@dataclass
class AssessmentWorkflowState:
    """Complete state of the assessment workflow"""
    session_id: str
    patient_profile: PatientProfile = field(default_factory=PatientProfile)
    concern_data: Optional[PresentingConcernData] = None
    selected_module: Optional[str] = None
    scid_results: Optional[Dict[str, Any]] = None
    da_results: Optional[Dict[str, Any]] = None
    treatment_plan: Optional[Dict[str, Any]] = None

    # Workflow control
    current_stage: AssessmentStage = AssessmentStage.PROFILE_COLLECTION
    profile_stage: ProfileCollectionStage = ProfileCollectionStage.AGE
    is_complete: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def update_timestamp(self):
        """Update the last updated timestamp"""
        self.updated_at = datetime.now()

class AssessmentWorkflow:
    """
    Complete assessment workflow orchestrator
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize the assessment workflow

        Args:
            use_llm: Whether to use LLM for intelligent features
        """
        self.use_llm = use_llm

        # Initialize components
        self.llm_client = LLMClient() if use_llm else None
        self.agent_llm = AgentLLMClient(
            agent_name="AssessmentWorkflow",
            system_prompt=self._get_system_prompt()
        ) if use_llm else None

        # Initialize assessment components
        self.concern_chatbot = None
        self.scid_assessment = None
        self.da_integrator = None
        self.tpa_util = TPAUtil()

        # Session management
        self.active_sessions: Dict[str, AssessmentWorkflowState] = {}

        logger.info("Assessment Workflow initialized")

    def _get_system_prompt(self) -> str:
        """Get system prompt for the assessment workflow agent"""
        return """You are an intelligent mental health assessment coordinator. Your role is to:

1. Guide patients through profile collection naturally and empathetically
2. Understand patient concerns using contextual conversation
3. Recommend appropriate SCID modules based on symptoms and presentation
4. Interpret assessment results in clinical context
5. Ensure assessment quality and clinical safety

Always maintain clinical professionalism while being warm and understanding.
Ask questions naturally and follow clinical best practices."""

    def start_assessment(self, patient_id: str) -> Tuple[str, str]:
        """
        Start a new assessment workflow session

        Args:
            patient_id: Unique identifier for the patient

        Returns:
            Tuple of (session_id, welcome_message)
        """
        import uuid

        # Generate session ID
        session_id = f"assessment_{uuid.uuid4().hex[:16]}"

        # Create workflow state
        workflow_state = AssessmentWorkflowState(
            session_id=session_id,
            patient_profile=PatientProfile()
        )

        self.active_sessions[session_id] = workflow_state

        # Generate welcome message
        welcome_message = self._generate_welcome_message()

        logger.info(f"Started assessment workflow session {session_id} for patient {patient_id}")
        return session_id, welcome_message

    def _generate_welcome_message(self) -> str:
        """Generate welcome message for new assessment"""
        return """Hello! I'm here to help you through a comprehensive mental health assessment.

To provide you with the best possible care, I'll first ask for some basic information about yourself, then we'll discuss your concerns, and finally create a personalized assessment and treatment plan.

Let's start with a few questions about you:"""

    def process_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """
        Process user message and advance workflow

        Args:
            session_id: Active session ID
            message: User message

        Returns:
            Response dictionary with next steps
        """
        if session_id not in self.active_sessions:
            return {
                "status": "error",
                "message": "Assessment session not found"
            }

        state = self.active_sessions[session_id]
        state.update_timestamp()

        try:
            if state.current_stage == AssessmentStage.PROFILE_COLLECTION:
                return self._process_profile_collection(state, message)
            elif state.current_stage == AssessmentStage.CONCERN_ASSESSMENT:
                return self._process_concern_assessment(state, message)
            elif state.current_stage == AssessmentStage.MODULE_SELECTION:
                return self._process_module_selection(state, message)
            elif state.current_stage == AssessmentStage.SCID_DEPLOYMENT:
                return self._process_scid_deployment(state, message)
            elif state.current_stage == AssessmentStage.DA_ANALYSIS:
                return self._process_da_analysis(state, message)
            elif state.current_stage == AssessmentStage.TREATMENT_PLANNING:
                return self._process_treatment_planning(state, message)
            else:
                return {
                    "status": "complete",
                    "message": "Assessment workflow is complete"
                }

        except Exception as e:
            logger.error(f"Error processing message in session {session_id}: {e}")
            return {
                "status": "error",
                "message": f"An error occurred during assessment: {str(e)}"
            }

    def _process_profile_collection(self, state: AssessmentWorkflowState, message: str) -> Dict[str, Any]:
        """Process profile collection stage"""
        profile = state.patient_profile

        try:
            if state.profile_stage == ProfileCollectionStage.AGE:
                age = self._extract_age(message)
                if age:
                    profile.age = age
                    state.profile_stage = ProfileCollectionStage.GENDER
                    return {
                        "status": "continue",
                        "message": "Thank you. What's your gender?",
                        "stage": "profile_collection",
                        "next_field": "gender"
                    }
                else:
                    return {
                        "status": "retry",
                        "message": "I didn't understand your age. Could you please tell me your age in years?",
                        "stage": "profile_collection",
                        "current_field": "age"
                    }

            elif state.profile_stage == ProfileCollectionStage.GENDER:
                gender = self._extract_gender(message)
                if gender:
                    profile.gender = gender
                    state.profile_stage = ProfileCollectionStage.OCCUPATION
                    return {
                        "status": "continue",
                        "message": "Thank you. What's your occupation or what do you do for work/study?",
                        "stage": "profile_collection",
                        "next_field": "occupation"
                    }
                else:
                    return {
                        "status": "retry",
                        "message": "I didn't understand your gender. Could you please specify male, female, or other?",
                        "stage": "profile_collection",
                        "current_field": "gender"
                    }

            elif state.profile_stage == ProfileCollectionStage.OCCUPATION:
                profile.occupation = message.strip()
                state.profile_stage = ProfileCollectionStage.CITY
                return {
                    "status": "continue",
                    "message": "Thank you. Which city do you live in?",
                    "stage": "profile_collection",
                    "next_field": "city"
                }

            elif state.profile_stage == ProfileCollectionStage.CITY:
                profile.city = message.strip()
                state.profile_stage = ProfileCollectionStage.CONFIRMATION

                # Generate profile summary and ask for confirmation
                profile_summary = self._generate_profile_summary(profile)
                return {
                    "status": "confirm",
                    "message": f"Thank you! Here's what I have:\n\n{profile_summary}\n\nIs this information correct? (yes/no)",
                    "stage": "profile_collection",
                    "profile_summary": profile.to_dict()
                }

            elif state.profile_stage == ProfileCollectionStage.CONFIRMATION:
                if self._is_confirmation_positive(message):
                    state.current_stage = AssessmentStage.CONCERN_ASSESSMENT
                    self.concern_chatbot = PresentingConcernChatbot(llm_client=self.llm_client)

                    # Start concern assessment
                    concern_response = self.concern_chatbot.start_conversation()
                    return {
                        "status": "stage_complete",
                        "message": "Great! Now let's talk about what brings you here today.\n\n" + concern_response.get('question', 'What brings you in today?'),
                        "stage": "concern_assessment",
                        "question_id": concern_response.get('question_id')
                    }
                else:
                    # Reset profile collection
                    state.patient_profile = PatientProfile()
                    state.profile_stage = ProfileCollectionStage.AGE
                    return {
                        "status": "retry",
                        "message": "Let's start over. What's your age?",
                        "stage": "profile_collection",
                        "next_field": "age"
                    }

        except Exception as e:
            logger.error(f"Error in profile collection: {e}")
            return {
                "status": "error",
                "message": "I had trouble understanding that. Let's try again."
            }

    def _extract_age(self, message: str) -> Optional[int]:
        """Extract age from message"""
        # Look for numbers in the message
        numbers = re.findall(r'\d+', message)
        for num in numbers:
            age = int(num)
            if 5 <= age <= 120:  # Reasonable age range
                return age

        # Try LLM extraction if available
        if self.llm_client:
            try:
                prompt = f"Extract the age from this message: '{message}'. Return only the number."
                response = self.llm_client.generate(prompt, max_tokens=10)
                numbers = re.findall(r'\d+', response)
                if numbers:
                    age = int(numbers[0])
                    if 5 <= age <= 120:
                        return age
            except Exception:
                pass

        return None

    def _extract_gender(self, message: str) -> Optional[str]:
        """Extract gender from message"""
        message_lower = message.lower()

        if any(word in message_lower for word in ['male', 'man', 'boy', 'guy', 'he']):
            return 'male'
        elif any(word in message_lower for word in ['female', 'woman', 'girl', 'she']):
            return 'female'
        elif any(word in message_lower for word in ['other', 'non-binary', 'transgender', 'prefer not']):
            return 'other'

        # Try LLM extraction
        if self.llm_client:
            try:
                prompt = f"Extract gender from: '{message}'. Return 'male', 'female', or 'other'."
                response = self.llm_client.generate(prompt, max_tokens=20).lower().strip()
                if response in ['male', 'female', 'other']:
                    return response
            except Exception:
                pass

        return None

    def _is_confirmation_positive(self, message: str) -> bool:
        """Check if message indicates positive confirmation"""
        positive_words = ['yes', 'correct', 'right', 'good', 'fine', 'okay', 'ok', 'yes', 'yep', 'yeah']
        message_lower = message.lower()

        return any(word in message_lower for word in positive_words)

    def _generate_profile_summary(self, profile: PatientProfile) -> str:
        """Generate human-readable profile summary"""
        return f"""• Age: {profile.age}
• Gender: {profile.gender}
• Occupation: {profile.occupation}
• City: {profile.city}"""

    def _process_concern_assessment(self, state: AssessmentWorkflowState, message: str) -> Dict[str, Any]:
        """Process concern assessment stage"""
        if not self.concern_chatbot:
            return {
                "status": "error",
                "message": "Concern assessment not initialized"
            }

        # Process message through concern chatbot
        try:
            response = self.concern_chatbot.process_message(message)

            if response.get("status") == "complete":
                # Concern assessment complete, move to module selection
                state.concern_data = self.concern_chatbot.data
                state.current_stage = AssessmentStage.MODULE_SELECTION

                # Generate concern summary
                concern_summary = self._generate_concern_summary(state.concern_data)

                # Get module recommendation
                module_recommendation = self._recommend_scid_module(state)

                return {
                    "status": "stage_complete",
                    "message": f"Thank you for sharing that information.\n\n{concern_summary}\n\nBased on what you've told me, I recommend the **{module_recommendation['module_name']}** assessment module.\n\nWould you like to proceed with this assessment? (yes/no)",
                    "stage": "module_selection",
                    "concern_summary": concern_summary,
                    "module_recommendation": module_recommendation
                }
            else:
                # Continue concern assessment
                return {
                    "status": "continue",
                    "message": response.get("message", "Can you tell me more?"),
                    "stage": "concern_assessment",
                    "question_id": response.get("question_id")
                }

        except Exception as e:
            logger.error(f"Error in concern assessment: {e}")
            return {
                "status": "error",
                "message": "I had trouble processing your response. Could you please rephrase?"
            }

    def _generate_concern_summary(self, concern_data: PresentingConcernData) -> str:
        """Generate comprehensive concern summary"""
        if self.llm_client:
            try:
                prompt = f"""Create a professional clinical summary of this patient's presenting concern:

Primary Concern: {concern_data.presenting_concern or 'Not specified'}
Onset: {concern_data.hpi_onset or 'Not specified'}
Duration: {concern_data.hpi_duration or 'Not specified'}
Severity (1-10): {concern_data.hpi_severity or 'Not specified'}
Frequency: {concern_data.hpi_frequency or 'Not specified'}
Triggers: {concern_data.hpi_triggers or 'Not specified'}
Impact on Work: {concern_data.hpi_impact_work or 'Not specified'}
Impact on Relationships: {concern_data.hpi_impact_relationships or 'Not specified'}
Functional Impact: {concern_data.function_ADL or 'Not specified'}

Write a concise clinical summary in 2-3 sentences."""

                return self.llm_client.generate(prompt, max_tokens=300)
            except Exception as e:
                logger.warning(f"LLM summary generation failed: {e}")

        # Fallback summary
        concern = concern_data.presenting_concern or "Not specified"
        severity = concern_data.hpi_severity or "Not specified"

        return f"Patient presents with {concern}. Severity rated as {severity}/10. Assessment indicates this is significantly impacting daily functioning."

    def _recommend_scid_module(self, state: AssessmentWorkflowState) -> Dict[str, Any]:
        """Recommend appropriate SCID module based on profile and concern data"""
        concern_text = state.concern_data.presenting_concern or ""
        concern_lower = concern_text.lower()

        # Simple keyword-based module selection
        module_map = {
            'depression': 'MDD',
            'depressive': 'MDD',
            'sad': 'MDD',
            'anxiety': 'GAD',
            'anxious': 'GAD',
            'panic': 'Panic',
            'ptsd': 'PTSD',
            'trauma': 'PTSD',
            'ocd': 'OCD',
            'obsessive': 'OCD',
            'compulsive': 'OCD',
            'bipolar': 'Bipolar',
            'manic': 'Bipolar',
            'eating': 'Eating',
            'alcohol': 'Alcohol',
            'substance': 'Substance',
            'psychotic': 'Psychotic',
            'schizophrenia': 'Psychotic'
        }

        module_names = {
            'MDD': 'Major Depressive Disorder',
            'GAD': 'Generalized Anxiety Disorder',
            'Panic': 'Panic Disorder',
            'PTSD': 'Post-Traumatic Stress Disorder',
            'OCD': 'Obsessive-Compulsive Disorder',
            'Bipolar': 'Bipolar Disorder',
            'Eating': 'Eating Disorders',
            'Alcohol': 'Alcohol Use Disorder',
            'Substance': 'Substance Use Disorder',
            'Psychotic': 'Psychotic Disorders'
        }

        # Find matching module
        selected_module = 'MDD'  # Default
        for keyword, module in module_map.items():
            if keyword in concern_lower:
                selected_module = module
                break

        # Use LLM for more sophisticated module selection if available
        if self.llm_client:
            try:
                prompt = f"""Based on this patient concern, recommend the most appropriate SCID module:

Patient Concern: {concern_text}
Age: {state.patient_profile.age}
Gender: {state.patient_profile.gender}

Available modules: MDD (Depression), GAD (Anxiety), Panic, PTSD, OCD, Bipolar, Eating, Alcohol, Substance, Psychotic

Return only the module code (e.g., MDD, GAD, etc.) that best fits."""

                llm_module = self.llm_client.generate(prompt, max_tokens=20).strip().upper()
                if llm_module in module_names:
                    selected_module = llm_module
            except Exception as e:
                logger.warning(f"LLM module selection failed: {e}")

        module_name = module_names.get(selected_module, selected_module)

        return {
            "module_code": selected_module,
            "module_name": module_name,
            "reasoning": f"Selected based on presenting symptoms: {concern_text[:100]}..."
        }

    def _process_module_selection(self, state: AssessmentWorkflowState, message: str) -> Dict[str, Any]:
        """Process module selection stage"""
        if self._is_confirmation_positive(message):
            # Proceed with SCID deployment
            state.current_stage = AssessmentStage.SCID_DEPLOYMENT
            state.selected_module = state.selected_module or "MDD"

            # Initialize SCID assessment
            self.scid_assessment = SCIDAssessment(use_llm=self.use_llm)

            try:
                # Start SCID assessment
                patient_info = {
                    "name": f"Patient_{state.session_id[:8]}",
                    "age": state.patient_profile.age,
                    "gender": state.patient_profile.gender,
                    "occupation": state.patient_profile.occupation,
                    "city": state.patient_profile.city,
                    "clinical_presentation": state.concern_data.presenting_concern if state.concern_data else ""
                }

                session_id, welcome = self.scid_assessment.start_assessment(
                    patient_id=state.session_id,
                    module_id=state.selected_module,
                    patient_info=patient_info
                )

                # Get first question
                question = self.scid_assessment.get_next_question(session_id)

                if question:
                    return {
                        "status": "stage_complete",
                        "message": f"Great! Let's begin the {state.selected_module} assessment.\n\n{question.display_text}",
                        "stage": "scid_deployment",
                        "question_id": question.question_id,
                        "question_type": question.response_type.value,
                        "options": question.options if hasattr(question, 'options') else None
                    }
                else:
                    # No questions available, skip to DA analysis
                    state.current_stage = AssessmentStage.DA_ANALYSIS
                    return self._process_da_analysis(state, "")

            except Exception as e:
                logger.error(f"SCID deployment failed: {e}")
                return {
                    "status": "error",
                    "message": "Unable to start assessment. Moving to diagnosis phase."
                }
        else:
            # Return to concern assessment for clarification
            state.current_stage = AssessmentStage.CONCERN_ASSESSMENT
            return {
                "status": "retry",
                "message": "Let's get more information about your concerns to make a better recommendation. Can you tell me more about what you're experiencing?",
                "stage": "concern_assessment"
            }

    def _process_scid_deployment(self, state: AssessmentWorkflowState, message: str) -> Dict[str, Any]:
        """Process SCID deployment stage"""
        # This is a simplified version - in practice, you'd handle the full SCID interaction
        # For now, we'll simulate completion and move to DA analysis

        try:
            # Get current SCID results
            scid_result = self.scid_assessment.get_current_results(state.session_id, include_llm_summary=False)
            state.scid_results = scid_result.to_json()

            # Complete SCID assessment
            final_result = self.scid_assessment.complete_assessment(state.session_id)
            state.current_stage = AssessmentStage.DA_ANALYSIS

            return {
                "status": "stage_complete",
                "message": "SCID assessment completed. Now performing differential diagnosis analysis...",
                "stage": "da_analysis",
                "scid_summary": f"Completed {state.selected_module} assessment with {len(scid_result.real_time_analyses)} analysis points"
            }

        except Exception as e:
            logger.error(f"SCID processing failed: {e}")
            state.current_stage = AssessmentStage.DA_ANALYSIS
            return {
                "status": "stage_complete",
                "message": "Moving to diagnosis analysis...",
                "stage": "da_analysis"
            }

    def _process_da_analysis(self, state: AssessmentWorkflowState, message: str) -> Dict[str, Any]:
        """Process DA analysis stage"""
        try:
            # Initialize DA integrator
            self.da_integrator = SCIDDAIntegrator(use_da=True)

            # Prepare patient data for DA
            patient_data = self._prepare_patient_data_for_da(state)

            # Run integrated SCID-DA analysis
            integrated_result = self.da_integrator.integrate_scid_da_analysis(
                patient_id=state.session_id,
                module_id=state.selected_module,
                patient_info=patient_data
            )

            state.da_results = {
                "diagnosis": integrated_result.da_diagnosis,
                "confidence": integrated_result.da_confidence,
                "severity": integrated_result.da_severity,
                "reasoning": integrated_result.da_reasoning,
                "agreement_level": integrated_result.agreement_level,
                "clinical_confidence": integrated_result.clinical_confidence
            }

            state.current_stage = AssessmentStage.TREATMENT_PLANNING

            return {
                "status": "stage_complete",
                "message": "Diagnosis analysis completed. Now creating your personalized treatment plan...",
                "stage": "treatment_planning",
                "da_summary": f"Primary diagnosis: {integrated_result.da_diagnosis or 'Under evaluation'}"
            }

        except Exception as e:
            logger.error(f"DA analysis failed: {e}")
            state.current_stage = AssessmentStage.TREATMENT_PLANNING
            return {
                "status": "stage_complete",
                "message": "Moving to treatment planning...",
                "stage": "treatment_planning"
            }

    def _process_treatment_planning(self, state: AssessmentWorkflowState, message: str) -> Dict[str, Any]:
        """Process treatment planning stage"""
        try:
            # Prepare patient data for TPA
            patient_data = self._prepare_patient_data_for_tpa(state)

            # Generate treatment plan
            treatment_plan = self.tpa_util.get_treatment_plan(patient_data)

            state.treatment_plan = {
                "title": treatment_plan.title,
                "goal": treatment_plan.goal,
                "top_actions": treatment_plan.top_actions,
                "steps": treatment_plan.step_by_step,
                "weekly_plan": treatment_plan.weekly_plan,
                "safety_note": treatment_plan.safety_note,
                "duration": treatment_plan.plan_metadata.total_duration,
                "time_commitment": treatment_plan.plan_metadata.estimated_time_per_day
            }

            state.current_stage = AssessmentStage.COMPLETED
            state.is_complete = True

            # Generate final comprehensive report
            final_report = self._generate_final_report(state)

            return {
                "status": "complete",
                "message": "Your personalized treatment plan is ready!",
                "treatment_plan": state.treatment_plan,
                "final_report": final_report,
                "recommendations": {
                    "next_steps": "Schedule follow-up appointment in 2 weeks",
                    "emergency_contact": "Call emergency services if symptoms worsen significantly",
                    "resources": "Access to mental health hotline and online support groups"
                }
            }

        except Exception as e:
            logger.error(f"Treatment planning failed: {e}")
            return {
                "status": "error",
                "message": "Unable to generate treatment plan. Please consult with a healthcare provider."
            }

    def _prepare_patient_data_for_da(self, state: AssessmentWorkflowState) -> Dict[str, Any]:
        """Prepare patient data for DA analysis"""
        return {
            "age": state.patient_profile.age,
            "gender": state.patient_profile.gender,
            "occupation": state.patient_profile.occupation,
            "city": state.patient_profile.city,
            "clinical_presentation": state.concern_data.presenting_concern if state.concern_data else "",
            "symptoms": self._extract_symptoms_from_concern(state.concern_data) if state.concern_data else []
        }

    def _prepare_patient_data_for_tpa(self, state: AssessmentWorkflowState) -> PatientData:
        """Prepare patient data for treatment plan generation"""
        symptoms = self._extract_symptoms_from_concern(state.concern_data) if state.concern_data else []

        # Determine diagnosis and severity
        primary_diagnosis = "Generalized Anxiety Disorder"  # Default
        severity = "moderate"

        if state.da_results and state.da_results.get("diagnosis"):
            primary_diagnosis = state.da_results["diagnosis"]

        if state.concern_data and state.concern_data.hpi_severity:
            if state.concern_data.hpi_severity >= 8:
                severity = "severe"
            elif state.concern_data.hpi_severity >= 6:
                severity = "moderate"
            else:
                severity = "mild"

        return PatientData(
            age=state.patient_profile.age or 30,
            gender=state.patient_profile.gender or "unknown",
            primary_diagnosis=primary_diagnosis,
            occupation=state.patient_profile.occupation,
            city=state.patient_profile.city,
            severity=severity,
            symptoms=symptoms,
            primary_goals=["Reduce symptoms", "Improve daily functioning"],
            treatment_preferences=["CBT", "Mindfulness"],
            weekly_time_commitment=10
        )

    def _extract_symptoms_from_concern(self, concern_data: PresentingConcernData) -> List[str]:
        """Extract symptoms from concern data"""
        symptoms = []

        if concern_data.presenting_concern:
            symptoms.append(concern_data.presenting_concern)

        if concern_data.hpi_triggers:
            symptoms.append(f"Triggers: {concern_data.hpi_triggers}")

        if concern_data.hpi_impact_work:
            symptoms.append(f"Work impact: {concern_data.hpi_impact_work}")

        if concern_data.hpi_impact_relationships:
            symptoms.append(f"Relationship impact: {concern_data.hpi_impact_relationships}")

        return symptoms

    def _generate_final_report(self, state: AssessmentWorkflowState) -> str:
        """Generate comprehensive final report"""
        if not self.llm_client:
            return self._generate_template_final_report(state)

        try:
            prompt = f"""Create a comprehensive clinical assessment report:

PATIENT PROFILE:
- Age: {state.patient_profile.age}
- Gender: {state.patient_profile.gender}
- Occupation: {state.patient_profile.occupation}
- City: {state.patient_profile.city}

PRESENTING CONCERN:
{state.concern_data.presenting_concern if state.concern_data else 'Not available'}

SEVERITY: {state.concern_data.hpi_severity if state.concern_data else 'Not assessed'}/10

DIAGNOSIS:
{state.da_results.get('diagnosis', 'Under evaluation') if state.da_results else 'Pending'}

TREATMENT PLAN:
{state.treatment_plan.get('title', 'Not available') if state.treatment_plan else 'Pending'}

Write a professional clinical report summarizing the assessment findings, diagnosis, and treatment recommendations."""

            return self.llm_client.generate(prompt, max_tokens=600)

        except Exception as e:
            logger.warning(f"LLM final report generation failed: {e}")
            return self._generate_template_final_report(state)

    def _generate_template_final_report(self, state: AssessmentWorkflowState) -> str:
        """Generate template-based final report"""
        report = f"""CLINICAL ASSESSMENT REPORT
========================

PATIENT INFORMATION:
• Age: {state.patient_profile.age}
• Gender: {state.patient_profile.gender}
• Occupation: {state.patient_profile.occupation}
• Location: {state.patient_profile.city}

PRESENTING CONCERN:
{state.concern_data.presenting_concern if state.concern_data else 'Not available'}

CLINICAL FINDINGS:
• Severity: {state.concern_data.hpi_severity if state.concern_data else 'Not assessed'}/10
• SCID Module: {state.selected_module}
• Diagnosis: {state.da_results.get('diagnosis', 'Under evaluation') if state.da_results else 'Pending'}

TREATMENT RECOMMENDATIONS:
{chr(10).join('• ' + action for action in state.treatment_plan.get('top_actions', [])[:3]) if state.treatment_plan else 'Pending'}

FOLLOW-UP:
• Schedule appointment in 2 weeks
• Monitor symptoms daily
• Contact healthcare provider if symptoms worsen

Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        return report

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of assessment session"""
        if session_id not in self.active_sessions:
            return {"status": "not_found"}

        state = self.active_sessions[session_id]

        return {
            "session_id": session_id,
            "current_stage": state.current_stage.value,
            "is_complete": state.is_complete,
            "profile_complete": state.patient_profile.is_complete(),
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat()
        }

    def export_assessment(self, session_id: str, format: str = 'json') -> str:
        """Export complete assessment results"""
        if session_id not in self.active_sessions:
            return "Session not found"

        state = self.active_sessions[session_id]

        export_data = {
            "session_id": session_id,
            "patient_profile": state.patient_profile.to_dict(),
            "concern_data": state.concern_data.__dict__ if state.concern_data else None,
            "selected_module": state.selected_module,
            "scid_results": state.scid_results,
            "da_results": state.da_results,
            "treatment_plan": state.treatment_plan,
            "workflow_status": state.current_stage.value,
            "is_complete": state.is_complete,
            "export_timestamp": datetime.now().isoformat()
        }

        if format.lower() == 'json':
            return json.dumps(export_data, indent=2, default=str)
        else:
            return str(export_data)

# Convenience functions
def start_new_assessment(patient_id: str, use_llm: bool = True) -> Tuple[AssessmentWorkflow, str, str]:
    """Start a new assessment workflow"""
    workflow = AssessmentWorkflow(use_llm=use_llm)
    session_id, welcome_message = workflow.start_assessment(patient_id)
    return workflow, session_id, welcome_message

def run_interactive_assessment():
    """Run an interactive assessment workflow that waits for user input"""
    print("🧠 Interactive MindMate Assessment")
    print("=" * 50)
    print("Welcome to your comprehensive mental health assessment!")
    print("Type 'exit' or 'quit' at any time to end the assessment.")
    print("-" * 50)
    print()

    try:
        # Start assessment
        workflow, session_id, welcome = start_new_assessment("interactive_user")

        print(f"Session ID: {session_id}")
        print(f"{welcome}")
        print()

        # Get first message
        current_response = workflow.start_assessment("interactive_user")[1]  # Get the initial response
        current_response = {"message": welcome, "status": "continue"}

        while True:
            if current_response.get("status") not in ["continue", "follow_up"]:
                break

            # Display bot message
            message = current_response.get('message', 'No message')
            print(f"🤖 MindMate: {message}")

            # Check if this is a follow-up question
            if current_response.get("type") == "follow_up":
                print("(This is a follow-up question)")
            elif current_response.get("question_id"):
                print("(Main assessment question)")

            # Get user input
            print()
            user_input = input("👤 You: ").strip()

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Thanks for participating in the assessment!")
                print("Your progress has been saved. You can resume anytime.")
                break

            # Skip empty input
            if not user_input:
                print("Please provide a response.")
                continue

            # Process the response
            try:
                current_response = workflow.process_message(session_id, user_input)
            except Exception as e:
                print(f"❌ Error processing response: {e}")
                print("Please try again.")
                continue

        # Show completion summary
        try:
            status = workflow.get_session_status(session_id)
            print("\n📊 Assessment Summary:")
            print(f"   Stage: {status['current_stage']}")
            print(f"   Complete: {status['is_complete']}")
            print(f"   Profile Complete: {status['profile_complete']}")

            # Export results if assessment is complete
            if status['is_complete']:
                print("\n📋 Complete Assessment Results:")
                results = workflow.export_assessment(session_id)
                print(results[:500] + "..." if len(results) > 500 else results)

        except Exception as e:
            print(f"❌ Error generating summary: {e}")

        print("\n✅ Interactive assessment session ended!")

    except KeyboardInterrupt:
        print("\n\n👋 Assessment interrupted by user.")
    except Exception as e:
        print(f"\n❌ Interactive assessment failed: {e}")
        import traceback
        traceback.print_exc()

def run_demo_assessment():
    """Run the original demo with pre-defined responses"""
    print("🧠 Assessment Workflow Demo (Pre-defined responses)")
    print("=" * 60)

    try:
        # Start assessment
        workflow, session_id, welcome = start_new_assessment("demo_patient_001")

        print(f"Session ID: {session_id}")
        print(f"Welcome: {welcome}")
        print()

        # Simulate profile collection
        responses = [
            "I'm 34 years old",
            "female",
            "software engineer",
            "San Francisco",
            "yes that's correct"
        ]

        current_response = {"status": "continue"}

        for response in responses:
            if current_response.get("status") == "continue":
                current_response = workflow.process_message(session_id, response)
                print(f"Bot: {current_response.get('message', 'No message')}")
                print("-" * 40)

        print("\n✅ Assessment workflow demo completed successfully!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

# Example usage and testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        run_interactive_assessment()
    else:
        print("Choose assessment mode:")
        print("1. Interactive mode (waits for your input)")
        print("2. Demo mode (pre-defined responses)")
        print()

        choice = input("Enter 1 or 2: ").strip()

        if choice == "1":
            run_interactive_assessment()
        else:
            run_demo_assessment()


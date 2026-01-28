"""
SCID Module Deployer Tool
Professional deployment system for SCID-CV and SCID-PD modules
Supports interactive administration with proper formatting and validation
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re

# Import real SCID components
try:
    # Import SCID-CV components
    from .scid_cv import (
        MODULE_REGISTRY,
        get_all_modules,
        get_module
    )
    from .scid_cv.base_types import (
        SCIDModule,
        SCIDQuestion,
        ResponseType,
        SCIDResponse,
        ModuleResult
    )
    from .scid_cv.utils import SCIDAdministrator

    # Import SCID-PD components
    from .scid_pd import (
        get_all_pd_modules,
        get_pd_module
    )
    from .scid_pd.base_types import (
        SCIDPDModule,
        SCIDPDQuestion,
        SCIDPDResponse,
        PersonalityProfile,
        PersonalityModuleResult
    )
    from .scid_pd.utils import SCIDPDAdministrator
    
    print("✅ Successfully imported real SCID modules")
    
except ImportError as e:
    print(f"❌ Error importing SCID modules: {e}")
    print("Please ensure the SCID modules are properly installed and accessible")
    raise

logger = logging.getLogger(__name__)

class DeploymentMode(Enum):
    """Modes of module deployment"""
    INTERACTIVE = "interactive"  # One question at a time
    BATCH = "batch"              # All questions at once
    HYBRID = "hybrid"           # Mix of both

class ResponseValidationError(Exception):
    """Raised when a response fails validation"""
    pass

@dataclass
class DeploymentSession:
    """Tracks the state of a module deployment session"""
    session_id: str
    module_id: str
    module_name: str
    patient_info: Dict[str, Any] = field(default_factory=dict)
    current_question_index: int = 0
    responses: Dict[str, Any] = field(default_factory=dict)
    free_text_responses: Dict[str, str] = field(default_factory=dict)  # Store free text responses separately
    response_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Store response metadata
    question_history: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    status: str = "initialized"  # initialized, in_progress, completed, paused
    skip_logic_applied: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)

    def update_activity(self):
        """Update the last activity timestamp"""
        self.last_activity = datetime.now()

    def add_response(self, question_id: str, response: Any, free_text: str = None, metadata: Dict[str, Any] = None):
        """Add a response and update activity"""
        self.responses[question_id] = response
        
        # Store free text if provided
        if free_text:
            self.free_text_responses[question_id] = free_text
        
        # Store metadata if provided
        if metadata:
            self.response_metadata[question_id] = metadata
        
        self.update_activity()

    def get_completion_percentage(self, total_questions: int) -> float:
        """Get completion percentage"""
        return (len(self.responses) / total_questions) * 100 if total_questions > 0 else 0

@dataclass
class ProfessionalQuestion:
    """Professional formatting for a question"""
    question_id: str
    display_text: str
    response_type: ResponseType
    options: List[str] = field(default_factory=list)
    scale_range: Tuple[int, int] = (0, 3)
    scale_labels: List[str] = field(default_factory=list)
    help_text: str = ""
    examples: List[str] = field(default_factory=list)
    required: bool = True
    question_number: int = 0
    total_questions: int = 0

class ModuleDeployer:
    """
    Professional SCID Module Deployment System

    Features:
    - Interactive question-by-question administration
    - Professional formatting and guidance
    - Response validation and error handling
    - Skip logic support
    - Session management and resumability
    - Integration with existing SCID administrators
    - Support for both SCID-CV and SCID-PD modules
    """

    def __init__(self, use_llm: bool = False):
        """
        Initialize the module deployer

        Args:
            use_llm: Whether to use LLM for intelligent module selection
        """
        self.use_llm = use_llm
        self.cv_modules = self._load_cv_modules()
        self.pd_modules = self._load_pd_modules()
        self.cv_administrator = SCIDAdministrator()
        self.pd_administrator = SCIDPDAdministrator()
        self.module_selector = None  # Module selector not available in current implementation
        self.active_sessions: Dict[str, DeploymentSession] = {}
        self.session_counter = 0

        logger.info(f"ModuleDeployer initialized with {len(self.cv_modules)} CV modules and {len(self.pd_modules)} PD modules")

    def _load_cv_modules(self) -> Dict[str, SCIDModule]:
        """Load all available SCID-CV modules"""
        try:
            return get_all_modules()
        except Exception as e:
            logger.warning(f"Failed to load CV modules: {e}")
            return {}

    def _load_pd_modules(self) -> Dict[str, SCIDPDModule]:
        """Load all available SCID-PD modules"""
        try:
            return get_all_pd_modules()
        except Exception as e:
            logger.warning(f"Failed to load PD modules: {e}")
            return {}

    def start_deployment_session(
        self,
        module_id: str,
        patient_info: Dict[str, Any] = None,
        session_id: str = None
    ) -> Tuple[str, str]:
        """
        Start a new deployment session for a specific module

        Args:
            module_id: ID of the module to deploy
            patient_info: Patient demographic and clinical information
            session_id: Optional custom session ID

        Returns:
            Tuple of (session_id, welcome_message)
        """
        if session_id is None:
            self.session_counter += 1
            session_id = "03d"

        # Determine module type and get module
        module = None
        module_type = "unknown"

        if module_id in self.cv_modules:
            module = self.cv_modules[module_id]
            module_type = "SCID-CV"
        elif module_id in self.pd_modules:
            module = self.pd_modules[module_id]
            module_type = "SCID-PD"
        else:
            raise ValueError(f"Module {module_id} not found. Available CV modules: {list(self.cv_modules.keys())}, PD modules: {list(self.pd_modules.keys())}")

        # Create session
        session = DeploymentSession(
            session_id=session_id,
            module_id=module_id,
            module_name=module.name,
            patient_info=patient_info or {}
        )

        self.active_sessions[session_id] = session

        # Create professional welcome message
        welcome_message = self._create_welcome_message(module, module_type, patient_info)

        logger.info(f"Started deployment session {session_id} for module {module_id}")
        return session_id, welcome_message

    def _create_welcome_message(self, module: Union[SCIDModule, SCIDPDModule], module_type: str, patient_info: Dict[str, Any]) -> str:
        """Create a professional welcome message"""
        patient_name = patient_info.get('name', 'the patient') if patient_info else 'the patient'

        welcome_lines = [
            "=" * 80,
            f"🏥 {module_type.upper()} MODULE DEPLOYMENT SESSION",
            "=" * 80,
            "",
            f"📋 Module: {module.name}",
            f"🎯 Purpose: {module.description}",
            f"⏱️  Estimated Time: {module.estimated_time_mins} minutes",
            "",
            "📝 Instructions:",
            "• Please answer each question honestly and to the best of your ability",
            "• Take your time to think about each question carefully",
            "• If you need clarification, ask the administrator",
            "• Some questions may be sensitive - please let us know if you need support",
            "",
            "🔒 Confidentiality:",
            "• All information shared will be kept strictly confidential",
            "• This assessment is for clinical purposes only",
            "",
            "🚀 Ready to begin the assessment?",
            "Type 'yes' to start or 'help' for more information.",
            "=" * 80
        ]

        return "\n".join(welcome_lines)

    def get_next_question(self, session_id: str) -> Optional[ProfessionalQuestion]:
        """
        Get the next question in the deployment sequence

        Args:
            session_id: Active session ID

        Returns:
            ProfessionalQuestion object or None if complete
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        # Get the appropriate module
        if session.module_id in self.cv_modules:
            module = self.cv_modules[session.module_id]
            questions = module.questions
        else:
            module = self.pd_modules[session.module_id]
            questions = module.questions

        # Find the next question to ask (considering skip logic)
        next_question = self._find_next_question(questions, session)

        if next_question is None:
            return None

        # Format as professional question
        question_number = len(session.question_history) + 1
        professional_question = self._format_professional_question(
            next_question, question_number, len(questions)
        )

        # Update session
        session.question_history.append(next_question.id)
        session.status = "in_progress"

        return professional_question

    def _find_next_question(self, questions: List[Union[SCIDQuestion, Any]], session: DeploymentSession) -> Optional[Union[SCIDQuestion, Any]]:
        """Find the next question to ask, considering skip logic"""
        # Start from the current question index
        for i in range(session.current_question_index, len(questions)):
            question = questions[i]

            # Check if this question should be skipped based on previous responses
            if self._should_skip_question(question, session):
                session.skip_logic_applied.append(question.id)
                session.current_question_index = i + 1  # Move to next question
                continue

            # Check if this is a required question or if we should ask it
            if question.required or self._should_ask_optional_question(question, session):
                session.current_question_index = i + 1  # Move to next question after returning this one
                return question

        return None

    def _should_skip_question(self, question: Union[SCIDQuestion, Any], session: DeploymentSession) -> bool:
        """Determine if a question should be skipped based on skip logic"""
        # Check skip logic if available
        if hasattr(question, 'skip_logic') and question.skip_logic:
            for response_value, skip_to_id in question.skip_logic.items():
                if response_value in session.responses.values():
                    # This question should be skipped
                    return True

        return False

    def _should_ask_optional_question(self, question: Union[SCIDQuestion, Any], session: DeploymentSession) -> bool:
        """Determine if an optional question should be asked"""
        # For now, ask all optional questions
        # This could be enhanced with more sophisticated logic
        return True

    def _format_professional_question(
        self,
        question: Union[SCIDQuestion, Any],
        question_number: int,
        total_questions: int
    ) -> ProfessionalQuestion:
        """Format a question for professional presentation"""

        # Create display text with progress indicator
        progress = f"Question {question_number} of {total_questions}"
        display_text = f"""
┌─ {progress} {'─' * (70 - len(progress))}─┐
│ {question.simple_text}
└{'─' * 74}┘
"""

        # Add help text if available
        if hasattr(question, 'help_text') and question.help_text:
            display_text += f"""
💡 Help: {question.help_text}
"""

        # Add examples if available
        if hasattr(question, 'examples') and question.examples:
            display_text += f"""
📋 Examples: {', '.join(question.examples[:2])}
"""

        professional_question = ProfessionalQuestion(
            question_id=question.id,
            display_text=display_text,
            response_type=question.response_type,
            required=question.required,
            question_number=question_number,
            total_questions=total_questions
        )

        # Format response options based on type and add to display
        if question.response_type == ResponseType.YES_NO:
            professional_question.options = ["Yes", "No"]
            professional_question.display_text += f"""
📝 Response Options:
   • Yes
   • No
   • [Or type your own response]
"""

        elif question.response_type == ResponseType.SCALE:
            if hasattr(question, 'scale_labels') and question.scale_labels:
                professional_question.scale_labels = question.scale_labels
                scale_text = "\n   • ".join([f"{i}: {label}" for i, label in enumerate(question.scale_labels)])
            else:
                # Default scale labels
                professional_question.scale_labels = [
                    "Not at all", "Slightly", "Moderately", "Very much"
                ]
                scale_text = "\n   • ".join([f"{i}: {label}" for i, label in enumerate(professional_question.scale_labels)])
            
            professional_question.display_text += f"""
📝 Response Options:
   • {scale_text}
   • [Or type your own response]
"""

        elif question.response_type == ResponseType.MULTIPLE_CHOICE:
            professional_question.options = question.options
            options_text = "\n   • ".join(professional_question.options)
            professional_question.display_text += f"""
📝 Response Options:
   • {options_text}
   • [Or type your own response]
"""

        elif question.response_type == ResponseType.TEXT:
            professional_question.display_text += f"""
📝 Please provide a detailed response:
   • [Type your response here]
"""

        return professional_question

    def process_response(
        self,
        session_id: str,
        question_id: str,
        response: Any,
        notes: str = "",
        free_text: str = None
    ) -> Tuple[bool, str]:
        """
        Process a response to a question

        Args:
            session_id: Active session ID
            question_id: ID of the question being answered
            response: The response value (structured option)
            notes: Optional notes about the response
            free_text: Optional free text response

        Returns:
            Tuple of (is_valid, feedback_message)
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]

        # Validate the response
        try:
            self._validate_response(session, question_id, response)
            
            # Store response with metadata
            metadata = {
                "timestamp": datetime.now(),
                "notes": notes,
                "response_type": "structured" if not free_text else "mixed",
                "original_response": response
            }
            
            session.add_response(question_id, response, free_text=free_text, metadata=metadata)

            # Create response object for session tracking
            scid_response = SCIDResponse(
                question_id=question_id,
                response=response,
                notes=notes,
                timestamp=datetime.now()
            )

            feedback = self._create_response_feedback(session, question_id, response)
            return True, feedback

        except ResponseValidationError as e:
            session.validation_errors.append(str(e))
            return False, f"❌ Validation Error: {e}"

    def _validate_response(self, session: DeploymentSession, question_id: str, response: Any):
        """Validate a response based on question requirements"""
        # Get the appropriate module
        if session.module_id in self.cv_modules:
            module = self.cv_modules[session.module_id]
            question = module.get_question_by_id(question_id)
        else:
            module = self.pd_modules[session.module_id]
            question = module.get_question_by_id(question_id)

        if not question:
            raise ResponseValidationError(f"Question {question_id} not found")

        # Validate based on response type - now accepts both structured options and free text
        if question.response_type == ResponseType.YES_NO:
            valid_responses = [True, False, "yes", "no", "Yes", "No", "YES", "NO", 1, 0]
            if response not in valid_responses:
                # Allow free text responses for yes/no questions
                if isinstance(response, str) and response.strip():
                    # Accept any non-empty string as valid
                    pass
                else:
                    raise ResponseValidationError(f"Response must be yes/no or provide a text explanation, got: {response}")

        elif question.response_type == ResponseType.SCALE:
            try:
                value = float(response)
                if not (question.scale_range[0] <= value <= question.scale_range[1]):
                    # Allow free text responses for scale questions
                    if isinstance(response, str) and response.strip():
                        # Accept any non-empty string as valid
                        pass
                    else:
                        raise ResponseValidationError(f"Response must be between {question.scale_range[0]} and {question.scale_range[1]} or provide a text explanation, got: {value}")
            except (ValueError, TypeError):
                # Allow free text responses for scale questions
                if isinstance(response, str) and response.strip():
                    # Accept any non-empty string as valid
                    pass
                else:
                    raise ResponseValidationError(f"Response must be a number between {question.scale_range[0]} and {question.scale_range[1]} or provide a text explanation, got: {response}")

        elif question.response_type == ResponseType.MULTIPLE_CHOICE:
            if isinstance(response, str):
                if response not in question.options:
                    # Allow free text responses for multiple choice questions
                    if response.strip():
                        # Accept any non-empty string as valid
                        pass
                    else:
                        raise ResponseValidationError(f"Response must be one of the options or provide a text explanation, got: {response}")
            elif isinstance(response, list):
                # For list responses, still validate against options
                invalid_options = set(response) - set(question.options)
                if invalid_options:
                    raise ResponseValidationError(f"Invalid options selected: {', '.join(invalid_options)}")

        elif question.response_type == ResponseType.TEXT:
            if not isinstance(response, str) or len(response.strip()) == 0:
                raise ResponseValidationError("Response must be non-empty text")

        # Check required questions
        if question.required and (response is None or (isinstance(response, str) and response.strip() == "")):
            raise ResponseValidationError("This is a required question and cannot be left blank")

    def _create_response_feedback(self, session: DeploymentSession, question_id: str, response: Any) -> str:
        """Create professional feedback for a valid response"""
        # Calculate progress
        if session.module_id in self.cv_modules:
            module = self.cv_modules[session.module_id]
            total_questions = len(module.questions)
        else:
            module = self.pd_modules[session.module_id]
            total_questions = len(module.questions)

        progress = session.get_completion_percentage(total_questions)

        feedback_lines = [
            "✅ Response recorded successfully",
            f"📊 Progress: {progress:.1f}% complete ({len(session.responses)}/{total_questions} questions)",
        ]

        if progress >= 100:
            feedback_lines.append("🎉 Assessment complete! Ready for results.")
        else:
            feedback_lines.append("➡️  Ready for the next question.")

        return "\n".join(feedback_lines)

    def complete_session(self, session_id: str) -> Union[ModuleResult, PersonalityProfile]:
        """
        Complete a deployment session and generate results

        Args:
            session_id: Session ID to complete

        Returns:
            ModuleResult for CV modules or PersonalityProfile for PD modules
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.active_sessions[session_id]
        session.status = "completed"

        # Generate results based on module type
        if session.module_id in self.cv_modules:
            module = self.cv_modules[session.module_id]
            result = self.cv_administrator.administer_module(module, session.responses)
        else:
            module = self.pd_modules[session.module_id]
            result = self.pd_administrator.administer_module(module, session.responses)

        logger.info(f"Completed session {session_id} for module {session.module_id}")
        return result

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get the current status of a deployment session"""
        if session_id not in self.active_sessions:
            return {"status": "not_found"}

        session = self.active_sessions[session_id]

        # Get question counts
        if session.module_id in self.cv_modules:
            module = self.cv_modules[session.module_id]
            total_questions = len(module.questions)
        else:
            module = self.pd_modules[session.module_id]
            total_questions = len(module.questions)

        return {
            "session_id": session.session_id,
            "module_id": session.module_id,
            "module_name": session.module_name,
            "status": session.status,
            "progress": session.get_completion_percentage(total_questions),
            "questions_completed": len(session.responses),
            "total_questions": total_questions,
            "start_time": session.start_time.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "validation_errors": len(session.validation_errors)
        }

    def list_available_modules(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all available modules by category"""
        cv_modules = []
        for module_id, module in self.cv_modules.items():
            cv_modules.append({
                "id": module_id,
                "name": module.name,
                "description": module.description,
                "estimated_time": module.estimated_time_mins,
                "questions_count": len(module.questions)
            })

        pd_modules = []
        for module_id, module in self.pd_modules.items():
            pd_modules.append({
                "id": module_id,
                "name": module.name,
                "description": module.description,
                "estimated_time": module.estimated_time_mins,
                "questions_count": len(module.questions),
                "cluster": module.dsm_cluster.value if hasattr(module, 'dsm_cluster') and module.dsm_cluster else "unknown"
            })

        return {
            "scid_cv_modules": cv_modules,
            "scid_pd_modules": pd_modules
        }

    async def suggest_modules_async(self, patient_info: Dict[str, Any], max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest appropriate modules based on patient information (async version)

        Args:
            patient_info: Patient demographic and clinical information
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested modules with rationale
        """
        if not self.module_selector:
            return []

        # Module selector functionality not available in current implementation
        return []

    def suggest_modules(self, patient_info: Dict[str, Any], max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """
        Suggest appropriate modules based on patient information (synchronous version)

        Args:
            patient_info: Patient demographic and clinical information
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of suggested modules with rationale
        """
        # For now, return empty list in synchronous version
        # In production, you might want to implement a synchronous version
        logger.warning("suggest_modules called synchronously - use suggest_modules_async for LLM features")
        return []

# Utility functions for external use
def create_deployment_session(
    module_id: str,
    patient_info: Dict[str, Any] = None,
    use_llm: bool = False
) -> Tuple[ModuleDeployer, str, str]:
    """
    Convenience function to create a deployment session

    Args:
        module_id: Module to deploy
        patient_info: Patient information
        use_llm: Whether to use LLM for intelligent features

    Returns:
        Tuple of (deployer, session_id, welcome_message)
    """
    deployer = ModuleDeployer(use_llm=use_llm)
    session_id, welcome_message = deployer.start_deployment_session(
        module_id=module_id,
        patient_info=patient_info
    )
    return deployer, session_id, welcome_message

# Example usage and testing functions
def demo_deployment():
    """Demo function showing how to use the module deployer"""
    print("🧪 Module Deployer Demo")
    print("=" * 50)

    # Create deployer
    deployer = ModuleDeployer(use_llm=False)

        # List available modules
    modules = deployer.list_available_modules()
    print(f"📋 Available CV modules: {len(modules['scid_cv_modules'])}")
    print(f"📋 Available PD modules: {len(modules['scid_pd_modules'])}")
    
    # Show some available module IDs
    if modules['scid_cv_modules']:
        print(f"📋 Sample CV modules: {[m['id'] for m in modules['scid_cv_modules'][:3]]}")
    if modules['scid_pd_modules']:
        print(f"📋 Sample PD modules: {[m['id'] for m in modules['scid_pd_modules'][:3]]}")

    # Start a session for Avoidant Personality Disorder module
    patient_info = {
        "name": "John Doe",
        "age": 35,
        "gender": "male",
        "presenting_concern": "Feeling socially inhibited and avoiding social situations due to fear of criticism"
    }

    try:
        session_id, welcome = deployer.start_deployment_session(
            module_id="AVPD",
            patient_info=patient_info
        )

        print(f"\n🎯 Started session: {session_id}")
        print(welcome)

        # Simulate answering questions
        question_count = 0
        while True:
            question = deployer.get_next_question(session_id)
            if question is None:
                break

            question_count += 1
            print(f"\n{question.display_text}")

            # Simulate a response based on question type
            if question.response_type == ResponseType.YES_NO:
                response = "yes"
            elif question.response_type == ResponseType.SCALE:
                response = 2  # Moderate
            elif question.response_type == ResponseType.MULTIPLE_CHOICE:
                response = question.options[0] if question.options else "Other"
            else:
                response = "Sample response"

            # Process the response
            is_valid, feedback = deployer.process_response(
                session_id, question.question_id, response
            )

            print(f"💬 Response: {response}")
            print(feedback)

            if question_count >= 3:  # Limit demo to 3 questions
                break

        # Get session status
        status = deployer.get_session_status(session_id)
        print(f"\n📊 Session Status: {status}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    demo_deployment()

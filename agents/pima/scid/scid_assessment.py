"""
SCID Assessment Tool - Complete Workflow Integration
==============================================

A comprehensive SCID-based assessment system that integrates:
- Module Selection (ReAct Agent)
- Module Deployment (Professional Administration)
- Real-time Analysis (DSM Criteria Analysis)
- Result Generation (Structured JSON + LLM Summary)

Author: SCID Assessment Team
Version: 1.0.0
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import asyncio
from sqlalchemy.orm import Session

# Import SCID Components
from .scid_cv import get_module, get_all_modules
from .scid_cv.base_types import SCIDModule, SCIDQuestion, ResponseType, ModuleResult
from .scid_cv.utils import SCIDAdministrator

from .scid_pd import get_pd_module, get_all_pd_modules
from .scid_pd.base_types import SCIDPDModule, SCIDPDQuestion, PersonalityModuleResult
from .scid_pd.utils import SCIDPDAdministrator

# Import Workflow Components
from .module_deployer import ModuleDeployer, ProfessionalQuestion
from .enhanced_module_deployer import EnhancedModuleDeployer
from .dsm_criteria_analyzer import DSMCriteriaAnalyzer, RealTimeAnalysis, ComprehensiveInsights
from .dsm_criteria_bank import DSMCriteriaBank

# Import LLM Client for Summaries
from agents.llm_client import LLMClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssessmentStatus(Enum):
    """Status of an assessment session"""
    INITIALIZED = "initialized"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class AssessmentMode(Enum):
    """Mode of assessment administration"""
    INTERACTIVE = "interactive"  # One question at a time
    BATCH = "batch"              # All questions at once
    HYBRID = "hybrid"           # Mix of both

@dataclass
class AssessmentSession:
    """Tracks the state of a complete assessment session"""
    session_id: str
    patient_id: str
    module_id: str
    module_name: str
    status: AssessmentStatus = AssessmentStatus.INITIALIZED
    mode: AssessmentMode = AssessmentMode.INTERACTIVE

    # Session metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress tracking
    current_question_index: int = 0
    total_questions: int = 0
    completion_percentage: float = 0.0

    # Response data
    responses: Dict[str, Any] = field(default_factory=dict)
    free_text_responses: Dict[str, str] = field(default_factory=dict)
    response_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    question_history: List[str] = field(default_factory=list)

    # Analysis results
    real_time_analyses: List[RealTimeAnalysis] = field(default_factory=list)
    current_analysis: Optional[RealTimeAnalysis] = None

    # Final results
    final_result: Optional[Union[ModuleResult, PersonalityModuleResult]] = None
    comprehensive_insights: Optional[ComprehensiveInsights] = None
    llm_summary: Optional[str] = None

    # Error tracking
    validation_errors: List[str] = field(default_factory=list)
    skip_logic_applied: List[str] = field(default_factory=list)

    def update_timestamp(self):
        """Update the last updated timestamp"""
        self.updated_at = datetime.now()

    def mark_started(self):
        """Mark assessment as started"""
        self.status = AssessmentStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.update_timestamp()

    def mark_completed(self):
        """Mark assessment as completed"""
        self.status = AssessmentStatus.COMPLETED
        self.completed_at = datetime.now()
        self.completion_percentage = 100.0
        self.update_timestamp()

    def update_progress(self):
        """Update completion percentage"""
        if self.total_questions > 0:
            self.completion_percentage = (len(self.responses) / self.total_questions) * 100
        self.update_timestamp()

@dataclass
class AssessmentResult:
    """Complete assessment result with both structured and narrative formats"""
    session_id: str
    patient_id: str
    module_id: str
    module_name: str

    # Structured results
    assessment_data: Dict[str, Any]
    clinical_insights: ComprehensiveInsights
    real_time_analyses: List[RealTimeAnalysis]

    # Narrative summary
    llm_summary: str

    # Metadata
    completion_percentage: float
    assessment_duration: Optional[timedelta]
    generated_at: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "module_id": self.module_id,
            "module_name": self.module_name,
            "assessment_data": self.assessment_data,
            "clinical_insights": {
                "diagnostic_summary": self.clinical_insights.diagnostic_summary,
                "key_symptoms": self.clinical_insights.key_symptoms,
                "severity_assessment": self.clinical_insights.severity_assessment,
                "functional_impairment": self.clinical_insights.functional_impairment,
                "differential_considerations": self.clinical_insights.differential_considerations,
                "treatment_implications": self.clinical_insights.treatment_implications,
                "risk_assessment": self.clinical_insights.risk_assessment,
                "follow_up_priorities": self.clinical_insights.follow_up_priorities,
                "clinical_notes": self.clinical_insights.clinical_notes
            },
            "completion_percentage": self.completion_percentage,
            "assessment_duration_seconds": self.assessment_duration.total_seconds() if self.assessment_duration else None,
            "generated_at": self.generated_at.isoformat()
        }, indent=2, default=str)

class SCIDAssessment:
    """
    Complete SCID Assessment Workflow System

    This class orchestrates the entire SCID assessment process:
    1. Initialize assessment with module selection
    2. Administer questions one-by-one with real-time analysis
    3. Generate incremental results (even if incomplete)
    4. Produce final comprehensive results with LLM summary
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize the SCID Assessment system

        Args:
            use_llm: Whether to use LLM for intelligent features and summaries
        """
        self.use_llm = use_llm

        # Initialize core components
        self.deployer = EnhancedModuleDeployer(use_llm=use_llm)
        self.analyzer = DSMCriteriaAnalyzer()
        self.criteria_bank = DSMCriteriaBank()

        # Initialize LLM client for summaries
        self.llm_client = LLMClient() if use_llm else None

        logger.info("SCID Assessment system initialized")

    def _load_session(self, db: Session, session_id: str) -> Optional[AssessmentSession]:
        """Load session from database and convert to domain object"""
        from models.sql_models.assessment_models import SCIDAssessment as SCIDAssessmentModel

        db_session = db.query(SCIDAssessmentModel).filter(SCIDAssessmentModel.session_id == session_id).first()
        if not db_session:
            return None

        # Reconstruct AssessmentSession domain object
        session = AssessmentSession(
            session_id=db_session.session_id,
            patient_id=str(db_session.patient_id),
            module_id=db_session.module_id,
            module_name=db_session.module_name,
            status=AssessmentStatus(db_session.status),
            mode=AssessmentMode.INTERACTIVE, # Default for now, store in DB if needed
            created_at=db_session.created_at,
            updated_at=db_session.updated_at,
            started_at=db_session.started_at,
            completed_at=db_session.completed_at,
            completion_percentage=db_session.completion_percentage
        )

        # Restore data from JSON fields
        if db_session.assessment_data:
            data = db_session.assessment_data
            if "responses" in data:
                session.responses = data["responses"].get("structured_responses", {})
                session.free_text_responses = data["responses"].get("free_text_responses", {})
                session.response_metadata = data["responses"].get("response_metadata", {})
                session.question_history = data["progress"].get("question_history", [])
                session.validation_errors = data["errors"].get("validation_errors", [])
                session.skip_logic_applied = data["errors"].get("skip_logic_applied", [])
            
            # Restore total questions if possible (might need module lookup)
            session.total_questions = data["progress"].get("total_questions", 0)

            # Restore analyses
            if "analysis" in data:
                # This is simplified - fully restoring objects might be complex
                # For now we rely on re-analyzing or just storing the JSON
                pass

        return session

    def _save_session(self, db: Session, session: AssessmentSession):
        """Save domain object to database"""
        from models.sql_models.assessment_models import SCIDAssessment as SCIDAssessmentModel

        # Generate data structure
        assessment_data = self._generate_assessment_data(session)

        # Check if exists
        db_session = db.query(SCIDAssessmentModel).filter(SCIDAssessmentModel.session_id == session.session_id).first()
        
        if db_session:
            # Update
            db_session.status = session.status.value
            db_session.completion_percentage = session.completion_percentage
            db_session.assessment_data = assessment_data
            db_session.updated_at = datetime.now()
            if session.started_at:
                db_session.started_at = session.started_at
            if session.completed_at:
                db_session.completed_at = session.completed_at
            
            # Update insights if available
            if session.comprehensive_insights:
                # Convert dataclass to dict
                db_session.clinical_insights = {
                    "diagnostic_summary": session.comprehensive_insights.diagnostic_summary,
                    "key_symptoms": session.comprehensive_insights.key_symptoms,
                    "severity_assessment": session.comprehensive_insights.severity_assessment,
                    "functional_impairment": session.comprehensive_insights.functional_impairment,
                    "differential_considerations": session.comprehensive_insights.differential_considerations,
                    "treatment_implications": session.comprehensive_insights.treatment_implications,
                    "risk_assessment": session.comprehensive_insights.risk_assessment,
                    "follow_up_priorities": session.comprehensive_insights.follow_up_priorities,
                    "clinical_notes": session.comprehensive_insights.clinical_notes
                }
            
            if session.llm_summary:
                db_session.llm_summary = session.llm_summary
        else:
            # Create new
            db_session = SCIDAssessmentModel(
                session_id=session.session_id,
                patient_id=session.patient_id,
                module_id=session.module_id,
                module_name=session.module_name,
                status=session.status.value,
                completion_percentage=session.completion_percentage,
                assessment_data=assessment_data,
                created_at=session.created_at,
                updated_at=session.updated_at,
                started_at=session.started_at
            )
            db.add(db_session)

        db.commit()
        db.refresh(db_session)

    def start_assessment(
        self,
        db: Session,
        patient_id: str,
        module_id: Optional[str] = None,
        patient_info: Optional[Dict[str, Any]] = None,
        mode: AssessmentMode = AssessmentMode.INTERACTIVE
    ) -> Tuple[str, str]:
        """
        Start a new SCID assessment session

        Args:
            db: Database session
            patient_id: Unique identifier for the patient
            module_id: Specific module ID (optional - will use selector if not provided)
            patient_info: Patient demographic and clinical information
            mode: Assessment administration mode

        Returns:
            Tuple of (session_id, welcome_message)
        """
        # Generate session ID
        session_id = str(uuid.uuid4())

        try:
            # If no module specified, default to MDD
            if not module_id:
                module_id = "MDD"
                logger.info(f"No module specified for patient {patient_id}, defaulting to MDD module")

            # Start deployment session
            deployment_session_id, welcome_message = self.deployer.start_deployment_session(
                module_id=module_id,
                patient_info=patient_info or {}
            )

            # Create assessment session domain object
            session = AssessmentSession(
                session_id=session_id,
                patient_id=patient_id,
                module_id=module_id,
                module_name=self._get_module_name(module_id),
                mode=mode
            )

            # Get total questions for progress tracking
            if module_id in self.deployer.cv_modules:
                session.total_questions = len(self.deployer.cv_modules[module_id].questions)
            elif module_id in self.deployer.pd_modules:
                session.total_questions = len(self.deployer.pd_modules[module_id].questions)

            # Save to DB
            self._save_session(db, session)

            logger.info(f"Started SCID assessment session {session_id} for patient {patient_id}, module {module_id}")
            return session_id, welcome_message

        except Exception as e:
            logger.error(f"Failed to start assessment: {e}")
            raise

    def get_next_question(self, db: Session, session_id: str) -> Optional[ProfessionalQuestion]:
        """
        Get the next question in the assessment

        Args:
            db: Database session
            session_id: Active assessment session ID

        Returns:
            ProfessionalQuestion object or None if assessment complete
        """
        session = self._load_session(db, session_id)
        if not session:
            # Potentially handle "legacy in-memory sessions here if needed, or raise Error"
            raise ValueError(f"Assessment session {session_id} not found")

        if session.status == AssessmentStatus.COMPLETED:
            return None

        if session.status == AssessmentStatus.INITIALIZED:
            session.mark_started()
            self._save_session(db, session)

        # Restore deployer state (important for skip logic)
        # We need to manually sync the deployer's internal session with our stored responses
        # This is a bit tricky because deployer expects its own session object
        # For now, we reconstruct enough context
        
        # In a stateless design, `deployer.get_next_question` should ideally accept the response history
        # Since `deployer` is stateful in `active_sessions`, we have a misalignment.
        # We will bypass the `deployer`'s session management for stateless retrieval if possible,
        # OR we create a temporary session in deployer.
        
        # Let's ensure a session exists in the deployer
        if session_id not in self.deployer.active_sessions:
            self.deployer.start_deployment_session(
                module_id=session.module_id,
                patient_info={}, # potentially reload patient info
                session_id=session_id
            )
            # Hydrate responses
            deployer_session = self.deployer.active_sessions[session_id]
            deployer_session.responses = session.responses.copy()
            deployer_session.question_history = session.question_history.copy()
            deployer_session.skip_logic_applied = session.skip_logic_applied.copy()
            deployer_session.validation_errors = session.validation_errors.copy()
            # Careful with current_question_index - we might need to recalculate or store it
        
        # Get next question from deployer
        question = self.deployer.get_next_question(session_id)

        if question is None:
            # Assessment complete
            session.mark_completed()
            self._save_session(db, session)
            logger.info(f"Assessment {session_id} completed")
            return None

        return question

    def process_response(
        self,
        db: Session,
        session_id: str,
        question_id: str,
        response: Any,
        notes: str = "",
        free_text: str = None
    ) -> Tuple[bool, str, Optional[RealTimeAnalysis]]:
        """
        Process a response and perform real-time analysis

        Args:
            db: Database session
            session_id: Active assessment session ID
            question_id: ID of the question being answered
            response: The response value
            notes: Optional notes about the response
            free_text: Optional free text response

        Returns:
            Tuple of (is_valid, feedback_message, analysis_result)
        """
        session = self._load_session(db, session_id)
        if not session:
            raise ValueError(f"Assessment session {session_id} not found")

        # Sync with Deployer (as in get_next_question)
        if session_id not in self.deployer.active_sessions:
            self.deployer.start_deployment_session(
                module_id=session.module_id,
                patient_info={}, 
                session_id=session_id
            )
            deployer_session = self.deployer.active_sessions[session_id]
            deployer_session.responses = session.responses.copy()
            deployer_session.question_history = session.question_history.copy()
            deployer_session.skip_logic_applied = session.skip_logic_applied.copy()
            deployer_session.validation_errors = session.validation_errors.copy()
            # We need to set current index correctly too, but let's see if skip logic handles it

        # Process response with enhanced analysis
        is_valid, feedback, analysis = self.deployer.process_response_with_analysis(
            session_id, question_id, response, notes, free_text
        )

        if is_valid:
            # Update domain session from deployer session
            deployer_session = self.deployer.active_sessions[session_id]
            session.responses = deployer_session.responses.copy()
            session.free_text_responses = deployer_session.free_text_responses.copy()
            session.response_metadata = deployer_session.response_metadata.copy()
            session.question_history = deployer_session.question_history.copy()
            session.skip_logic_applied = deployer_session.skip_logic_applied.copy()
            session.validation_errors = deployer_session.validation_errors.copy()

            # Store analysis result
            if analysis:
                session.real_time_analyses.append(analysis)
                session.current_analysis = analysis

            # Update progress
            session.update_progress()

            # Save to DB
            self._save_session(db, session)

            logger.info(f"Processed response for question {question_id} in session {session_id}")

        return is_valid, feedback, analysis

    def get_current_results(
        self,
        db: Session,
        session_id: str,
        include_llm_summary: bool = True
    ) -> AssessmentResult:
        """
        Get current assessment results (even if incomplete)

        Args:
            db: Database session
            session_id: Active assessment session ID
            include_llm_summary: Whether to generate LLM summary

        Returns:
            AssessmentResult with current state
        """
        session = self._load_session(db, session_id)
        if not session:
            raise ValueError(f"Assessment session {session_id} not found")

        # Generate comprehensive insights
        module = self._get_module(session.module_id)
        comprehensive_insights = self.analyzer.get_comprehensive_insights(module, session.responses)
        
        # Store insights back to session for saving
        session.comprehensive_insights = comprehensive_insights

        # Calculate assessment duration
        duration = None
        if session.started_at:
            # Handle potential timezone mismatch
            now = datetime.now()
            if session.started_at.tzinfo:
                now = datetime.now(session.started_at.tzinfo)
            duration = now - session.started_at

        # Generate structured assessment data
        assessment_data = self._generate_assessment_data(session)

        # Generate LLM summary if requested and LLM is available
        llm_summary = ""
        # Check if stored in DB
        from models.sql_models.assessment_models import SCIDAssessment as SCIDAssessmentModel
        db_session = db.query(SCIDAssessmentModel).filter(SCIDAssessmentModel.session_id == session_id).first()
        if db_session and db_session.llm_summary and len(db_session.llm_summary) > 10:
             llm_summary = db_session.llm_summary
        
        # Generate new if needed
        if (not llm_summary) and include_llm_summary and self.llm_client and session.real_time_analyses:
            try:
                llm_summary = self._generate_llm_summary(session, comprehensive_insights)
                session.llm_summary = llm_summary
                self._save_session(db, session) # Save the summary
            except Exception as e:
                logger.warning(f"Failed to generate LLM summary: {e}")
                llm_summary = "Summary generation failed - see structured results below"

        result = AssessmentResult(
            session_id=session.session_id,
            patient_id=session.patient_id,
            module_id=session.module_id,
            module_name=session.module_name,
            assessment_data=assessment_data,
            clinical_insights=comprehensive_insights,
            real_time_analyses=session.real_time_analyses.copy(),
            llm_summary=llm_summary,
            completion_percentage=session.completion_percentage,
            assessment_duration=duration,
            generated_at=datetime.now()
        )

        return result

    def complete_assessment(self, db: Session, session_id: str) -> AssessmentResult:
        """
        Complete the assessment and generate final results

        Args:
            db: Database session
            session_id: Assessment session ID to complete

        Returns:
            Final AssessmentResult
        """
        session = self._load_session(db, session_id)
        if not session:
            raise ValueError(f"Assessment session {session_id} not found")

        try:
            # Sync deployer if needed
            if session_id not in self.deployer.active_sessions:
                 self.deployer.start_deployment_session(
                    module_id=session.module_id,
                    patient_info={}, 
                    session_id=session_id
                )
                 # Restore minimal state if needed for completion logic

            # Complete the deployment session
            # final_result = self.deployer.complete_session(session_id) # Might depend on internal state
            # session.final_result = final_result # Not persisting this object directly yet

            # Mark as completed
            session.mark_completed()
            self._save_session(db, session)

            # Generate final results
            final_assessment = self.get_current_results(db, session_id, include_llm_summary=True)

            logger.info(f"Completed assessment {session_id} for patient {session.patient_id}")
            return final_assessment

        except Exception as e:
            logger.error(f"Failed to complete assessment {session_id}: {e}")
            raise

    def get_session_status(self, db: Session, session_id: str) -> Dict[str, Any]:
        """Get the current status of an assessment session"""
        session = self._load_session(db, session_id)
        if not session:
            return {"status": "not_found"}

        return {
            "session_id": session.session_id,
            "patient_id": session.patient_id,
            "module_id": session.module_id,
            "module_name": session.module_name,
            "status": session.status.value,
            "mode": session.mode.value,
            "completion_percentage": session.completion_percentage,
            "questions_completed": len(session.responses),
            "total_questions": session.total_questions,
            "created_at": session.created_at.isoformat(),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "updated_at": session.updated_at.isoformat(),
            "validation_errors": len(session.validation_errors)
        }

    def list_active_sessions(self, db: Session) -> List[Dict[str, Any]]:
        """List all active assessment sessions"""
        from models.sql_models.assessment_models import SCIDAssessment as SCIDAssessmentModel, AssessmentStatus as DBStatus
        
        # Query active sessions from DB
        # active_db_sessions = db.query(SCIDAssessmentModel).filter(SCIDAssessmentModel.status == DBStatus.IN_PROGRESS).all()
        # For compatibility with Enum, just check strings
        active_db_sessions = db.query(SCIDAssessmentModel).all() # Just return all for now or filter by status

        results = []
        for db_s in active_db_sessions:
            if db_s.status != "completed":
                 results.append({
                    "session_id": db_s.session_id,
                    "patient_id": str(db_s.patient_id),
                    "module_id": db_s.module_id,
                    "module_name": db_s.module_name,
                    "status": db_s.status,
                    "completion_percentage": db_s.completion_percentage,
                    "created_at": db_s.created_at.isoformat(),
                    "updated_at": db_s.updated_at.isoformat()
                 })
        return results

    def pause_session(self, db: Session, session_id: str):
        """Pause an active assessment session"""
        session = self._load_session(db, session_id)
        if not session:
            raise ValueError(f"Assessment session {session_id} not found")

        session.status = AssessmentStatus.PAUSED
        self._save_session(db, session)

        logger.info(f"Paused assessment session {session_id}")

    def resume_session(self, db: Session, session_id: str):
        """Resume a paused assessment session"""
        session = self._load_session(db, session_id)
        if not session:
            raise ValueError(f"Assessment session {session_id} not found")

        if session.status == AssessmentStatus.PAUSED:
            session.status = AssessmentStatus.IN_PROGRESS
            self._save_session(db, session)

        logger.info(f"Resumed assessment session {session_id}")

    def cancel_session(self, session_id: str):
        """Cancel an assessment session"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Assessment session {session_id} not found")

        session = self.active_sessions[session_id]
        session.status = AssessmentStatus.CANCELLED
        session.update_timestamp()


        logger.info(f"Cancelled assessment session {session_id}")

    def delete_session(self, db: Session, session_id: str):
        """Hard delete an assessment session"""
        
        # Helper to delete from DB
        from models.sql_models.assessment_models import SCIDAssessment as SCIDAssessmentModel
        
        db_session = db.query(SCIDAssessmentModel).filter(SCIDAssessmentModel.session_id == session_id).first()
        if db_session:
            db.delete(db_session)
            db.commit()
            logger.info(f"Deleted assessment session {session_id} from database")
        else:
             logger.warning(f"Assessment session {session_id} not found in database for deletion")
             
        # Clean up deployer memory if present
        if session_id in self.deployer.active_sessions:
            del self.deployer.active_sessions[session_id]

    def get_resume_context(self, db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get context to resume an assessment (e.g. current question)
        """
        session = self._load_session(db, session_id)
        if not session:
             raise ValueError(f"Assessment session {session_id} not found")
             
        # Ensure it's in a resumable state
        if session.status == AssessmentStatus.COMPLETED:
            return None
            
        # Hydrate deployer if needed (critical for skip logic)
        self.get_next_question(db, session_id) # This side-effect hydrates the deployer
        
        # Current question is waiting in deployer
        question = self.deployer.get_next_question(session_id)
        
        if not question:
            return None
            
        return {
             "session_id": session_id,
             "question_id": question.question_id,
             "display_text": question.display_text,
             "response_type": question.response_type.value,
             "options": question.options,
             "question_number": question.question_number,
             "total_questions": question.total_questions,
             "progress_percentage": (question.question_number - 1) / question.total_questions * 100
        }

    def _get_module(self, module_id: str) -> Union[SCIDModule, SCIDPDModule]:
        """Get module object by ID"""
        if module_id in self.deployer.cv_modules:
            return self.deployer.cv_modules[module_id]
        elif module_id in self.deployer.pd_modules:
            return self.deployer.pd_modules[module_id]
        else:
            raise ValueError(f"Module {module_id} not found")

    def _get_module_name(self, module_id: str) -> str:
        """Get module name by ID"""
        try:
            module = self._get_module(module_id)
            return module.name
        except:
            return module_id

    def _generate_assessment_data(self, session: AssessmentSession) -> Dict[str, Any]:
        """Generate structured assessment data"""
        import json
        data = {
            "session_info": {
                "session_id": session.session_id,
                "patient_id": session.patient_id,
                "module_id": session.module_id,
                "module_name": session.module_name,
                "completion_percentage": session.completion_percentage,
                "status": session.status.value
            },
            "responses": {
                "structured_responses": session.responses,
                "free_text_responses": session.free_text_responses,
                "response_metadata": session.response_metadata,
                "total_responses": len(session.responses)
            },
            "progress": {
                "questions_completed": len(session.responses),
                "total_questions": session.total_questions,
                "question_history": session.question_history
            },
            "analysis": {
                "current_analysis": session.current_analysis.__dict__ if session.current_analysis else None,
                "total_analyses": len(session.real_time_analyses),
                "latest_insights": session.real_time_analyses[-1].insights if session.real_time_analyses else []
            },
            "errors": {
                "validation_errors": session.validation_errors,
                "skip_logic_applied": session.skip_logic_applied
            }
        }
        return json.loads(json.dumps(data, default=str))

    def _generate_llm_summary(self, session: AssessmentSession, insights: ComprehensiveInsights) -> str:
        """Generate LLM-powered summary of assessment"""
        if not self.llm_client:
            return "LLM client not available"

        # Prepare context for LLM
        context = f"""
        SCID Assessment Summary for {session.module_name}

        Patient Progress: {session.completion_percentage:.1f}% complete
        Questions Answered: {len(session.responses)}/{session.total_questions}

        Clinical Insights:
        - Diagnostic Summary: {insights.diagnostic_summary}
        - Severity Assessment: {insights.severity_assessment}
        - Functional Impairment: {insights.functional_impairment}
        - Risk Assessment: {insights.risk_assessment}

        Key Symptoms: {', '.join(insights.key_symptoms[:5])}
        Treatment Implications: {', '.join(insights.treatment_implications[:3])}
        Follow-up Priorities: {', '.join(insights.follow_up_priorities[:3])}

        Recent Analysis:
        - Diagnostic Likelihood: {session.current_analysis.diagnostic_likelihood:.1% if session.current_analysis else 'N/A'}
        - Criteria Met: {session.current_analysis.criteria_met if session.current_analysis else 0}
        - Risk Factors: {', '.join(session.current_analysis.risk_factors) if session.current_analysis else 'None'}
        """

        prompt = f"""
        Please provide a comprehensive yet concise clinical summary of this SCID assessment.
        Focus on the key findings, clinical implications, and recommendations.

        Context:
        {context}

        Please structure your response as:
        1. Clinical Presentation Summary
        2. Key Diagnostic Findings
        3. Risk Assessment
        4. Treatment Recommendations
        5. Follow-up Needs

        Keep the summary professional, clear, and clinically relevant.
        """

        try:
            response = self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            return response.content
        except Exception as e:
            logger.error(f"LLM summary generation failed: {e}")
            return f"Clinical Summary Generation Failed: {str(e)}"

    def save_assessment(self, session_id: str, filepath: str):
        """Save assessment results to file"""
        result = self.get_current_results(session_id)
        with open(filepath, 'w') as f:
            f.write(result.to_json())

        logger.info(f"Saved assessment {session_id} to {filepath}")

    def load_assessment(self, filepath: str) -> AssessmentResult:
        """Load assessment results from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Reconstruct AssessmentResult
        clinical_insights = ComprehensiveInsights(
            diagnostic_summary=data['clinical_insights']['diagnostic_summary'],
            key_symptoms=data['clinical_insights']['key_symptoms'],
            severity_assessment=data['clinical_insights']['severity_assessment'],
            functional_impairment=data['clinical_insights']['functional_impairment'],
            differential_considerations=data['clinical_insights']['differential_considerations'],
            treatment_implications=data['clinical_insights']['treatment_implications'],
            risk_assessment=data['clinical_insights']['risk_assessment'],
            follow_up_priorities=data['clinical_insights']['follow_up_priorities'],
            clinical_notes=data['clinical_insights']['clinical_notes']
        )

        result = AssessmentResult(
            session_id=data['session_id'],
            patient_id=data['patient_id'],
            module_id=data['module_id'],
            module_name=data['module_name'],
            assessment_data=data['assessment_data'],
            clinical_insights=clinical_insights,
            real_time_analyses=[],  # Would need to reconstruct these if needed
            llm_summary=data.get('llm_summary', ''),
            completion_percentage=data['completion_percentage'],
            assessment_duration=timedelta(seconds=data['assessment_duration_seconds']) if data['assessment_duration_seconds'] else None,
            generated_at=datetime.fromisoformat(data['generated_at'])
        )

        return result

# Utility functions for easy integration
def create_assessment_session(
    patient_id: str,
    module_id: str = None,
    patient_info: Dict[str, Any] = None,
    use_llm: bool = True
) -> Tuple[SCIDAssessment, str, str]:
    """
    Convenience function to create and start an assessment session

    Args:
        patient_id: Unique identifier for the patient
        module_id: Specific module ID (optional)
        patient_info: Patient information
        use_llm: Whether to use LLM features

    Returns:
        Tuple of (assessment_system, session_id, welcome_message)
    """
    assessment = SCIDAssessment(use_llm=use_llm)
    session_id, welcome_message = assessment.start_assessment(
        patient_id=patient_id,
        module_id=module_id,
        patient_info=patient_info
    )
    return assessment, session_id, welcome_message

def quick_assessment_demo():
    """Demo function showing how to use the SCID Assessment system"""
    print("🧪 SCID Assessment System Demo")
    print("=" * 60)

    # Create assessment system
    assessment = SCIDAssessment(use_llm=False)  # Disable LLM for demo

    # Start assessment
    patient_info = {
        "name": "John Doe",
        "age": 35,
        "gender": "male",
        "clinical_presentation": "Patient reports feeling persistently sad, loss of interest in activities, difficulty sleeping, and decreased appetite for the past 3 weeks."
    }

    try:
        session_id, welcome = assessment.start_assessment(
            patient_id="demo_patient_123",
            module_id="MDD",  # Directly specify MDD module
            patient_info=patient_info
        )

        print(f"🎯 Started assessment session: {session_id}")
        print(welcome)
        print()

        # Simulate answering questions
        question_count = 0
        max_questions = 5  # Limit demo to 5 questions

        while question_count < max_questions:
            # Get next question
            question = assessment.get_next_question(session_id)
            if question is None:
                break

            question_count += 1
            print(f"📋 Question {question_count}:")
            print(question.display_text)

            # Simulate response based on question type
            if question.response_type == ResponseType.YES_NO:
                response = "yes"
                print("💬 Response: Yes")             
            elif question.response_type == ResponseType.SCALE:
                response = 2  # Moderate
                print("💬 Response: 2 (Moderate)")
            elif question.response_type == ResponseType.MULTIPLE_CHOICE:
                response = question.options[0] if question.options else "Other"
                print(f"💬 Response: {response}")
            else:
                response = "Sample response for demo"
                print(f"💬 Response: {response}")

            # Process response with analysis
            is_valid, feedback, analysis = assessment.process_response(
                session_id, question.question_id, response
            )

            print(f"✅ Feedback: {feedback}")

            if analysis:
                print(f"🧠 Real-time Analysis:")
                print(".1f")                
                print(f"   Criteria Met: {analysis.criteria_met}/{analysis.total_criteria}")
                print(f"   Severity: {analysis.severity_estimate}")
                print(f"   Risk Factors: {', '.join(analysis.risk_factors) if analysis.risk_factors else 'None'}")
                if analysis.insights:
                    print(f"   Insights: {analysis.insights[0]}")

            print("-" * 60)

        # Get current results
        print("📊 CURRENT ASSESSMENT RESULTS:")        
        print("=" * 60)
        result = assessment.get_current_results(session_id, include_llm_summary=False)

        print(f"Progress: {result.completion_percentage:.1f}%")
        print(f"Duration: {result.assessment_duration}")
        print(f"Diagnostic Summary: {result.clinical_insights.diagnostic_summary}")
        print(f"Key Symptoms: {', '.join(result.clinical_insights.key_symptoms)}")
        print(f"Severity: {result.clinical_insights.severity_assessment}")

        # Save results
        assessment.save_assessment(session_id, "/tmp/demo_assessment.json")
        print("💾 Results saved to /tmp/demo_assessment.json")

        # Get session status
        status = assessment.get_session_status(session_id)
        print(f"📈 Session Status: {status}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_assessment_demo()

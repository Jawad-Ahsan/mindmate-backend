"""
SCID Assessment Router
FastAPI router for SCID-based assessment workflows
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from agents.pima.scid.scid_assessment import SCIDAssessment, AssessmentResult, AssessmentMode
from core.config import settings
from database.database import get_db
from models.sql_models import Patient
from routers.authentication.authenticate import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assessment",
    tags=["assessment"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models for API
class StartAssessmentRequest(BaseModel):
    """Request to start a new assessment"""
    patient_id: str = Field(..., description="Unique identifier for the patient")
    module_id: Optional[str] = Field(None, description="Specific SCID module ID (optional, defaults to MDD)")
    patient_info: Optional[Dict[str, Any]] = Field(None, description="Patient demographic and clinical information")
    use_llm: bool = Field(False, description="Whether to use LLM for enhanced analysis")

class AssessmentResponse(BaseModel):
    """Response containing assessment results"""
    session_id: str
    patient_id: str
    module_id: str
    module_name: str
    assessment_data: Dict[str, Any]
    clinical_insights: Dict[str, Any]
    completion_percentage: float
    llm_summary: Optional[str] = None
    generated_at: datetime

class QuestionResponse(BaseModel):
    """Response containing next question"""
    session_id: str
    question_id: str
    display_text: str
    response_type: str
    options: List[str] = []
    question_number: int
    total_questions: int
    progress_percentage: float

class ProcessResponseRequest(BaseModel):
    """Request to process a response"""
    session_id: str
    question_id: str
    response: Any
    notes: str = ""
    free_text: Optional[str] = None

class ProcessResponseResponse(BaseModel):
    """Response after processing user input"""
    is_valid: bool
    feedback: str
    analysis: Optional[Dict[str, Any]] = None
    next_question: Optional[QuestionResponse] = None
    completion_percentage: float

class SessionStatusResponse(BaseModel):
    """Assessment session status"""
    session_id: str
    patient_id: str
    module_id: str
    module_name: str
    status: str
    mode: str
    completion_percentage: float
    questions_completed: int
    total_questions: int
    created_at: datetime
    started_at: Optional[datetime]
    updated_at: datetime

# Global assessment system instance
assessment_system = SCIDAssessment(use_llm=False)

@router.post("/start", response_model=Dict[str, Any])
async def start_assessment(
    assessment_request: StartAssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Start a new SCID assessment session

    - **patient_id**: Unique identifier for the patient
    - **module_id**: Specific SCID module (optional, defaults to MDD)
    - **patient_info**: Additional patient information
    - **use_llm**: Whether to use LLM for analysis
    """
    try:
        # Check if this is demo mode (test patient ID)
        is_demo_mode = assessment_request.patient_id == "550e8400-e29b-41d4-a716-446655440000"

        # Verify patient exists or create demo patient
        if is_demo_mode:
            # For demo mode, always create a new patient
            patient = None
            actual_patient_id = assessment_request.patient_id  # Will be replaced with auto-generated ID
        else:
            # For regular mode, query existing patient
            patient = db.query(Patient).filter(Patient.id == assessment_request.patient_id).first()
            actual_patient_id = assessment_request.patient_id

        if not patient:
            if is_demo_mode:
                # Try to find existing demo patient first
                demo_patient = db.query(Patient).filter(Patient.email == "demo@example.com").first()
                if demo_patient:
                    patient = demo_patient
                    actual_patient_id = str(patient.id)
                    logger.info(f"Using existing demo patient with ID: {actual_patient_id}")
                else:
                    # Create a demo patient for testing
                    from datetime import datetime, timezone
                    patient = Patient(
                        first_name="Demo",
                        last_name="Patient",
                        email="demo@example.com",
                        phone="+1234567890",
                        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
                        gender="male",  # Correct enum value
                        city="Demo City",
                        district="Demo District",
                        province="Demo Province",
                        country="Demo Country",
                        postal_code="12345",
                        primary_language="english",  # Correct enum value
                        record_status="active",  # Correct enum value
                        intake_completed_date=datetime.now(timezone.utc),
                        accepts_terms_and_conditions=True
                    )
                    db.add(patient)
                    db.commit()
                    db.refresh(patient)
                    # Use the actual auto-generated ID for the assessment
                    actual_patient_id = str(patient.id)
                    logger.info(f"Created demo patient with ID: {actual_patient_id}")
            else:
                raise HTTPException(status_code=404, detail=f"Patient {assessment_request.patient_id} not found")

        # Start assessment
        session_id, welcome_message = assessment_system.start_assessment(
            db=db,
            patient_id=actual_patient_id,
            module_id=assessment_request.module_id,
            patient_info=assessment_request.patient_info,
            mode=AssessmentMode.INTERACTIVE
        )

        # Get first question
        question = assessment_system.get_next_question(db, session_id)

        response_data = {
            "session_id": session_id,
            "welcome_message": welcome_message,
            "first_question": None
        }

        if question:
            response_data["first_question"] = {
                "session_id": session_id,
                "question_id": question.question_id,
                "display_text": question.display_text,
                "response_type": question.response_type.value,
                "options": question.options,
                "question_number": question.question_number,
                "total_questions": question.total_questions,
                "progress_percentage": (question.question_number - 1) / question.total_questions * 100
            }

        logger.info(f"Started assessment session {session_id} for patient {actual_patient_id}")
        return response_data

    except Exception as e:
        logger.error(f"Failed to start assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start assessment: {str(e)}")

@router.post("/respond", response_model=ProcessResponseResponse)
async def process_response(
    request: ProcessResponseRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Process a response to an assessment question

    - **session_id**: Active assessment session ID
    - **question_id**: ID of the question being answered
    - **response**: The patient's response
    - **notes**: Optional notes about the response
    - **free_text**: Optional free text response
    """
    try:
        # Process the response
        is_valid, feedback, analysis = assessment_system.process_response(
            db=db,
            session_id=request.session_id,
            question_id=request.question_id,
            response=request.response,
            notes=request.notes,
            free_text=request.free_text
        )

        response_data = {
            "is_valid": is_valid,
            "feedback": feedback,
            "analysis": None,
            "next_question": None,
            "completion_percentage": 0.0
        }

        # Add analysis if available
        if analysis:
            response_data["analysis"] = {
                "diagnostic_likelihood": analysis.diagnostic_likelihood,
                "severity_estimate": analysis.severity_estimate,
                "criteria_met": analysis.criteria_met,
                "criteria_partially_met": analysis.criteria_partially_met,
                "criteria_ambiguous": analysis.criteria_ambiguous,
                "insights": analysis.insights,
                "risk_factors": analysis.risk_factors
            }

        # Get next question if response was valid
        if is_valid:
            next_question = assessment_system.get_next_question(db, request.session_id)
            if next_question:
                response_data["next_question"] = {
                    "session_id": request.session_id,
                    "question_id": next_question.question_id,
                    "display_text": next_question.display_text,
                    "response_type": next_question.response_type.value,
                    "options": next_question.options,
                    "question_number": next_question.question_number,
                    "total_questions": next_question.total_questions,
                    "progress_percentage": (next_question.question_number - 1) / next_question.total_questions * 100
                }

        # Get current completion percentage
        session_status = assessment_system.get_session_status(db, request.session_id)
        response_data["completion_percentage"] = session_status["completion_percentage"]

        logger.info(f"Processed response for question {request.question_id} in session {request.session_id}")
        return ProcessResponseResponse(**response_data)

    except Exception as e:
        logger.error(f"Failed to process response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@router.get("/status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the current status of an assessment session"""
    try:
        status = assessment_system.get_session_status(db, session_id)

        return SessionStatusResponse(
            session_id=status["session_id"],
            patient_id=status["patient_id"],
            module_id=status["module_id"],
            module_name=status["module_name"],
            status=status["status"],
            mode=status["mode"],
            completion_percentage=status["completion_percentage"],
            questions_completed=status["questions_completed"],
            total_questions=status["total_questions"],
            created_at=datetime.fromisoformat(status["created_at"]),
            started_at=datetime.fromisoformat(status["started_at"]) if status["started_at"] else None,
            updated_at=datetime.fromisoformat(status["updated_at"])
        )

    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.get("/results/{session_id}", response_model=AssessmentResponse)
async def get_assessment_results(
    session_id: str,
    include_llm_summary: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get current assessment results (even if incomplete)"""
    try:
        result = assessment_system.get_current_results(
            db=db,
            session_id=session_id,
            include_llm_summary=include_llm_summary
        )

        return AssessmentResponse(
            session_id=result.session_id,
            patient_id=result.patient_id,
            module_id=result.module_id,
            module_name=result.module_name,
            assessment_data=result.assessment_data,
            clinical_insights={
                "diagnostic_summary": result.clinical_insights.diagnostic_summary,
                "key_symptoms": result.clinical_insights.key_symptoms,
                "severity_assessment": result.clinical_insights.severity_assessment,
                "functional_impairment": result.clinical_insights.functional_impairment,
                "differential_considerations": result.clinical_insights.differential_considerations,
                "treatment_implications": result.clinical_insights.treatment_implications,
                "risk_assessment": result.clinical_insights.risk_assessment,
                "follow_up_priorities": result.clinical_insights.follow_up_priorities,
                "clinical_notes": result.clinical_insights.clinical_notes
            },
            completion_percentage=result.completion_percentage,
            llm_summary=result.llm_summary,
            generated_at=result.generated_at
        )

    except Exception as e:
        logger.error(f"Failed to get assessment results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get assessment results: {str(e)}")

@router.post("/complete/{session_id}", response_model=AssessmentResponse)
async def complete_assessment(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Complete an assessment and generate final results"""
    try:
        final_result = assessment_system.complete_assessment(db, session_id)

        # Save results to database/file in background
        background_tasks.add_task(save_assessment_results, final_result, db)

        return AssessmentResponse(
            session_id=final_result.session_id,
            patient_id=final_result.patient_id,
            module_id=final_result.module_id,
            module_name=final_result.module_name,
            assessment_data=final_result.assessment_data,
            clinical_insights={
                "diagnostic_summary": final_result.clinical_insights.diagnostic_summary,
                "key_symptoms": final_result.clinical_insights.key_symptoms,
                "severity_assessment": final_result.clinical_insights.severity_assessment,
                "functional_impairment": final_result.clinical_insights.functional_impairment,
                "differential_considerations": final_result.clinical_insights.differential_considerations,
                "treatment_implications": final_result.clinical_insights.treatment_implications,
                "risk_assessment": final_result.clinical_insights.risk_assessment,
                "follow_up_priorities": final_result.clinical_insights.follow_up_priorities,
                "clinical_notes": final_result.clinical_insights.clinical_notes
            },
            completion_percentage=final_result.completion_percentage,
            llm_summary=final_result.llm_summary,
            generated_at=final_result.generated_at
        )

    except Exception as e:
        logger.error(f"Failed to complete assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete assessment: {str(e)}")

@router.get("/modules", response_model=List[Dict[str, Any]])
async def list_available_modules(
    current_user: dict = Depends(get_current_user)
):
    """List all available SCID modules"""
    try:
        modules_info = assessment_system.deployer.list_available_modules()
        return modules_info["scid_cv_modules"] + modules_info["scid_pd_modules"]

    except Exception as e:
        logger.error(f"Failed to list modules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list modules: {str(e)}")

@router.get("/sessions", response_model=List[SessionStatusResponse])
async def list_active_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all active assessment sessions"""
    try:
        sessions = assessment_system.list_active_sessions(db)
        return [
            SessionStatusResponse(
                session_id=s["session_id"],
                patient_id=s["patient_id"],
                module_id=s["module_id"],
                module_name=s["module_name"],
                status=s["status"],
                mode=s["mode"],
                completion_percentage=s["completion_percentage"],
                questions_completed=s["questions_completed"],
                total_questions=s["total_questions"],
                created_at=datetime.fromisoformat(s["created_at"]),
                started_at=datetime.fromisoformat(s["started_at"]) if s["started_at"] else None,
                updated_at=datetime.fromisoformat(s["updated_at"])
            )
            for s in sessions
        ]

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@router.post("/pause/{session_id}")
async def pause_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Pause an active assessment session"""
    try:
        assessment_system.pause_session(db, session_id)
        return {"message": f"Assessment session {session_id} paused successfully"}

    except Exception as e:
        logger.error(f"Failed to pause session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to pause session: {str(e)}")

@router.post("/resume/{session_id}")
async def resume_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Resume a paused assessment session"""
    try:
        assessment_system.resume_session(db, session_id)
        return {"message": f"Assessment session {session_id} resumed successfully"}


    except Exception as e:
        logger.error(f"Failed to resume session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume session: {str(e)}")

@router.delete("/{session_id}", status_code=204)
async def delete_assessment_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Permanently delete an assessment session"""
    try:
        assessment_system.delete_session(db, session_id)
        return None  # 204 No Content

    except Exception as e:
        logger.error(f"Failed to delete session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@router.get("/{session_id}/continue", response_model=Optional[QuestionResponse])
async def continue_assessment(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the current question to resume an assessment"""
    try:
        resume_context = assessment_system.get_resume_context(db, session_id)
        if not resume_context:
            return None # Or raise 404/400? For now None implies just render waiting/completed screen
            
        return QuestionResponse(**resume_context)

    except Exception as e:
        logger.error(f"Failed to resume assessment context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resume assessment context: {str(e)}")


# Background task functions
async def save_assessment_results(result: AssessmentResult, db: Session = None):
    """Background task to save assessment results"""
    try:
        # Save to file
        filename = f"/tmp/assessment_{result.session_id}_{result.generated_at.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            f.write(result.to_json())

        logger.info(f"Saved assessment results for session {result.session_id} to {filename}")

        # TODO: Save to database if needed
        # You can add database saving logic here

    except Exception as e:
        logger.error(f"Failed to save assessment results: {e}")

@router.get("/patient/history", response_model=List[SessionStatusResponse])
async def get_patient_assessments(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Get assessment history for the current patient"""
    try:
        # Check if user is a patient
        # NOTE: Adjust role check as per your auth system
        
        # Assuming we can find assessments for this user
        # We need to find the patient record associated with this user
        # user_email = current_user.get("sub")
        # patient = db.query(Patient).filter(Patient.email == user_email).first()
        
        # Or if current_user contains patient_id or similar info
        # For now, let's list all assessments (admin) or filter if we had patient_id context
        # Given the requirements, we'll implement a simple filter by known patient IDs if available
        # or simplified: return all sessions for now (demo purpose mostly)
        
        # BETTER: filter by patient_id derived from user. 
        # But we don't have easy link here without more robust user service lookups.
        # Fallback: Query all assessments for now, or improve later.
        
        # Let's try to get patient by email
        email = current_user.email
        patient = db.query(Patient).filter(Patient.email == email).first()
        
        from models.sql_models.assessment_models import SCIDAssessment as SCIDAssessmentModel, AssessmentStatus as DBStatus
        
        query = db.query(SCIDAssessmentModel)
        if patient:
            query = query.filter(SCIDAssessmentModel.patient_id == patient.id)
            
        sessions = query.order_by(SCIDAssessmentModel.created_at.desc()).all()
        
        return [
            SessionStatusResponse(
                session_id=s.session_id,
                patient_id=str(s.patient_id),
                module_id=s.module_id,
                module_name=s.module_name,
                status=s.status,
                mode="interactive", # default
                completion_percentage=s.completion_percentage,
                questions_completed=0, # not stored directly in top level usually
                total_questions=0,
                created_at=s.created_at,
                started_at=s.started_at,
                updated_at=s.updated_at
            )
            for s in sessions
        ]
    except Exception as e:
        logger.error(f"Failed to get patient history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get patient history: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for assessment service"""
    return {
        "status": "healthy",
        "service": "SCID Assessment",
        "timestamp": datetime.now().isoformat()
    }

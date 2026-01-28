"""
TPA Router - FastAPI endpoints for Treatment Planning Agent
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# Import TPA components
from .tpa_ import TreatmentPlanningAgent
from .tpa_schemas import (
    TreatmentPlanSimple, PatientDemographics, PatientGoals,
    SymptomCluster, ProvisionalDiagnosis, PatientPreferences,
    PlanGenerationRequest, PlanUpdateRequest, PlanResponse, ProgressResponse
)
from .treatment_plan_tracker import TreatmentPlanTracker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tpa", tags=["Treatment Planning Agent"])

def get_tpa_agent() -> TreatmentPlanningAgent:
    return TreatmentPlanningAgent()

def get_plan_tracker() -> TreatmentPlanTracker:
    return TreatmentPlanTracker("system")

@router.post("/generate-plan", response_model=PlanResponse)
async def generate_treatment_plan(
    request: PlanGenerationRequest,
    tpa: TreatmentPlanningAgent = Depends(get_tpa_agent),
    tracker: TreatmentPlanTracker = Depends(get_plan_tracker)
) -> PlanResponse:
    """Generate a personalized treatment plan"""
    try:
        logger.info(f"Generating treatment plan for patient: {request.patient_demographics.age}yo {request.patient_demographics.gender}")

        # Generate plan
        simple_plan = tpa.create_simple_treatment_plan(
            patient_demographics=request.patient_demographics,
            patient_goals=request.patient_goals,
            symptom_clusters=request.symptom_clusters,
            provisional_diagnosis=request.provisional_diagnosis,
            patient_preferences=request.patient_preferences,
            red_flags=request.red_flags
        )

        # Store plan
        plan_id = tracker.add_plan({
            "title": simple_plan.title,
            "goal": simple_plan.goal,
            "steps": [
                {
                    "step_id": f"step_{i+1}",
                    "title": step.title,
                    "description": step.description,
                    "frequency": step.frequency,
                    "estimated_duration": step.duration,
                    "category": "treatment",
                    "priority": 3,
                    "is_required": True
                }
                for i, step in enumerate(simple_plan.treatment_steps)
            ],
            "start_date": datetime.now().date(),
            "created_by": "TPA_API",
            "patient_id": request.patient_id or "auto_generated"
        })

        simple_plan.patient_id = plan_id

        return PlanResponse(
            plan_id=plan_id,
            plan=simple_plan,
            created_at=datetime.now(),
            status="active",
            message="Treatment plan generated successfully"
        )

    except Exception as e:
        logger.error(f"Error generating treatment plan: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate treatment plan: {str(e)}")

@router.get("/plan/{plan_id}", response_model=PlanResponse)
async def get_treatment_plan(
    plan_id: str,
    tracker: TreatmentPlanTracker = Depends(get_plan_tracker)
) -> PlanResponse:
    """Retrieve a specific treatment plan by ID"""
    try:
        plan_data = tracker.get_plan(plan_id)
        if not plan_data:
            raise HTTPException(status_code=404, detail=f"Treatment plan {plan_id} not found")

        simple_plan = TreatmentPlanSimple(
            patient_id=plan_data.patient_id,
            title=plan_data.title,
            goal="",
            top_actions=[],
            step_by_step=[],
            weekly_plan={},
            safety_note="Monitor symptoms and contact healthcare provider if needed.",
            plan_metadata={},
            tracking_schema={},
            reminder_schedule="Daily at 9 AM"
        )

        return PlanResponse(
            plan_id=plan_id,
            plan=simple_plan,
            created_at=plan_data.created_at,
            status=plan_data.status,
            message="Plan retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve plan: {str(e)}")

@router.put("/plan/{plan_id}/update", response_model=PlanResponse)
async def update_treatment_plan(
    plan_id: str,
    update_request: PlanUpdateRequest,
    tpa: TreatmentPlanningAgent = Depends(get_tpa_agent),
    tracker: TreatmentPlanTracker = Depends(get_plan_tracker)
) -> PlanResponse:
    """Update an existing treatment plan"""
    try:
        existing_plan = tracker.get_plan(plan_id)
        if not existing_plan:
            raise HTTPException(status_code=404, detail=f"Treatment plan {plan_id} not found")

        # Generate updated plan
        updated_simple_plan = tpa.create_simple_treatment_plan(
            patient_demographics=update_request.patient_demographics or PatientDemographics(
                age=30, gender="unknown", occupation=None, cultural_background=None,
                living_situation=None, support_system=None
            ),
            patient_goals=update_request.patient_goals or PatientGoals(
                primary_goals=["Improve mental health"], treatment_preferences=[],
                previous_treatments=[], success_metrics=None
            ),
            symptom_clusters=update_request.symptom_clusters or [],
            provisional_diagnosis=update_request.provisional_diagnosis or ProvisionalDiagnosis(
                primary_diagnosis="General mental health concerns",
                severity="mild",
                confidence_level=0.5
            ),
            patient_preferences=update_request.patient_preferences or PatientPreferences(
                preferred_approach="self_help", weekly_time_commitment=5,
                mode_preference="online", budget_level="low_cost"
            ),
            red_flags=update_request.red_flags
        )

        # Update plan in tracker
        tracker.update_plan(plan_id, {
            "title": updated_simple_plan.title,
            "goal": updated_simple_plan.goal,
            "steps": [
                {
                    "step_id": f"step_{i+1}",
                    "title": step.title,
                    "description": step.description,
                    "frequency": step.frequency,
                    "estimated_duration": step.duration,
                    "category": "treatment",
                    "priority": 3,
                    "is_required": True
                }
                for i, step in enumerate(updated_simple_plan.treatment_steps)
            ],
            "updated_at": datetime.now()
        })

        return PlanResponse(
            plan_id=plan_id,
            plan=updated_simple_plan,
            created_at=datetime.now(),
            status="updated",
            message="Treatment plan updated successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update plan: {str(e)}")

@router.delete("/plan/{plan_id}")
async def delete_treatment_plan(
    plan_id: str,
    tracker: TreatmentPlanTracker = Depends(get_plan_tracker)
) -> Dict[str, Any]:
    """Delete a treatment plan"""
    try:
        existing_plan = tracker.get_plan(plan_id)
        if not existing_plan:
            raise HTTPException(status_code=404, detail=f"Treatment plan {plan_id} not found")

        success = tracker.delete_plan(plan_id)

        if success:
            return {
                "plan_id": plan_id,
                "deleted": True,
                "message": "Treatment plan deleted successfully",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete plan from database")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete plan: {str(e)}")

@router.get("/plan/{plan_id}/progress", response_model=ProgressResponse)
async def get_plan_progress(
    plan_id: str,
    days: int = Query(30, description="Number of days to look back for progress data"),
    tracker: TreatmentPlanTracker = Depends(get_plan_tracker)
) -> ProgressResponse:
    """Get progress tracking data for a specific treatment plan"""
    try:
        plan_data = tracker.get_plan(plan_id)
        if not plan_data:
            raise HTTPException(status_code=404, detail=f"Treatment plan {plan_id} not found")

        progress_report = tracker.get_progress_report(plan_id=plan_id, days=days)

        return ProgressResponse(
            plan_id=plan_id,
            progress=progress_report,
            retrieved_at=datetime.now(),
            message="Progress data retrieved successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving progress for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve progress: {str(e)}")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for TPA service"""
    return {
        "service": "Treatment Planning Agent (TPA)",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

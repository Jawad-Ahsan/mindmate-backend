"""
Specialist SMA Routes - Appointment Management for Specialists
============================================================
FastAPI routes for specialist-side appointment management functionality.

Endpoints:
- Get booked appointments
- Update appointment status (confirm/reject)
- Cancel appointment
- Get patient public profile
- Get patient referral report from PIMA
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

# Import dependencies
from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token

# Import SMA components
from agents.sma.sma import SMA
from agents.sma.sma_schemas import (
    UpdateAppointmentStatusRequest, CancelAppointmentBySpecialistRequest,
    AppointmentStatus
)

# Import models for type hints
from models.sql_models.specialist_models import Specialists

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/specialist-sma", tags=["Specialist SMA"])

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_current_specialist(current_user_data: dict = Depends(get_current_user_from_token)) -> Specialists:
    """Dependency to get current authenticated specialist"""
    user = current_user_data["user"]
    user_type = current_user_data["user_type"]
    
    if user_type != "specialist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Specialist access required"
        )
    
    return user

def get_sma_service(db: Session = Depends(get_db)) -> SMA:
    """Dependency to get SMA service"""
    return SMA(db)

# ============================================================================
# APPOINTMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get(
    "/my-appointments",
    summary="Get My Appointments",
    description="""
    Get appointments for the current specialist.
    
    **Features:**
    - Paginated results
    - Filter by appointment status
    - Include patient details
    - Sort by appointment date
    
    **Returns:** Paginated list of appointments
    """,
    responses={
        200: {
            "description": "Appointments retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "appointments": [
                            {
                                "id": "uuid",
                                "patient_id": "uuid",
                                "patient_name": "John Doe",
                                "scheduled_start": "2025-01-20T10:00:00Z",
                                "scheduled_end": "2025-01-20T11:00:00Z",
                                "consultation_mode": "online",
                                "fee": 3000,
                                "status": "confirmed",
                                "notes": "Patient notes",
                                "created_at": "2025-01-15T10:00:00Z",
                                "updated_at": "2025-01-15T10:00:00Z"
                            }
                        ],
                        "total_count": 15,
                        "page": 1,
                        "size": 20,
                        "has_more": True
                    }
                }
            }
        },
        500: {"description": "Internal server error"}
    }
)
async def get_my_appointments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page"),
    
    current_specialist: Specialists = Depends(get_current_specialist),
    sma: SMA = Depends(get_sma_service)
):
    """Get appointments for current specialist"""
    
    try:
        result = sma.get_booked_appointments(
            specialist_id=current_specialist.id,
            page=page,
            size=size
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting specialist appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointments"
        )

@router.post(
    "/update-appointment-status",
    summary="Update Appointment Status",
    description="""
    Update appointment status (confirm/reject) and notify patient via email.
    
    **Features:**
    - Confirm or reject appointments
    - Automatic email notification to patient
    - Add specialist notes
    - Status tracking
    
    **Returns:** Update confirmation
    """,
    responses={
        200: {
            "description": "Appointment status updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "appointment": {
                            "id": "uuid",
                            "status": "confirmed",
                            "updated_at": "2025-01-15T10:00:00Z"
                        },
                        "message": "Appointment status updated to confirmed"
                    }
                }
            }
        },
        400: {"description": "Invalid status update request"},
        404: {"description": "Appointment not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_appointment_status(
    request: UpdateAppointmentStatusRequest,
    current_specialist: Specialists = Depends(get_current_specialist),
    sma: SMA = Depends(get_sma_service)
):
    """Update appointment status"""
    
    try:
        result = sma.update_appointment_status(current_specialist.id, request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating appointment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update appointment status"
        )

@router.post(
    "/cancel-appointment",
    summary="Cancel Appointment",
    description="""
    Cancel an appointment and notify patient via email.
    
    **Features:**
    - Cancel scheduled or confirmed appointments
    - Automatic email notification to patient
    - Add cancellation reason
    - Status tracking
    
    **Returns:** Cancellation confirmation
    """,
    responses={
        200: {
            "description": "Appointment cancelled successfully",
            "content": {
                "application/json": {
                    "example": {
                        "appointment": {
                            "id": "uuid",
                            "status": "cancelled",
                            "cancelled_at": "2025-01-15T10:00:00Z"
                        },
                        "message": "Appointment cancelled successfully"
                    }
                }
            }
        },
        400: {"description": "Appointment cannot be cancelled"},
        404: {"description": "Appointment not found"},
        500: {"description": "Internal server error"}
    }
)
async def cancel_appointment(
    request: CancelAppointmentBySpecialistRequest,
    current_specialist: Specialists = Depends(get_current_specialist),
    sma: SMA = Depends(get_sma_service)
):
    """Cancel appointment by specialist"""
    
    try:
        result = sma.cancel_appointment_by_specialist(current_specialist.id, request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel appointment"
        )

# ============================================================================
# PATIENT INFORMATION ENDPOINTS
# ============================================================================

@router.get(
    "/patient/{patient_id}/profile",
    summary="Get Patient Public Profile",
    description="""
    Get patient public profile information for the specialist.
    
    **Features:**
    - Patient basic information
    - Consultation history
    - Age and demographic data
    - City and location
    
    **Returns:** Patient public profile
    """,
    responses={
        200: {
            "description": "Patient profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "patient": {
                            "id": "uuid",
                            "first_name": "John",
                            "last_name": "Doe",
                            "age": 28,
                            "gender": "male",
                            "city": "Karachi",
                            "consultation_history": [
                                {
                                    "appointment_id": "uuid",
                                    "specialist_name": "Dr. Sara Khan",
                                    "date": "2025-01-10T10:00:00Z",
                                    "status": "completed"
                                }
                            ]
                        },
                        "message": "Patient profile retrieved successfully"
                    }
                }
            }
        },
        404: {"description": "Patient not found or no appointment history"},
        500: {"description": "Internal server error"}
    }
)
async def get_patient_public_profile(
    patient_id: uuid.UUID,
    current_specialist: Specialists = Depends(get_current_specialist),
    sma: SMA = Depends(get_sma_service)
):
    """Get patient public profile"""
    
    try:
        result = sma.get_patient_public_profile(current_specialist.id, patient_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting patient profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient profile"
        )

@router.get(
    "/patient/{patient_id}/referral-report",
    summary="Get Patient Referral Report",
    description="""
    Get patient referral report from PIMA (Patient Information Management Agent).
    
    **Features:**
    - Patient assessment report
    - Risk level analysis
    - Treatment recommendations
    - Generated by PIMA agent
    
    **Returns:** Patient referral report
    """,
    responses={
        200: {
            "description": "Patient referral report retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "report": {
                            "patient_id": "uuid",
                            "report_available": True,
                            "report_generated_at": "2025-01-15T10:00:00Z",
                            "report_type": "initial_assessment",
                            "report_summary": "Patient assessment completed by PIMA agent",
                            "risk_level": "moderate",
                            "recommendations": [
                                "Consider CBT therapy for anxiety management",
                                "Regular follow-up appointments recommended",
                                "Monitor for depressive symptoms"
                            ],
                            "generated_by": "PIMA_Agent"
                        },
                        "message": "Patient referral report retrieved successfully"
                    }
                }
            }
        },
        404: {"description": "Patient not found or no appointment history"},
        500: {"description": "Internal server error"}
    }
)
async def get_patient_referral_report(
    patient_id: uuid.UUID,
    current_specialist: Specialists = Depends(get_current_specialist),
    sma: SMA = Depends(get_sma_service)
):
    """Get patient referral report from PIMA"""
    
    try:
        result = sma.get_patient_referral_report(current_specialist.id, patient_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting patient referral report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patient referral report"
        )

"""
SMA Router - FastAPI endpoints for Specialist Matching Agent
==========================================================
API endpoints for specialist search, matching, and appointment booking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
import logging

# Import dependencies
from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token

# Import SMA components
from agents.sma.sma import SMA
from agents.sma.sma_schemas import (
    SpecialistSearchRequest, TopSpecialistsRequest, SlotHoldRequest,
    AppointmentConfirmRequest, AppointmentCancelRequest, AppointmentRescheduleRequest,
    RequestAppointmentRequest, RequestAppointmentResponse,
    SpecialistSearchResponse, TopSpecialistsResponse, SlotHoldResponse,
    AppointmentConfirmResponse, AppointmentListResponse, HealthCheckResponse,
    ConsultationMode, SortOption, SlotStatus, AppointmentStatus
)

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["Specialist Matching Agent"])

# Test endpoint to verify router is working
@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify SMA router is working"""
    return {"message": "SMA router is working", "status": "ok"}

# Simple test endpoint without dependencies
@router.get("/test-simple")
async def test_simple_endpoint():
    """Simple test endpoint without any dependencies"""
    return {"message": "Simple test endpoint working", "status": "ok"}

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_sma(db: Session = Depends(get_db)) -> SMA:
    """Dependency to get SMA instance"""
    return SMA(db)

def get_current_patient(current_user_data: dict = Depends(get_current_user_from_token)):
    """Dependency to get current authenticated patient"""
    user = current_user_data["user"]
    user_type = current_user_data["user_type"]
    
    if user_type != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient access required"
        )
    
    return user

def get_current_specialist(current_user_data: dict = Depends(get_current_user_from_token)):
    """Dependency to get current authenticated specialist"""
    user = current_user_data["user"]
    user_type = current_user_data["user_type"]
    
    if user_type != "specialist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Specialist access required"
        )
    
    return user

# ============================================================================
# SPECIALIST SEARCH ENDPOINTS
# ============================================================================

@router.get(
    "/specialists/search",
    response_model=SpecialistSearchResponse,
    summary="Search Specialists",
    description="""
    Search and filter specialists based on various criteria.
    
    **Features:**
    - Filter by specialist type, location, specializations
    - Sort by best match, rating, experience, fee
    - Pagination support
    - Automatic ranking based on preferences
    
    **Access:** All authenticated users
    """,
    responses={
        200: {"description": "Specialists found successfully"},
        400: {"description": "Invalid search parameters"},
        500: {"description": "Internal server error"}
    }
)
async def search_specialists(
    # Search parameters
    query: Optional[str] = Query(None, description="Free text search query"),
    specialist_type: Optional[str] = Query(None, description="Type of specialist"),
    consultation_mode: Optional[ConsultationMode] = Query(None, description="Preferred consultation mode"),
    city: Optional[str] = Query(None, description="City for in-person consultations"),
    languages: Optional[str] = Query(None, description="Comma-separated list of preferred languages"),
    specializations: Optional[str] = Query(None, description="Comma-separated list of required specializations"),
    budget_max: Optional[float] = Query(None, ge=0, description="Maximum budget in PKR"),
    
    # Sorting and pagination
    sort_by: SortOption = Query(SortOption.BEST_MATCH, description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page"),
    
    # Availability constraints
    available_from: Optional[datetime] = Query(None, description="Earliest available date"),
    available_to: Optional[datetime] = Query(None, description="Latest available date"),
    
    # Dependencies
    sma: SMA = Depends(get_sma)
):
    """Search specialists with filters and pagination"""
    
    logger.info(f"Search specialists endpoint called with params: query={query}, page={page}, size={size}")
    
    try:
        # Parse comma-separated lists
        languages_list = languages.split(",") if languages else None
        specializations_list = specializations.split(",") if specializations else None
        
        # Build request
        request = SpecialistSearchRequest(
            query=query,
            specialist_type=specialist_type,
            consultation_mode=consultation_mode,
            city=city,
            languages=languages_list,
            specializations=specializations_list,
            budget_max=budget_max,
            sort_by=sort_by,
            page=page,
            size=size,
            available_from=available_from,
            available_to=available_to
        )
        
        # Perform search
        result = sma.search_specialists(request)
        
        return SpecialistSearchResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in specialist search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/specialists/top",
    response_model=TopSpecialistsResponse,
    summary="Get Top Specialists",
    description="""
    Get top N specialists with scoring rationale.
    
    **Features:**
    - Returns best matches with scoring breakdown
    - Explains why each specialist was recommended
    - Useful for recommendation systems
    
    **Access:** All authenticated users
    """,
    responses={
        200: {"description": "Top specialists retrieved successfully"},
        400: {"description": "Invalid request parameters"},
        500: {"description": "Internal server error"}
    }
)
async def get_top_specialists(
    request: TopSpecialistsRequest,
    sma: SMA = Depends(get_sma)
):
    """Get top specialists with scoring rationale"""
    
    try:
        result = sma.get_top_specialists(request)
        return TopSpecialistsResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting top specialists: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/specialists/{specialist_id}",
    summary="Get Specialist Details",
    description="""
    Get detailed specialist information including availability.
    
    **Features:**
    - Complete specialist profile
    - Available appointment slots
    - Contact and practice information
    
    **Access:** All authenticated users
    """,
    responses={
        200: {"description": "Specialist details retrieved successfully"},
        404: {"description": "Specialist not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_specialist_details(
    specialist_id: uuid.UUID,
    include_slots: bool = Query(True, description="Include available slots"),
    sma: SMA = Depends(get_sma)
):
    """Get detailed specialist information"""
    
    try:
        result = sma.get_specialist_details(specialist_id, include_slots)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting specialist details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/specialists/{specialist_id}/slots",
    summary="Get Specialist Slots",
    description="""
    Get available appointment slots for a specialist.
    
    **Features:**
    - Filter by date range and status
    - Real-time availability
    - Slot details for booking
    
    **Access:** All authenticated users
    """,
    responses={
        200: {"description": "Slots retrieved successfully"},
        404: {"description": "Specialist not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_specialist_slots(
    specialist_id: uuid.UUID,
    from_date: Optional[datetime] = Query(None, description="Start date for slot search"),
    to_date: Optional[datetime] = Query(None, description="End date for slot search"),
    status: Optional[SlotStatus] = Query(None, description="Filter by slot status"),
    sma: SMA = Depends(get_sma)
):
    """Get available slots for a specialist"""
    
    try:
        slots = sma.get_specialist_slots(specialist_id, from_date, to_date, status)
        return {"slots": slots}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting specialist slots: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# APPOINTMENT BOOKING ENDPOINTS
# ============================================================================

@router.post(
    "/appointments/hold",
    response_model=SlotHoldResponse,
    summary="Hold Appointment Slot",
    description="""
    Hold a slot for booking (step 1 of booking process).
    
    **Process:**
    1. Hold slot for specified duration
    2. Return hold token for confirmation
    3. Slot becomes unavailable to others
    
    **Access:** Authenticated patients
    """,
    responses={
        200: {"description": "Slot held successfully"},
        400: {"description": "Invalid slot or patient"},
        409: {"description": "Slot already held"},
        500: {"description": "Internal server error"}
    }
)
async def hold_slot(
    request: SlotHoldRequest,
    current_patient = Depends(get_current_patient),
    sma: SMA = Depends(get_sma)
):
    """Hold a slot for booking"""
    
    try:
        # Ensure patient is booking for themselves
        if str(request.patient_id) != str(current_patient.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only hold slots for yourself"
            )
        
        result = sma.hold_slot(request)
        return SlotHoldResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error holding slot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/appointments/confirm",
    response_model=AppointmentConfirmResponse,
    summary="Confirm Appointment",
    description="""
    Confirm an appointment using hold token (step 2 of booking process).
    
    **Process:**
    1. Validate hold token
    2. Create appointment record
    3. Mark slot as booked
    4. Send confirmation
    
    **Access:** Authenticated patients
    """,
    responses={
        200: {"description": "Appointment confirmed successfully"},
        400: {"description": "Invalid hold token or request"},
        410: {"description": "Hold token expired"},
        500: {"description": "Internal server error"}
    }
)
async def confirm_appointment(
    request: AppointmentConfirmRequest,
    current_patient = Depends(get_current_patient),
    sma: SMA = Depends(get_sma)
):
    """Confirm an appointment using hold token"""
    
    try:
        result = sma.confirm_appointment(request)
        return AppointmentConfirmResponse(**result)
        
    except ValueError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error confirming appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# APPOINTMENT REQUEST ENDPOINTS
# ============================================================================

@router.post(
    "/appointments/request",
    response_model=RequestAppointmentResponse,
    summary="Request Appointment",
    description="""
    Request an appointment with a specialist (requires approval).
    
    **Process:**
    1. Patient requests appointment with specialist
    2. Specialist receives notification
    3. Specialist can approve/reject the request
    4. Patient is notified of the decision
    
    **Access:** Authenticated patients
    """,
    responses={
        200: {"description": "Appointment request sent successfully"},
        400: {"description": "Invalid request parameters"},
        404: {"description": "Specialist not found"},
        500: {"description": "Internal server error"}
    }
)
async def request_appointment(
    request: RequestAppointmentRequest,
    current_patient = Depends(get_current_patient),
    sma: SMA = Depends(get_sma)
):
    """Request an appointment with a specialist"""
    
    try:
        result = sma.request_appointment(current_patient.id, request)
        return RequestAppointmentResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error requesting appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# APPOINTMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get(
    "/appointments/my-appointments",
    response_model=AppointmentListResponse,
    summary="Get My Appointments",
    description="""
    Get appointments for the current authenticated patient.
    
    **Features:**
    - Paginated results
    - Filter by appointment status
    - Include specialist details
    - Sort by appointment date
    
    **Access:** Authenticated patients (own appointments)
    """,
    responses={
        200: {"description": "Appointments retrieved successfully"},
        500: {"description": "Internal server error"}
    }
)
async def get_my_appointments(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page"),
    status_filter: Optional[AppointmentStatus] = Query(None, description="Filter by appointment status"),
    
    current_patient = Depends(get_current_patient),
    sma: SMA = Depends(get_sma)
):
    """Get appointments for the current authenticated patient"""
    
    try:
        result = sma.get_patient_appointments(current_patient.id, page, size, status_filter.value if status_filter else None)
        return AppointmentListResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting patient appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve appointments"
        )

@router.get(
    "/appointments/patient/{patient_id}",
    response_model=AppointmentListResponse,
    summary="Get Patient Appointments",
    description="""
    Get appointments for a patient.
    
    **Features:**
    - Paginated appointment history
    - Filter by appointment status
    - Sorted by date (newest first)
    
    **Access:** Patient (own appointments) or authorized users
    """,
    responses={
        200: {"description": "Appointments retrieved successfully"},
        403: {"description": "Access denied"},
        404: {"description": "Patient not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_patient_appointments(
    patient_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by appointment status"),
    current_patient = Depends(get_current_patient),
    sma: SMA = Depends(get_sma)
):
    """Get appointments for a patient"""
    
    try:
        # Ensure patient is accessing their own appointments
        if str(patient_id) != str(current_patient.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only access your own appointments"
            )
        
        result = sma.get_patient_appointments(patient_id, page, size, status)
        return AppointmentListResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting patient appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/appointments/specialist/{specialist_id}",
    response_model=AppointmentListResponse,
    summary="Get Specialist Appointments",
    description="""
    Get appointments for a specialist.
    
    **Features:**
    - Paginated appointment list
    - Filter by date range and status
    - Sorted by date (oldest first)
    
    **Access:** Specialist (own appointments) or authorized users
    """,
    responses={
        200: {"description": "Appointments retrieved successfully"},
        403: {"description": "Access denied"},
        404: {"description": "Specialist not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_specialist_appointments(
    specialist_id: uuid.UUID,
    from_date: Optional[datetime] = Query(None, description="Start date filter"),
    to_date: Optional[datetime] = Query(None, description="End date filter"),
    status: Optional[AppointmentStatus] = Query(None, description="Filter by appointment status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Results per page"),
    current_specialist = Depends(get_current_specialist),
    sma: SMA = Depends(get_sma)
):
    """Get appointments for a specialist"""
    
    try:
        # Ensure specialist is accessing their own appointments
        if str(specialist_id) != str(current_specialist.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only access your own appointments"
            )
        
        result = sma.get_specialist_appointments(
            specialist_id, from_date, to_date, status, page, size
        )
        return AppointmentListResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting specialist appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.patch(
    "/appointments/{appointment_id}/cancel",
    summary="Cancel Appointment",
    description="""
    Cancel an appointment.
    
    **Features:**
    - Cancel by patient or specialist
    - Provide cancellation reason
    - Update appointment status
    
    **Access:** Patient or specialist (own appointments)
    """,
    responses={
        200: {"description": "Appointment cancelled successfully"},
        400: {"description": "Cannot cancel appointment"},
        403: {"description": "Access denied"},
        404: {"description": "Appointment not found"},
        500: {"description": "Internal server error"}
    }
)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    request: AppointmentCancelRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    sma: SMA = Depends(get_sma)
):
    """Cancel an appointment"""
    
    try:
        result = sma.cancel_appointment(appointment_id, request)
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
            detail="Internal server error"
        )

@router.patch(
    "/appointments/{appointment_id}/reschedule",
    summary="Reschedule Appointment",
    description="""
    Reschedule an appointment to a new slot.
    
    **Process:**
    1. Cancel original appointment
    2. Create new appointment with new slot
    3. Link to original appointment
    
    **Access:** Patient or specialist (own appointments)
    """,
    responses={
        200: {"description": "Appointment rescheduled successfully"},
        400: {"description": "Cannot reschedule appointment"},
        403: {"description": "Access denied"},
        404: {"description": "Appointment not found"},
        500: {"description": "Internal server error"}
    }
)
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    request: AppointmentRescheduleRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    sma: SMA = Depends(get_sma)
):
    """Reschedule an appointment"""
    
    try:
        result = sma.reschedule_appointment(appointment_id, request)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rescheduling appointment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@router.get(
    "/recommendations/{patient_id}",
    summary="Get Personalized Recommendations",
    description="""
    Get personalized specialist recommendations for a patient.
    
    **Features:**
    - Based on patient profile and preferences
    - Scoring rationale included
    - Integration with other MindMate agents
    
    **Access:** Patient (own recommendations) or authorized users
    """,
    responses={
        200: {"description": "Recommendations generated successfully"},
        403: {"description": "Access denied"},
        404: {"description": "Patient not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_recommendations(
    patient_id: uuid.UUID,
    specializations: Optional[str] = Query(None, description="Comma-separated specializations"),
    consultation_mode: Optional[ConsultationMode] = Query(None, description="Preferred consultation mode"),
    budget_max: Optional[float] = Query(None, ge=0, description="Maximum budget"),
    limit: int = Query(3, ge=1, le=10, description="Number of recommendations"),
    current_patient = Depends(get_current_patient),
    sma: SMA = Depends(get_sma)
):
    """Get personalized specialist recommendations"""
    
    try:
        # Ensure patient is accessing their own recommendations
        if str(patient_id) != str(current_patient.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Can only access your own recommendations"
            )
        
        # Parse specializations
        specializations_list = specializations.split(",") if specializations else None
        
        result = sma.get_matching_recommendations(
            patient_id=patient_id,
            specializations=specializations_list,
            consultation_mode=consultation_mode,
            budget_max=budget_max,
            limit=limit
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Health check endpoint for SMA service"
)
async def health_check(sma: SMA = Depends(get_sma)):
    """Health check endpoint"""
    
    try:
        result = sma.get_health_status()
        return HealthCheckResponse(**result)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthCheckResponse(
            status="unhealthy",
            service="sma",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            message=f"Health check failed: {str(e)}"
        )

@router.post(
    "/cleanup",
    summary="Cleanup Expired Holds",
    description="Clean up expired slot holds (admin/maintenance endpoint)"
)
async def cleanup_expired_holds(sma: SMA = Depends(get_sma)):
    """Clean up expired holds"""
    
    try:
        cleaned_count = sma.cleanup_expired_holds()
        return {
            "message": f"Cleaned up {cleaned_count} expired holds",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired holds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

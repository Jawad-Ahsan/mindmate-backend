"""
Enhanced Specialist Routes - Advanced Filtering and Management
============================================================
FastAPI routes for specialist dashboard with enhanced filtering capabilities.

Features:
- Advanced appointment filtering by status, date, patient type
- Patient management with status tracking
- Session management with notes and progress tracking
- Real-time dashboard statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List
from datetime import datetime, timedelta, timezone
import logging

# Import dependencies
from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token

# Import models
from models.sql_models.specialist_models import Specialists
from models.sql_models.appointments_model import Appointment, AppointmentStatusEnum
from models.sql_models.patient_models import Patient
from models.sql_models.base_model import Base

# Import schemas
from models.pydantic_models.specialist_appointment_schemas import (
    AppointmentFilterRequest, PatientFilterRequest, SessionFilterRequest,
    UpdateAppointmentStatusRequest, UpdatePatientStatusRequest, AddSessionNotesRequest,
    FilteredAppointmentsResponse, FilteredPatientsResponse, FilteredSessionsResponse,
    StatusUpdateResponse, DashboardStats, AppointmentSummary, PatientSummary, SessionSummary,
    AppointmentFilterStatus, PatientStatus, SessionFilterType
)

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/specialist", tags=["Enhanced Specialist"])

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

# ============================================================================
# ENHANCED APPOINTMENT FILTERING
# ============================================================================

@router.post(
    "/appointments/filter",
    response_model=FilteredAppointmentsResponse,
    summary="Filter Appointments",
    description="""
    Get filtered appointments for the current specialist based on various criteria.
    
    **Filters:**
    - Status: pending_approval, scheduled, confirmed, completed, cancelled, no_show
    - Date range: from and to dates
    - Patient type: new, active, follow_up, discharged
    - Pagination support
    
    **Returns:** Filtered list of appointments with metadata
    """
)
async def filter_appointments(
    request: AppointmentFilterRequest,
    current_specialist: Specialists = Depends(get_current_specialist),
    db: Session = Depends(get_db)
):
    """Filter appointments based on various criteria"""
    
    try:
        # Build base query
        query = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id
        )
        
        # Apply status filter
        if request.status and request.status != AppointmentFilterStatus.ALL:
            status_mapping = {
                AppointmentFilterStatus.PENDING_APPROVAL: AppointmentStatusEnum.PENDING_APPROVAL,
                AppointmentFilterStatus.SCHEDULED: AppointmentStatusEnum.SCHEDULED,
                AppointmentFilterStatus.CONFIRMED: AppointmentStatusEnum.CONFIRMED,
                AppointmentFilterStatus.COMPLETED: AppointmentStatusEnum.COMPLETED,
                AppointmentFilterStatus.CANCELLED: AppointmentStatusEnum.CANCELLED,
                AppointmentFilterStatus.NO_SHOW: AppointmentStatusEnum.NO_SHOW,
            }
            query = query.filter(Appointment.status == status_mapping[request.status])
        
        # Apply date filters
        if request.date_from:
            query = query.filter(Appointment.scheduled_start >= request.date_from)
        if request.date_to:
            query = query.filter(Appointment.scheduled_start <= request.date_to)
        
        # Apply patient type filter (this would require additional patient status tracking)
        # For now, we'll implement basic filtering
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.order_by(desc(Appointment.scheduled_start))
        query = query.offset((request.page - 1) * request.size).limit(request.size)
        
        # Execute query
        appointments = query.all()
        
        # Convert to response format
        appointment_summaries = []
        for apt in appointments:
            # Get patient details
            patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
            if patient:
                # Map AppointmentStatusEnum to AppointmentFilterStatus
                status_mapping = {
                    AppointmentStatusEnum.PENDING_APPROVAL: AppointmentFilterStatus.PENDING_APPROVAL,
                    AppointmentStatusEnum.SCHEDULED: AppointmentFilterStatus.SCHEDULED,
                    AppointmentStatusEnum.CONFIRMED: AppointmentFilterStatus.CONFIRMED,
                    AppointmentStatusEnum.COMPLETED: AppointmentFilterStatus.COMPLETED,
                    AppointmentStatusEnum.CANCELLED: AppointmentFilterStatus.CANCELLED,
                    AppointmentStatusEnum.NO_SHOW: AppointmentFilterStatus.NO_SHOW,
                }
                
                summary = AppointmentSummary(
                    id=str(apt.id),
                    patient_id=str(apt.patient_id),
                    patient_name=f"{patient.first_name} {patient.last_name}",
                    patient_email=patient.email,
                    scheduled_start=apt.scheduled_start,
                    scheduled_end=apt.scheduled_end,
                    status=status_mapping[apt.status],
                    appointment_type=apt.appointment_type.value,
                    fee=apt.fee,
                    notes=apt.notes,
                    session_notes=apt.session_notes,
                    created_at=apt.created_at,
                    updated_at=apt.updated_at
                )
                appointment_summaries.append(summary)
        
        # Build filters applied dict
        filters_applied = {
            "status": request.status.value if request.status else None,
            "date_from": request.date_from.isoformat() if request.date_from else None,
            "date_to": request.date_to.isoformat() if request.date_to else None,
            "patient_type": request.patient_type.value if request.patient_type else None,
            "page": request.page,
            "size": request.size
        }
        
        return FilteredAppointmentsResponse(
            appointments=appointment_summaries,
            total_count=total_count,
            page=request.page,
            size=request.size,
            has_more=total_count > request.page * request.size,
            filters_applied=filters_applied
        )
        
    except Exception as e:
        logger.error(f"Error filtering appointments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter appointments"
        )

@router.put(
    "/appointments/{appointment_id}/status",
    response_model=StatusUpdateResponse,
    summary="Update Appointment Status",
    description="""
    Update appointment status and add notes.
    
    **Status Transitions:**
    - pending_approval → scheduled/confirmed/rejected
    - scheduled → confirmed/completed/cancelled
    - confirmed → completed/cancelled/no_show
    
    **Returns:** Status update confirmation
    """
)
async def update_appointment_status(
    appointment_id: str,
    request: UpdateAppointmentStatusRequest,
    current_specialist: Specialists = Depends(get_current_specialist),
    db: Session = Depends(get_db)
):
    """Update appointment status"""
    
    try:
        # Find appointment
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.specialist_id == current_specialist.id
        ).first()
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Validate status transition
        valid_transitions = {
            AppointmentStatusEnum.PENDING_APPROVAL: [
                AppointmentStatusEnum.SCHEDULED,
                AppointmentStatusEnum.CONFIRMED
            ],
            AppointmentStatusEnum.SCHEDULED: [
                AppointmentStatusEnum.CONFIRMED,
                AppointmentStatusEnum.COMPLETED,
                AppointmentStatusEnum.CANCELLED
            ],
            AppointmentStatusEnum.CONFIRMED: [
                AppointmentStatusEnum.COMPLETED,
                AppointmentStatusEnum.CANCELLED,
                AppointmentStatusEnum.NO_SHOW
            ]
        }
        
        current_status = appointment.status
        new_status = AppointmentStatusEnum(request.new_status)
        
        if current_status in valid_transitions and new_status not in valid_transitions[current_status]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {current_status.value} to {new_status.value}"
            )
        
        # Update status
        appointment.status = new_status
        appointment.notes = request.notes or appointment.notes
        
        # Add session notes if completing
        if new_status == AppointmentStatusEnum.COMPLETED and request.session_notes:
            appointment.session_notes = request.session_notes
        
        # Update timestamp
        appointment.updated_at = datetime.now(timezone.utc)
        
        # Commit changes
        db.commit()
        
        return StatusUpdateResponse(
            success=True,
            message=f"Appointment status updated to {new_status.value}",
            updated_item={
                "id": str(appointment.id),
                "status": new_status.value,
                "updated_at": appointment.updated_at
            },
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update appointment status"
        )

# ============================================================================
# ENHANCED PATIENT MANAGEMENT
# ============================================================================

@router.post(
    "/patients/filter",
    response_model=FilteredPatientsResponse,
    summary="Filter Patients",
    description="""
    Get filtered patients for the current specialist based on various criteria.
    
    **Filters:**
    - Status: new, active, follow_up, discharged
    - Search: by name or email
    - Pagination support
    
    **Returns:** Filtered list of patients with metadata
    """
)
async def filter_patients(
    request: PatientFilterRequest,
    current_specialist: Specialists = Depends(get_current_specialist),
    db: Session = Depends(get_db)
):
    """Filter patients based on various criteria"""
    
    try:
        # Build base query - get patients who have appointments with this specialist
        query = db.query(Patient).join(Appointment).filter(
            Appointment.specialist_id == current_specialist.id
        ).distinct()
        
        # Apply status filter (this would require additional patient status tracking)
        # For now, we'll implement basic filtering
        
        # Apply search filter
        if request.search_query:
            search_term = f"%{request.search_query}%"
            query = query.filter(
                or_(
                    Patient.first_name.ilike(search_term),
                    Patient.last_name.ilike(search_term),
                    Patient.email.ilike(search_term)
                )
            )
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.order_by(desc(Patient.created_at))
        query = query.offset((request.page - 1) * request.size).limit(request.size)
        
        # Execute query
        patients = query.all()
        
        # Convert to response format
        patient_summaries = []
        for patient in patients:
            # Get patient statistics
            total_sessions = db.query(Appointment).filter(
                Appointment.patient_id == patient.id,
                Appointment.specialist_id == current_specialist.id,
                Appointment.status.in_([
                    AppointmentStatusEnum.COMPLETED,
                    AppointmentStatusEnum.CONFIRMED
                ])
            ).count()
            
            # Get last session date
            last_session = db.query(Appointment).filter(
                Appointment.patient_id == patient.id,
                Appointment.specialist_id == current_specialist.id,
                Appointment.status == AppointmentStatusEnum.COMPLETED
            ).order_by(desc(Appointment.scheduled_start)).first()
            
            # For now, set a default status (this would be enhanced with patient status tracking)
            patient_status = PatientStatus.ACTIVE if total_sessions > 0 else PatientStatus.NEW
            
            summary = PatientSummary(
                id=str(patient.id),
                first_name=patient.first_name,
                last_name=patient.last_name,
                email=patient.email,
                phone=patient.phone,
                status=patient_status,
                last_session_date=last_session.scheduled_start if last_session else None,
                next_followup_date=None,  # Would be enhanced with follow-up tracking
                total_sessions=total_sessions,
                created_at=patient.created_at
            )
            patient_summaries.append(summary)
        
        # Build filters applied dict
        filters_applied = {
            "status": request.status.value if request.status else None,
            "search_query": request.search_query,
            "page": request.page,
            "size": request.size
        }
        
        return FilteredPatientsResponse(
            patients=patient_summaries,
            total_count=total_count,
            page=request.page,
            size=request.size,
            has_more=total_count > request.page * request.size,
            filters_applied=filters_applied
        )
        
    except Exception as e:
        logger.error(f"Error filtering patients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter patients"
        )

# ============================================================================
# ENHANCED SESSION MANAGEMENT
# ============================================================================

@router.post(
    "/sessions/filter",
    response_model=FilteredSessionsResponse,
    summary="Filter Sessions",
    description="""
    Get filtered sessions for the current specialist based on various criteria.
    
    **Filters:**
    - Type: today, upcoming, completed, all
    - Date range: from and to dates
    - Pagination support
    
    **Returns:** Filtered list of sessions with metadata
    """
)
async def filter_sessions(
    request: SessionFilterRequest,
    current_specialist: Specialists = Depends(get_current_specialist),
    db: Session = Depends(get_db)
):
    """Filter sessions based on various criteria"""
    
    try:
        # Build base query - sessions are appointments with the specialist
        query = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id
        )
        
        # Apply filter type
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        if request.filter_type == SessionFilterType.TODAY:
            query = query.filter(
                and_(
                    Appointment.scheduled_start >= today_start,
                    Appointment.scheduled_start < today_end
                )
            )
        elif request.filter_type == SessionFilterType.UPCOMING:
            query = query.filter(
                Appointment.scheduled_start > now
            )
        elif request.filter_type == SessionFilterType.COMPLETED:
            query = query.filter(
                Appointment.status == AppointmentStatusEnum.COMPLETED
            )
        # ALL shows everything
        
        # Apply date filters
        if request.date_from:
            query = query.filter(Appointment.scheduled_start >= request.date_from)
        if request.date_to:
            query = query.filter(Appointment.scheduled_start <= request.date_to)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        query = query.order_by(desc(Appointment.scheduled_start))
        query = query.offset((request.page - 1) * request.size).limit(request.size)
        
        # Execute query
        appointments = query.all()
        
        # Convert to response format
        session_summaries = []
        for apt in appointments:
            # Get patient details
            patient = db.query(Patient).filter(Patient.id == apt.patient_id).first()
            if patient:
                summary = SessionSummary(
                    id=str(apt.id),
                    appointment_id=str(apt.id),
                    patient_name=f"{patient.first_name} {patient.last_name}",
                    session_date=apt.scheduled_start or apt.created_at,
                    status=apt.status.value,
                    notes=apt.notes,
                    mood_rating=None,  # Would be enhanced with mood tracking
                    progress_notes=apt.session_notes
                )
                session_summaries.append(summary)
        
        # Build filters applied dict
        filters_applied = {
            "filter_type": request.filter_type.value,
            "date_from": request.date_from.isoformat() if request.date_from else None,
            "date_to": request.date_to.isoformat() if request.date_to else None,
            "page": request.page,
            "size": request.size
        }
        
        return FilteredSessionsResponse(
            sessions=session_summaries,
            total_count=total_count,
            page=request.page,
            size=request.size,
            has_more=total_count > request.page * request.size,
            filters_applied=filters_applied
        )
        
    except Exception as e:
        logger.error(f"Error filtering sessions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter sessions"
        )

@router.post(
    "/sessions/{appointment_id}/notes",
    response_model=StatusUpdateResponse,
    summary="Add Session Notes",
    description="""
    Add or update session notes for a completed appointment.
    
    **Features:**
    - Session notes and progress tracking
    - Mood rating (1-10 scale)
    - Next steps planning
    
    **Returns:** Notes update confirmation
    """
)
async def add_session_notes(
    appointment_id: str,
    request: AddSessionNotesRequest,
    current_specialist: Specialists = Depends(get_current_specialist),
    db: Session = Depends(get_db)
):
    """Add or update session notes"""
    
    try:
        # Find appointment
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.specialist_id == current_specialist.id
        ).first()
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appointment not found"
            )
        
        # Update session notes
        appointment.session_notes = request.notes
        appointment.notes = request.progress_notes or appointment.notes
        appointment.updated_at = datetime.now(timezone.utc)
        
        # Commit changes
        db.commit()
        
        return StatusUpdateResponse(
            success=True,
            message="Session notes updated successfully",
            updated_item={
                "id": str(appointment.id),
                "session_notes": appointment.session_notes,
                "updated_at": appointment.updated_at
            },
            timestamp=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding session notes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add session notes"
        )

# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

@router.get(
    "/dashboard/stats",
    response_model=DashboardStats,
    summary="Get Dashboard Statistics",
    description="""
    Get comprehensive dashboard statistics for the current specialist.
    
    **Statistics:**
    - Appointment counts by status
    - Patient counts by status
    - Session counts by type
    - Real-time data
    
    **Returns:** Dashboard statistics
    """
)
async def get_dashboard_stats(
    current_specialist: Specialists = Depends(get_current_specialist),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for specialist"""
    
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Get appointment statistics
        total_appointments = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id
        ).count()
        
        pending_approvals = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id,
            Appointment.status == AppointmentStatusEnum.PENDING_APPROVAL
        ).count()
        
        scheduled_appointments = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id,
            Appointment.status == AppointmentStatusEnum.SCHEDULED
        ).count()
        
        completed_sessions = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id,
            Appointment.status == AppointmentStatusEnum.COMPLETED
        ).count()
        
        # Get patient statistics
        total_patients = db.query(Patient).join(Appointment).filter(
            Appointment.specialist_id == current_specialist.id
        ).distinct().count()
        
        # For now, use basic logic for patient status counts
        # This would be enhanced with proper patient status tracking
        new_patients = db.query(Patient).join(Appointment).filter(
            Appointment.specialist_id == current_specialist.id,
            Appointment.status == AppointmentStatusEnum.PENDING_APPROVAL
        ).distinct().count()
        
        active_patients = db.query(Patient).join(Appointment).filter(
            Appointment.specialist_id == current_specialist.id,
            Appointment.status.in_([
                AppointmentStatusEnum.SCHEDULED,
                AppointmentStatusEnum.CONFIRMED
            ])
        ).distinct().count()
        
        # Get session statistics
        today_sessions = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id,
            and_(
                Appointment.scheduled_start >= today_start,
                Appointment.scheduled_start < today_end
            )
        ).count()
        
        upcoming_sessions = db.query(Appointment).filter(
            Appointment.specialist_id == current_specialist.id,
            Appointment.scheduled_start > now
        ).count()
        
        return DashboardStats(
            total_appointments=total_appointments,
            pending_approvals=pending_approvals,
            scheduled_appointments=scheduled_appointments,
            completed_sessions=completed_sessions,
            total_patients=total_patients,
            new_patients=new_patients,
            active_patients=active_patients,
            today_sessions=today_sessions,
            upcoming_sessions=upcoming_sessions
        )
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics"
        )

"""
Admin Router - API endpoints for admin operations
================================================
Handles admin-specific operations like user management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from models.sql_models.patient_models import Patient, PatientAuthInfo
from models.sql_models.specialist_models import Specialists, SpecialistsAuthInfo, SpecialistsApprovalData
from models.sql_models.admin_models import Admin, AdminRoleEnum
from models.sql_models.forum_models import ForumReport, ForumQuestion, ForumAnswer

router = APIRouter(prefix="/admin", tags=["Admin"])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

from pydantic import BaseModel, ConfigDict

class PatientResponse(BaseModel):
    """Patient response model for admin view"""
    id: str
    email: str
    full_name: str
    phone: str | None
    date_of_birth: datetime | None
    city: str | None
    district: str | None
    province: str | None
    country: str | None
    is_active: bool
    created_at: datetime
    last_login: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class SpecialistResponse(BaseModel):
    """Specialist response model for admin view"""
    id: str
    email: str
    full_name: str
    phone: str | None
    city: str | None
    specialist_type: str | None
    years_experience: int | None
    approval_status: str
    created_at: datetime
    last_login: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class ForumReportAdminResponse(BaseModel):
    """Forum report response model for admin view"""
    id: str
    post_id: str
    post_type: str
    reason: str | None
    status: str
    reporter_name: str
    reporter_type: str
    created_at: datetime
    post_content: str
    post_author_name: str
    moderated_by: str | None
    moderated_at: datetime | None
    moderation_notes: str | None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )

class ReportActionRequest(BaseModel):
    """Request model for taking action on a report"""
    action: str  # "keep" or "remove"
    notes: str | None = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def verify_admin_permissions(current_user_data: dict) -> Admin:
    """Verify that the current user is an admin with proper permissions"""
    user = current_user_data.get("user")
    user_type = current_user_data.get("user_type")
    
    if not user or user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    
    # Check if user is admin or super admin
    if not hasattr(user, 'role') or user.role not in [AdminRoleEnum.ADMIN, AdminRoleEnum.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    
    return user

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.get("/patients", response_model=List[PatientResponse])
async def get_all_patients(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all registered patients (admin only)"""
    try:
        # Verify admin permissions
        admin_user = verify_admin_permissions(current_user_data)
        
        # Get all patients with their auth info
        patients = db.query(Patient).filter(
            Patient.is_deleted == False
        ).all()
        
        result = []
        for patient in patients:
            # Get auth info for each patient
            auth_info = db.query(PatientAuthInfo).filter(
                PatientAuthInfo.patient_id == patient.id
            ).first()
            
            result.append(PatientResponse(
                id=str(patient.id),
                email=patient.email,
                full_name=f"{patient.first_name} {patient.last_name}",
                phone=patient.phone,
                date_of_birth=patient.date_of_birth,
                city=patient.city,
                district=patient.district,
                province=patient.province,
                country=patient.country,
                is_active=auth_info.is_active if auth_info else False,
                created_at=patient.created_at,
                last_login=auth_info.last_login if auth_info else None
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching patients: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve patients"
        )

@router.delete("/patients/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Permanently delete a patient (admin only)"""
    try:
        # Verify admin permissions
        admin_user = verify_admin_permissions(current_user_data)
        
        # Find the patient
        patient = db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.is_deleted == False
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient not found"
            )
        
        # Get patient auth info
        auth_info = db.query(PatientAuthInfo).filter(
            PatientAuthInfo.patient_id == patient.id
        ).first()
        
        # Permanently delete the patient and all related data
        if auth_info:
            db.delete(auth_info)
        
        # Delete the patient (this will cascade to related data due to relationships)
        db.delete(patient)
        db.commit()
        
        return {"message": "Patient deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting patient: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete patient"
        )

# ============================================================================
# SPECIALIST MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/specialists", response_model=List[SpecialistResponse])
async def get_all_specialists(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all registered specialists (admin only)"""
    try:
        # Verify admin permissions
        admin_user = verify_admin_permissions(current_user_data)
        
        # Get all specialists with their auth info
        specialists = db.query(Specialists).filter(
            Specialists.is_deleted == False
        ).all()
        
        result = []
        for specialist in specialists:
            # Get auth info for each specialist
            auth_info = db.query(SpecialistsAuthInfo).filter(
                SpecialistsAuthInfo.specialist_id == specialist.id
            ).first()
            
            result.append(SpecialistResponse(
                id=str(specialist.id),
                email=specialist.email,
                full_name=f"{specialist.first_name} {specialist.last_name}",
                phone=specialist.phone,
                city=specialist.city,
                specialist_type=specialist.specialist_type.value if specialist.specialist_type else None,
                years_experience=specialist.years_experience,
                approval_status=specialist.approval_status.value if specialist.approval_status else "pending",
                created_at=specialist.created_at,
                last_login=auth_info.last_login_at if auth_info else None
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching specialists: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve specialists"
        )

@router.post("/specialists/{specialist_id}/approve")
async def approve_specialist(
    specialist_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Approve a specialist (admin only)"""
    try:
        # Verify admin permissions
        admin_user = verify_admin_permissions(current_user_data)
        
        # Find the specialist
        specialist = db.query(Specialists).filter(
            Specialists.id == specialist_id,
            Specialists.is_deleted == False
        ).first()
        
        if not specialist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specialist not found"
            )
        
        # Update approval status
        specialist.approval_status = "approved"
        specialist.availability_status = "accepting_new_patients"
        
        db.commit()
        
        return {"message": "Specialist approved successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error approving specialist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve specialist"
        )

@router.post("/specialists/{specialist_id}/reject")
async def reject_specialist(
    specialist_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Reject a specialist (admin only) - this will delete their account"""
    try:
        # Verify admin permissions
        admin_user = verify_admin_permissions(current_user_data)
        
        # Find the specialist
        specialist = db.query(Specialists).filter(
            Specialists.id == specialist_id,
            Specialists.is_deleted == False
        ).first()
        
        if not specialist:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specialist not found"
            )
        
        # Get specialist auth info
        auth_info = db.query(SpecialistsAuthInfo).filter(
            SpecialistsAuthInfo.specialist_id == specialist.id
        ).first()
        
        # Get approval data
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        # Permanently delete the specialist and all related data
        if auth_info:
            db.delete(auth_info)
        
        if approval_data:
            db.delete(approval_data)
        
        # Delete the specialist (this will cascade to related data due to relationships)
        db.delete(specialist)
        db.commit()
        
        return {"message": "Specialist rejected and account deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error rejecting specialist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject specialist"
        )

# ============================================================================
# FORUM REPORT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/reports", response_model=List[ForumReportAdminResponse])
async def get_all_reports(
    status: str | None = None,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get all forum reports (admin only)"""
    try:
        # Verify admin permissions
        admin_user = verify_admin_permissions(current_user_data)
        
        # Build query
        query = db.query(ForumReport)
        
        # Filter by status if provided
        if status:
            query = query.filter(ForumReport.status == status)
        
        reports = query.order_by(ForumReport.created_at.desc()).all()
        
        response_data = []
        for report in reports:
            # Get post content and author
            post_content = ""
            post_author_name = "Unknown"
            
            if report.post_type == "question":
                question = db.query(ForumQuestion).filter(ForumQuestion.id == report.post_id).first()
                if question:
                    post_content = question.title + ": " + question.content[:200] + "..."
                    patient = db.query(Patient).filter(Patient.id == question.patient_id).first()
                    if patient:
                        post_author_name = f"{patient.first_name} {patient.last_name}"
            else:  # answer
                answer = db.query(ForumAnswer).filter(ForumAnswer.id == report.post_id).first()
                if answer:
                    post_content = answer.content[:200] + "..."
                    specialist = db.query(Specialists).filter(Specialists.id == answer.specialist_id).first()
                    if specialist:
                        post_author_name = f"{specialist.first_name} {specialist.last_name}"
            
            response_data.append(ForumReportAdminResponse(
                id=str(report.id),
                post_id=str(report.post_id),
                post_type=report.post_type,
                reason=report.reason,
                status=report.status,
                reporter_name=report.reporter_name,
                reporter_type=report.reporter_type,
                created_at=report.created_at,
                post_content=post_content,
                post_author_name=post_author_name,
                moderated_by=str(report.moderated_by) if report.moderated_by else None,
                moderated_at=report.moderated_at,
                moderation_notes=report.moderation_notes
            ))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching reports: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reports"
        )

@router.post("/reports/{report_id}/action")
async def take_report_action(
    report_id: str,
    action_data: ReportActionRequest,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Take action on a report (admin only)"""
    try:
        # Verify admin permissions
        admin_user = verify_admin_permissions(current_user_data)
        
        # Find the report
        report = db.query(ForumReport).filter(ForumReport.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        if report.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report has already been processed"
            )
        
        if action_data.action == "keep":
            # Mark report as resolved
            report.mark_resolved(str(admin_user.id), action_data.notes)
            
        elif action_data.action == "remove":
            # Mark report as removed and delete the post
            report.mark_removed(str(admin_user.id), action_data.notes)
            
            if report.post_type == "question":
                question = db.query(ForumQuestion).filter(ForumQuestion.id == report.post_id).first()
                if question:
                    question.is_deleted = True
            else:  # answer
                answer = db.query(ForumAnswer).filter(ForumAnswer.id == report.post_id).first()
                if answer:
                    answer.is_deleted = True
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be 'keep' or 'remove'"
            )
        
        db.commit()
        
        return {"message": f"Report {action_data.action}d successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error taking report action: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to take action on report"
        )

"""
Admin Router - API endpoints for admin operations
================================================
Handles admin-specific operations like user management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal
import os
import mimetypes
from jose import JWTError, jwt

from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from models.sql_models.patient_models import Patient, PatientAuthInfo
from utils.email_utils import send_specialist_approval_email, safe_enum_to_string
from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, SpecialistsApprovalData, 
    SpecialistSpecializations, SpecialistDocuments, SpecialistAvailability,
    TimeSlotEnum, ApprovalStatusEnum
)
from models.sql_models.admin_models import Admin, AdminRoleEnum
from models.sql_models.forum_models import ForumReport, ForumQuestion, ForumAnswer

router = APIRouter(prefix="/admin", tags=["Admin"])

async def get_current_user_from_token_or_query(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """Extract current user from JWT token (header or query parameter)"""
    from fastapi.security import HTTPAuthorizationCredentials
    from fastapi.security import HTTPBearer
    
    security = HTTPBearer()
    
    try:
        # First try to get token from Authorization header
        try:
            credentials: HTTPAuthorizationCredentials = await security(request)
            if credentials and credentials.credentials:
                token = credentials.credentials
            else:
                raise HTTPException(status_code=401, detail="No token in header")
        except:
            # If header fails, try query parameter
            token = request.query_params.get("token")
            if not token:
                raise HTTPException(status_code=401, detail="No authentication token provided")
        
        # Decode and validate token
        try:
            SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
            ALGORITHM = "HS256"
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        user_type: str = payload.get("user_type")
        
        if user_id is None or email is None or user_type is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Verify admin permissions
        if user_type != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Find admin user
        admin = db.query(Admin).filter(
            Admin.id == user_id,
            Admin.email == email,
            Admin.is_deleted == False
        ).first()
        
        if not admin:
            raise HTTPException(status_code=401, detail="Admin user not found")
        
        return {
            "user_id": user_id,
            "email": email,
            "user_type": user_type,
            "admin": admin
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")

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
    address: str | None
    city: str | None
    clinic_name: str | None
    bio: str | None
    consultation_fee: Decimal | None
    languages_spoken: List[str] | None
    website_url: str | None
    social_media_links: Dict[str, str] | None
    specialist_type: str | None
    years_experience: int | None
    approval_status: str
    created_at: datetime
    last_login: datetime | None
    specializations: List[Dict[str, Any]] | None = None
    documents: List[Dict[str, Any]] | None = None
    availability_slots: List[str] | None = None
    profile_completion_percentage: float | None = None
    submission_date: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None
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

def calculate_profile_completion_for_admin(specialist, specializations, availability_slots, documents):
    """Calculate profile completion percentage for admin view"""
    try:
        required_fields = {
            'phone': specialist.phone,
            'address': specialist.address,
            'bio': specialist.bio,
            'consultation_fee': specialist.consultation_fee,
            'languages_spoken': specialist.languages_spoken,
            'specializations': len(specializations) > 0,
            'availability_slots': len(availability_slots) > 0
        }
        
        # Count completed required fields
        completed_required = sum(1 for value in required_fields.values() if value)
        total_required = len(required_fields)
        
        # Check documents (4 mandatory documents required)
        mandatory_doc_types = ['identity_card', 'degree', 'license', 'experience_letter']
        uploaded_doc_types = [doc.get('document_type') for doc in documents]
        completed_documents = sum(1 for doc_type in mandatory_doc_types if doc_type in uploaded_doc_types)
        
        # Calculate weighted completion percentage
        # Profile fields: 70%, Documents: 30%
        profile_percentage = (completed_required / total_required) * 70
        document_percentage = (completed_documents / 4) * 30
        
        total_percentage = profile_percentage + document_percentage
        return round(total_percentage, 1)
        
    except Exception as e:
        print(f"Error calculating profile completion: {str(e)}")
        return 0.0

# ============================================================================
# DOCUMENT SERVING ENDPOINTS
# ============================================================================

@router.get("/documents/{document_id}/view")
async def view_document(
    document_id: str,
    current_user_data: dict = Depends(get_current_user_from_token_or_query),
    db: Session = Depends(get_db)
):
    """View a specialist document (admin only)"""
    try:
        # Verify admin permissions (current_user_data already contains admin info)
        admin_user = current_user_data["admin"]
        
        # Find the document
        document = db.query(SpecialistDocuments).filter(
            SpecialistDocuments.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found on server"
            )
        
        # Get MIME type
        content_type, _ = mimetypes.guess_type(document.file_path)
        if not content_type:
            content_type = document.mime_type or "application/octet-stream"
        
        # Return file for viewing (inline)
        return FileResponse(
            path=document.file_path,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={document.document_name}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error viewing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to view document"
        )

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    current_user_data: dict = Depends(get_current_user_from_token_or_query),
    db: Session = Depends(get_db)
):
    """Download a specialist document (admin only)"""
    try:
        # Verify admin permissions (current_user_data already contains admin info)
        admin_user = current_user_data["admin"]
        
        # Find the document
        document = db.query(SpecialistDocuments).filter(
            SpecialistDocuments.id == document_id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if file exists
        if not os.path.exists(document.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document file not found on server"
            )
        
        # Get MIME type
        content_type, _ = mimetypes.guess_type(document.file_path)
        if not content_type:
            content_type = document.mime_type or "application/octet-stream"
        
        # Return file for download (attachment)
        return FileResponse(
            path=document.file_path,
            media_type=content_type,
            filename=document.document_name,
            headers={
                "Content-Disposition": f"attachment; filename={document.document_name}",
                "Cache-Control": "no-cache"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download document"
        )

@router.get("/specialists/{specialist_id}/details")
async def get_specialist_details(
    specialist_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get detailed specialist information (admin only)"""
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
        
        # Get auth info
        auth_info = db.query(SpecialistsAuthInfo).filter(
            SpecialistsAuthInfo.specialist_id == specialist.id
        ).first()
        
        # Get specializations
        specializations = db.query(SpecialistSpecializations).filter(
            SpecialistSpecializations.specialist_id == specialist.id
        ).all()
        
        # Get approval data and documents
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        documents = []
        if approval_data:
            docs = db.query(SpecialistDocuments).filter(
                SpecialistDocuments.approval_data_id == approval_data.id
            ).all()
            documents = [
                {
                    "id": str(doc.id),
                    "document_name": doc.document_name,
                    "document_type": doc.document_type.value if doc.document_type else None,
                    "verification_status": doc.verification_status.value if doc.verification_status else None,
                    "upload_date": doc.upload_date,
                    "expiry_date": doc.expiry_date,
                    "file_size": doc.file_size,
                    "mime_type": doc.mime_type,
                    "verification_notes": doc.verification_notes,
                    "verified_by": str(doc.verified_by) if doc.verified_by else None,
                    "verified_at": doc.verified_at
                }
                for doc in docs
            ]
        
        # Get availability slots
        availability_slots = db.query(SpecialistAvailability).filter(
            SpecialistAvailability.specialist_id == specialist.id
        ).all()
        availability_list = [
            {
                "time_slot": slot.time_slot.value,
                "display": slot.slot_display,
                "created_at": slot.created_at
            }
            for slot in availability_slots
        ]
        
        # Calculate profile completion
        profile_completion = calculate_profile_completion_for_admin(specialist, specializations, availability_slots, documents)
        
        # Enhanced response with all details
        return {
            "id": str(specialist.id),
            "email": specialist.email,
            "full_name": f"{specialist.first_name} {specialist.last_name}",
            "first_name": specialist.first_name,
            "last_name": specialist.last_name,
            "phone": specialist.phone,
            "address": specialist.address,
            "city": specialist.city,
            "clinic_name": specialist.clinic_name,
            "bio": specialist.bio,
            "consultation_fee": float(specialist.consultation_fee) if specialist.consultation_fee else None,
            "languages_spoken": specialist.languages_spoken,
            "website_url": specialist.website_url,
            "social_media_links": specialist.social_media_links,
            "specialist_type": specialist.specialist_type.value if specialist.specialist_type else None,
            "years_experience": specialist.years_experience,
            "approval_status": specialist.approval_status.value if specialist.approval_status else "pending",
            "created_at": specialist.created_at,
            "updated_at": specialist.updated_at,
            "last_login": auth_info.last_login_at if auth_info else None,
            "email_verification_status": auth_info.email_verification_status.value if auth_info and auth_info.email_verification_status else None,
            "specializations": [
                {
                    "specialization": spec.specialization.value if spec.specialization else None,
                    "years_of_experience_in_specialization": spec.years_of_experience_in_specialization,
                    "is_primary_specialization": spec.is_primary_specialization,
                    "certification_date": spec.certification_date,
                    "created_at": spec.created_at
                }
                for spec in specializations
            ],
            "documents": documents,
            "availability_slots": availability_list,
            "profile_completion_percentage": profile_completion,
            "approval_data": {
                "license_number": approval_data.license_number if approval_data else None,
                "submission_date": approval_data.updated_at if approval_data else None,
                "created_at": approval_data.created_at if approval_data else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching specialist details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve specialist details"
        )

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
            
            # Get specializations
            specializations = db.query(SpecialistSpecializations).filter(
                SpecialistSpecializations.specialist_id == specialist.id
            ).all()
            
            # Get documents
            approval_data = db.query(SpecialistsApprovalData).filter(
                SpecialistsApprovalData.specialist_id == specialist.id
            ).first()
            
            documents = []
            if approval_data:
                docs = db.query(SpecialistDocuments).filter(
                    SpecialistDocuments.approval_data_id == approval_data.id
                ).all()
                documents = [
                    {
                        "id": str(doc.id),
                        "document_name": doc.document_name,
                        "document_type": doc.document_type.value if doc.document_type else None,
                        "verification_status": doc.verification_status.value if doc.verification_status else None,
                        "upload_date": doc.upload_date,
                        "expiry_date": doc.expiry_date,
                        "file_size": doc.file_size,
                        "mime_type": doc.mime_type
                    }
                    for doc in docs
                ]
            
            # Get availability slots
            availability_slots = db.query(SpecialistAvailability).filter(
                SpecialistAvailability.specialist_id == specialist.id
            ).all()
            availability_list = [slot.time_slot.value for slot in availability_slots] if availability_slots else []
            
            # Calculate profile completion percentage
            profile_completion = calculate_profile_completion_for_admin(specialist, specializations, availability_slots, documents)
            
            # Get submission date (when they submitted for approval)
            submission_date = None
            if specialist.approval_status == ApprovalStatusEnum.UNDER_REVIEW and approval_data:
                submission_date = approval_data.updated_at
            
            result.append(SpecialistResponse(
                id=str(specialist.id),
                email=specialist.email,
                full_name=f"{specialist.first_name} {specialist.last_name}",
                phone=specialist.phone,
                address=specialist.address,
                city=specialist.city,
                clinic_name=specialist.clinic_name,
                bio=specialist.bio,
                consultation_fee=specialist.consultation_fee,
                languages_spoken=specialist.languages_spoken,
                website_url=specialist.website_url,
                social_media_links=specialist.social_media_links,
                specialist_type=specialist.specialist_type.value if specialist.specialist_type else None,
                years_experience=specialist.years_experience,
                approval_status=specialist.approval_status.value if specialist.approval_status else "pending",
                created_at=specialist.created_at,
                last_login=auth_info.last_login_at if auth_info else None,
                specializations=[
                    {
                        "specialization": spec.specialization.value if spec.specialization else None,
                        "years_of_experience_in_specialization": spec.years_of_experience_in_specialization,
                        "is_primary_specialization": spec.is_primary_specialization,
                        "certification_date": spec.certification_date
                    }
                    for spec in specializations
                ] if specializations else None,
                documents=documents,
                availability_slots=availability_list,
                profile_completion_percentage=profile_completion,
                submission_date=submission_date
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
        
        # Enhanced validation for profile completion
        if not specialist.phone or not specialist.address or not specialist.bio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specialist must complete their profile before approval"
            )
        
        # Check if availability slots are set
        availability_slots = db.query(SpecialistAvailability).filter(
            SpecialistAvailability.specialist_id == specialist.id
        ).all()
        
        if not availability_slots:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specialist must set availability slots before approval"
            )
        
        # Check if documents are submitted
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        if not approval_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specialist must submit required documents before approval"
            )
        
        # Check if all mandatory documents are uploaded
        documents = db.query(SpecialistDocuments).filter(
            SpecialistDocuments.approval_data_id == approval_data.id
        ).all()
        
        mandatory_doc_types = ['identity_card', 'degree', 'license', 'experience_letter']
        uploaded_doc_types = [doc.document_type.value for doc in documents]
        missing_docs = [doc_type for doc_type in mandatory_doc_types if doc_type not in uploaded_doc_types]
        
        if missing_docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing mandatory documents: {', '.join(missing_docs)}"
            )
        
        # Update approval status
        specialist.approval_status = ApprovalStatusEnum.APPROVED
        specialist.availability_status = "accepting_new_patients"
        
        # Get primary specialization for email
        primary_spec = db.query(SpecialistSpecializations).filter(
            SpecialistSpecializations.specialist_id == specialist.id,
            SpecialistSpecializations.is_primary_specialization == True
        ).first()
        
        specialization_name = safe_enum_to_string(primary_spec.specialization) if primary_spec else "Mental Health"
        
        # Send approval email to specialist
        try:
            send_specialist_approval_email(
                email=specialist.email,
                first_name=specialist.first_name,
                last_name=specialist.last_name,
                specialization=specialization_name,
                status="approved"
            )
        except Exception as e:
            print(f"Failed to send approval email: {str(e)}")
            # Don't fail the approval if email fails
        
        db.commit()
        
        return {
            "message": "Specialist approved successfully",
            "specialist_id": str(specialist.id),
            "approval_status": "approved",
            "email_sent": True
        }
        
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
    """Reject a specialist (admin only)"""
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
        
        # Update approval status to rejected
        specialist.approval_status = ApprovalStatusEnum.REJECTED
        specialist.availability_status = "not_accepting_new_patients"
        
        # Get primary specialization for email
        primary_spec = db.query(SpecialistSpecializations).filter(
            SpecialistSpecializations.specialist_id == specialist.id,
            SpecialistSpecializations.is_primary_specialization == True
        ).first()
        
        specialization_name = safe_enum_to_string(primary_spec.specialization) if primary_spec else "Mental Health"
        
        # Send rejection email to specialist
        try:
            send_specialist_approval_email(
                email=specialist.email,
                first_name=specialist.first_name,
                last_name=specialist.last_name,
                specialization=specialization_name,
                status="rejected",
                admin_notes="Your application has been reviewed. Please contact support for more information."
            )
        except Exception as e:
            print(f"Failed to send rejection email: {str(e)}")
            # Don't fail the rejection if email fails
        
        db.commit()
        
        return {
            "message": "Specialist rejected successfully",
            "specialist_id": str(specialist.id),
            "approval_status": "rejected",
            "email_sent": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error rejecting specialist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject specialist"
        )

@router.post("/specialists/{specialist_id}/suspend")
async def suspend_specialist(
    specialist_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Suspend a specialist (admin only)"""
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
        
        # Update approval status to suspended
        specialist.approval_status = ApprovalStatusEnum.SUSPENDED
        specialist.availability_status = "not_accepting_new_patients"
        
        db.commit()
        
        return {"message": "Specialist suspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error suspending specialist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend specialist"
        )

@router.post("/specialists/{specialist_id}/unsuspend")
async def unsuspend_specialist(
    specialist_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Unsuspend a specialist (admin only)"""
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
        
        # Check if specialist was previously approved
        if specialist.approval_status == ApprovalStatusEnum.SUSPENDED:
            # Restore to approved status
            specialist.approval_status = ApprovalStatusEnum.APPROVED
            specialist.availability_status = "accepting_new_patients"
        else:
            # If not previously approved, set to pending
            specialist.approval_status = ApprovalStatusEnum.PENDING
            specialist.availability_status = "not_accepting_new_patients"
        
        db.commit()
        
        return {"message": "Specialist unsuspended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error unsuspending specialist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsuspend specialist"
        )

@router.delete("/specialists/{specialist_id}")
async def delete_specialist(
    specialist_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a specialist (admin only)"""
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
        
        return {"message": "Specialist deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting specialist: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete specialist"
        )

@router.get("/specialists/{specialist_id}/details")
async def get_specialist_details(
    specialist_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get detailed specialist information including documents (admin only)"""
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
        
        # Get approval data and documents
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        documents = []
        if approval_data:
            from models.sql_models.specialist_models import SpecialistDocuments
            documents = db.query(SpecialistDocuments).filter(
                SpecialistDocuments.approval_data_id == approval_data.id
            ).all()
        
        # Get specializations
        from models.sql_models.specialist_models import SpecialistSpecializations
        specializations = db.query(SpecialistSpecializations).filter(
            SpecialistSpecializations.specialist_id == specialist.id
        ).all()
        
        return {
            "id": str(specialist.id),
            "email": specialist.email,
            "full_name": f"{specialist.first_name} {specialist.last_name}",
            "phone": specialist.phone,
            "city": specialist.city,
            "specialist_type": specialist.specialist_type.value if specialist.specialist_type else None,
            "years_experience": specialist.years_experience,
            "approval_status": specialist.approval_status.value if specialist.approval_status else "pending",
            "availability_status": specialist.availability_status.value if specialist.availability_status else "not_accepting",
            "bio": specialist.bio,
            "consultation_fee": specialist.consultation_fee,
            "languages_spoken": specialist.languages_spoken,
            "website_url": specialist.website_url,
            "clinic_name": specialist.clinic_name,
            "created_at": specialist.created_at,
            "updated_at": specialist.updated_at,
            "specializations": [
                {
                    "specialization": spec.specialization.value,
                    "years_of_experience": spec.years_of_experience_in_specialization,
                    "is_primary": spec.is_primary_specialization,
                    "certification_date": spec.certification_date
                } for spec in specializations
            ],
            "documents": [
                {
                    "id": str(doc.id),
                    "document_type": doc.document_type.value,
                    "document_name": doc.document_name,
                    "verification_status": doc.verification_status.value,
                    "upload_date": doc.upload_date,
                    "expiry_date": doc.expiry_date
                } for doc in documents
            ],
            "approval_data": {
                "submission_date": approval_data.submission_date if approval_data else None,
                "background_check_status": approval_data.background_check_status if approval_data else None
            } if approval_data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching specialist details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve specialist details"
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

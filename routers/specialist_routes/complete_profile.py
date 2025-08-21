"""
Specialist Profile Completion and Document Submission API
========================================================
Provides endpoints for specialists to complete their profile and submit required documents
Includes proper validation, error handling, and admin notifications
"""

import os
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr, Field, validator
from decimal import Decimal
import uuid

# Import database models
from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, SpecialistsApprovalData,
    SpecialistDocuments, SpecialistSpecializations,
    SpecializationEnum, DocumentTypeEnum, DocumentStatusEnum,
    ApprovalStatusEnum, EmailVerificationStatusEnum
)
from models.sql_models.base_model import USERTYPE

# Import authentication dependencies
from ..authentication.authenticate import get_current_user_from_token

# Import utilities
from utils.email_utils import send_notification_email, safe_enum_to_string
from database.database import get_db

router = APIRouter(prefix="/specialist", tags=["Specialist Profile"])

# File upload configuration
UPLOAD_DIR = os.getenv("DOCUMENT_UPLOAD_DIR", "uploads/specialist_documents")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf", "image/jpeg", "image/png", 
    "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SpecializationItem(BaseModel):
    """Individual specialization entry"""
    specialization: SpecializationEnum
    years_of_experience_in_specialization: int = Field(ge=0, le=50)
    is_primary_specialization: bool = False
    certification_date: Optional[datetime] = None

class ProfileCompletionRequest(BaseModel):
    """Request model for profile completion"""
    # Contact & Location Details
    phone: str = Field(..., pattern=r'^\+?92[0-9]{10}$', description="Pakistani phone format: +92XXXXXXXXXX")
    address: str = Field(..., min_length=10, max_length=500, description="Complete address")
    clinic_name: Optional[str] = Field(None, max_length=200, description="Clinic or practice name")
    
    # Professional Details
    bio: str = Field(..., min_length=50, max_length=2000, description="Professional biography")
    consultation_fee: Decimal = Field(..., ge=0, le=50000, description="Fee in PKR")
    languages_spoken: List[str] = Field(..., min_items=1, description="Languages spoken (language codes)")
    
    # Specializations
    specializations: List[SpecializationItem] = Field(..., min_items=1, max_items=5)
    
    # Optional Professional Info
    website_url: Optional[str] = Field(None, pattern=r'^https?://.*', description="Professional website")
    social_media_links: Optional[Dict[str, str]] = Field(None, description="Social media profiles")
    
    @validator('specializations')
    def validate_specializations(cls, v):
        if not v:
            raise ValueError("At least one specialization is required")
        
        # Check for exactly one primary specialization
        primary_count = sum(1 for spec in v if spec.is_primary_specialization)
        if primary_count != 1:
            raise ValueError("Exactly one specialization must be marked as primary")
        
        # Check for duplicate specializations
        specializations_set = set(spec.specialization for spec in v)
        if len(specializations_set) != len(v):
            raise ValueError("Duplicate specializations are not allowed")
        
        return v
    
    @validator('languages_spoken')
    def validate_languages(cls, v):
        valid_languages = {'en', 'ur', 'hi', 'ar', 'ps', 'sd', 'bal'}  # Common languages in Pakistan
        for lang in v:
            if lang not in valid_languages:
                raise ValueError(f"Unsupported language code: {lang}")
        return v

class DocumentSubmissionRequest(BaseModel):
    """Request model for document metadata"""
    document_type: DocumentTypeEnum
    document_name: str = Field(..., min_length=3, max_length=255)
    expiry_date: Optional[datetime] = None

class ProfileCompletionResponse(BaseModel):
    """Response for profile completion"""
    message: str
    profile_completion_percentage: int
    missing_fields: List[str]
    next_steps: List[str]

class DocumentSubmissionResponse(BaseModel):
    """Response for document submission"""
    message: str
    document_id: str
    document_name: str
    verification_status: str
    admin_notified: bool
    next_steps: List[str]

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ensure_upload_directory():
    """Ensure upload directory exists"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def validate_file_upload(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check file size
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Check file extension
    if not any(file.filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Content-Type: {file.content_type}"
        )

def save_uploaded_file(file: UploadFile, specialist_id: str, document_type: str) -> str:
    """Save uploaded file and return file path"""
    ensure_upload_directory()
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1].lower()
    unique_filename = f"{specialist_id}_{document_type}_{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    return file_path

def calculate_profile_completion(specialist: Specialists) -> tuple:
    """Calculate profile completion percentage and missing fields"""
    required_fields = {
        'phone': specialist.phone,
        'address': specialist.address,
        'bio': specialist.bio,
        'consultation_fee': specialist.consultation_fee,
        'languages_spoken': specialist.languages_spoken,
    }
    
    optional_fields = {
        'clinic_name': specialist.clinic_name,
        'website_url': specialist.website_url,
        'social_media_links': specialist.social_media_links,
    }
    
    # Check specializations
    has_specializations = len(specialist.specializations) > 0
    
    completed_required = sum(1 for value in required_fields.values() if value)
    total_required = len(required_fields) + (1 if has_specializations else 0)
    
    completed_optional = sum(1 for value in optional_fields.values() if value)
    total_optional = len(optional_fields)
    
    # Weight: 80% for required, 20% for optional
    completion_percentage = int(
        (completed_required / total_required * 0.8 + 
         completed_optional / total_optional * 0.2) * 100
    )
    
    missing_fields = [
        field for field, value in required_fields.items() 
        if not value
    ]
    if not has_specializations:
        missing_fields.append('specializations')
    
    return completion_percentage, missing_fields

def get_admin_emails_for_notifications(db: Session) -> List[str]:
    """Get admin emails for notifications"""
    try:
        from models.sql_models.admin_models import Admin, AdminStatusEnum
        return [
            admin.email for admin in db.query(Admin).filter(
                Admin.is_active == True,
                Admin.status == AdminStatusEnum.ACTIVE,
                Admin.is_deleted == False
            ).all()
        ]
    except Exception as e:
        print(f"Error fetching admin emails: {str(e)}")
        return []

def notify_admins_document_submission(
    db: Session, 
    specialist: Specialists, 
    document_type: str, 
    document_name: str
) -> bool:
    """Send document submission notification to admins"""
    try:
        admin_emails = get_admin_emails_for_notifications(db)
        
        if not admin_emails:
            print("No admin emails found for document submission notification")
            return False
        
        success_count = 0
        
        for admin_email in admin_emails:
            try:
                subject = f"New Document Submission - {specialist.full_name}"
                content = f"""
                <h2>New Document Submitted for Approval</h2>
                
                <p><strong>Specialist Information:</strong></p>
                <ul>
                    <li><strong>Name:</strong> {specialist.full_name}</li>
                    <li><strong>Email:</strong> {specialist.email}</li>
                    <li><strong>Type:</strong> {safe_enum_to_string(specialist.specialist_type)}</li>
                    <li><strong>City:</strong> {specialist.city}</li>
                </ul>
                
                <p><strong>Document Details:</strong></p>
                <ul>
                    <li><strong>Document Type:</strong> {document_type.replace('_', ' ').title()}</li>
                    <li><strong>Document Name:</strong> {document_name}</li>
                    <li><strong>Submission Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                </ul>
                
                <p>Please log into the admin panel to review and approve the submitted document.</p>
                
                <p>Best regards,<br>MindMate System</p>
                """
                
                if send_notification_email(admin_email, subject, content):
                    success_count += 1
                    
            except Exception as e:
                print(f"Failed to notify admin {admin_email}: {str(e)}")
                continue
        
        return success_count > 0
        
    except Exception as e:
        print(f"Admin notification failed: {str(e)}")
        return False

# ============================================================================
# AUTHENTICATION HELPER
# ============================================================================

async def get_authenticated_specialist(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
) -> Specialists:
    """Get authenticated specialist with proper validation"""
    user = current_user_data["user"]
    user_type = current_user_data["user_type"]
    
    if user_type != "specialist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only accessible to specialists"
        )
    
    # Verify specialist still exists and is verified
    specialist = db.query(Specialists).filter(
        Specialists.id == user.id,
        Specialists.is_deleted == False
    ).first()
    
    if not specialist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialist account not found"
        )
    
    # Check authentication info
    auth_info = db.query(SpecialistsAuthInfo).filter(
        SpecialistsAuthInfo.specialist_id == specialist.id,
        SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED
    ).first()
    
    if not auth_info:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required to access this endpoint"
        )
    
    return specialist

# ============================================================================
# PROFILE COMPLETION ENDPOINT
# ============================================================================

@router.post(
    "/complete-profile",
    response_model=ProfileCompletionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        403: {"model": ErrorResponse, "description": "Access denied or verification required"},
        404: {"model": ErrorResponse, "description": "Specialist not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def complete_profile(
    request: ProfileCompletionRequest,
    db: Session = Depends(get_db),
    specialist: Specialists = Depends(get_authenticated_specialist)
):
    """Complete specialist profile with professional information and specializations"""
    try:
        print(f"Profile completion request for specialist: {specialist.email}")
        
        # Update specialist basic information
        specialist.phone = request.phone
        specialist.address = request.address
        specialist.clinic_name = request.clinic_name
        specialist.bio = request.bio
        specialist.consultation_fee = request.consultation_fee
        specialist.languages_spoken = request.languages_spoken
        specialist.website_url = request.website_url
        specialist.social_media_links = request.social_media_links if request.social_media_links else {}
        
        # Clear existing specializations to replace with new ones
        existing_specializations = db.query(SpecialistSpecializations).filter(
            SpecialistSpecializations.specialist_id == specialist.id
        ).all()
        
        for spec in existing_specializations:
            db.delete(spec)
        
        db.flush()  # Ensure deletions are committed before insertions
        
        # Add new specializations
        for spec_data in request.specializations:
            specialization = SpecialistSpecializations(
                specialist_id=specialist.id,
                specialization=spec_data.specialization,
                years_of_experience_in_specialization=spec_data.years_of_experience_in_specialization,
                is_primary_specialization=spec_data.is_primary_specialization,
                certification_date=spec_data.certification_date
            )
            db.add(specialization)
        
        # Update timestamps
        specialist.updated_at = datetime.now(timezone.utc)
        
        # Commit all changes
        db.commit()
        
        print(f"Profile completed successfully for specialist: {specialist.email}")
        
        # Calculate completion percentage and missing fields
        completion_percentage, missing_fields = calculate_profile_completion(specialist)
        
        # Determine next steps based on profile completion and approval status
        next_steps = []
        if completion_percentage == 100:
            next_steps.append("✅ Profile is complete!")
        else:
            next_steps.append(f"📋 Profile is {completion_percentage}% complete")
            if missing_fields:
                next_steps.append(f"❌ Missing: {', '.join(missing_fields)}")
        
        if specialist.approval_status == ApprovalStatusEnum.PENDING:
            next_steps.extend([
                "📄 Submit required documents for verification",
                "⏳ Wait for admin approval",
                "📧 You'll receive email notification once approved"
            ])
        elif specialist.approval_status == ApprovalStatusEnum.UNDER_REVIEW:
            next_steps.extend([
                "🔍 Your application is under review",
                "📧 You'll receive email notification once approved"
            ])
        elif specialist.approval_status == ApprovalStatusEnum.APPROVED:
            next_steps.extend([
                "🎉 Your account is approved!",
                "📅 You can now start accepting appointments",
                "⚙️ Configure your availability and schedule"
            ])
        
        return ProfileCompletionResponse(
            message="Profile updated successfully",
            profile_completion_percentage=completion_percentage,
            missing_fields=missing_fields,
            next_steps=next_steps
        )
        
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        print(f"Database integrity error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database constraint violation. Please check your data and try again."
        )
    except Exception as e:
        db.rollback()
        print(f"Profile completion error for {specialist.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile. Please try again later."
        )

# ============================================================================
# DOCUMENT SUBMISSION ENDPOINT
# ============================================================================

@router.post(
    "/submit-documents",
    response_model=DocumentSubmissionResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error or file issue"},
        403: {"model": ErrorResponse, "description": "Access denied or verification required"},
        404: {"model": ErrorResponse, "description": "Specialist not found"},
        413: {"model": ErrorResponse, "description": "File too large"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def submit_documents(
    document_type: DocumentTypeEnum = Form(..., description="Type of document being submitted"),
    document_name: str = Form(..., min_length=3, max_length=255, description="Display name for the document"),
    expiry_date: Optional[str] = Form(None, description="Document expiry date (YYYY-MM-DD format)"),
    file: UploadFile = File(..., description="Document file (PDF, JPG, PNG, DOC, DOCX)"),
    db: Session = Depends(get_db),
    specialist: Specialists = Depends(get_authenticated_specialist)
):
    """Submit documents for specialist verification with admin notification"""
    try:
        print(f"Document submission for specialist: {specialist.email}, type: {document_type}")
        
        # Validate file
        validate_file_upload(file)
        
        # Parse expiry date if provided
        parsed_expiry_date = None
        if expiry_date:
            try:
                parsed_expiry_date = datetime.fromisoformat(expiry_date)
                if parsed_expiry_date <= datetime.now():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Document expiry date must be in the future"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid expiry date format. Use YYYY-MM-DD."
                )
        
        # Get or create approval data
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        if not approval_data:
            approval_data = SpecialistsApprovalData(
                specialist_id=specialist.id,
                submission_date=datetime.now(timezone.utc),
                background_check_status='pending'
            )
            db.add(approval_data)
            db.flush()
        
        # Check if document type already exists (replace if exists)
        existing_doc = db.query(SpecialistDocuments).filter(
            SpecialistDocuments.approval_data_id == approval_data.id,
            SpecialistDocuments.document_type == document_type
        ).first()
        
        if existing_doc:
            # Delete old file if exists
            if os.path.exists(existing_doc.file_path):
                try:
                    os.remove(existing_doc.file_path)
                except Exception as e:
                    print(f"Failed to delete old file {existing_doc.file_path}: {str(e)}")
            
            # Delete existing record
            db.delete(existing_doc)
            db.flush()
        
        # Save new file
        try:
            file_path = save_uploaded_file(file, str(specialist.id), document_type.value)
        except Exception as e:
            print(f"File save error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file. Please try again."
            )
        
        # Create document record
        document = SpecialistDocuments(
            approval_data_id=approval_data.id,
            document_type=document_type,
            document_name=document_name,
            file_path=file_path,
            file_size=file.size,
            mime_type=file.content_type,
            verification_status=DocumentStatusEnum.PENDING,
            upload_date=datetime.now(timezone.utc),
            expiry_date=parsed_expiry_date
        )
        db.add(document)
        
        # Update approval data submission date
        approval_data.submission_date = datetime.now(timezone.utc)
        
        # Commit transaction
        db.commit()
        
        print(f"Document saved successfully: {document.id}")
        
        # Send admin notification
        admin_notified = notify_admins_document_submission(
            db, specialist, document_type.value, document_name
        )
        
        if admin_notified:
            print(f"Admin notification sent for document submission: {specialist.email}")
        else:
            print(f"Warning: Failed to send admin notification for: {specialist.email}")
        
        # Prepare next steps based on approval status
        next_steps = [
            "✅ Document uploaded successfully",
            "📧 Admin team has been notified",
            "⏳ Your document is pending review"
        ]
        
        if specialist.approval_status == ApprovalStatusEnum.PENDING:
            next_steps.extend([
                "📋 Submit any remaining required documents",
                "🔍 Wait for admin approval (typically 2-3 business days)",
                "📧 You'll receive email notification once approved"
            ])
        elif specialist.approval_status == ApprovalStatusEnum.UNDER_REVIEW:
            next_steps.extend([
                "🔍 Your application is currently under review",
                "📧 You'll receive email notification once review is complete"
            ])
        
        return DocumentSubmissionResponse(
            message=f"{document_type.value.replace('_', ' ').title()} submitted successfully",
            document_id=str(document.id),
            document_name=document_name,
            verification_status=DocumentStatusEnum.PENDING.value,
            admin_notified=admin_notified,
            next_steps=next_steps
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Document submission error for {specialist.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit document. Please try again later."
        )

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "router",
    "complete_profile",
    "submit_documents",
    "ProfileCompletionRequest",
    "DocumentSubmissionRequest",
    "ProfileCompletionResponse",
    "DocumentSubmissionResponse"
]
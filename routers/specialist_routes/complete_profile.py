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
    SpecialistDocuments, SpecialistSpecializations, SpecialistAvailability,
    SpecializationEnum, DocumentTypeEnum, DocumentStatusEnum,
    ApprovalStatusEnum, EmailVerificationStatusEnum, TimeSlotEnum
)
from models.sql_models.base_model import USERTYPE

# Import authentication dependencies
from ..authentication.authenticate import get_current_user_from_token

# Import utilities
from utils.email_utils import send_notification_email, safe_enum_to_string, send_admin_specialist_registration_notification
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

# Mandatory documents configuration (using existing SQL model enum values)
MANDATORY_DOCUMENTS = [
    {
        "type": DocumentTypeEnum.IDENTITY_CARD,
        "label": "Identity Card (CNIC)",
        "description": "Clear photo of your CNIC (both sides)",
        "required": True
    },
    {
        "type": DocumentTypeEnum.DEGREE,
        "label": "Degree Certificate",
        "description": "Your highest degree certificate in mental health field",
        "required": True
    },
    {
        "type": DocumentTypeEnum.LICENSE,
        "label": "Professional License",
        "description": "Valid professional license or registration certificate",
        "required": True
    },
    {
        "type": DocumentTypeEnum.EXPERIENCE_LETTER,
        "label": "Experience Letter", 
        "description": "Work experience certificate or letter from previous employer",
        "required": True
    }
]

MANDATORY_DOCUMENT_TYPES = [doc["type"] for doc in MANDATORY_DOCUMENTS]

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
    bio: str = Field(..., min_length=1, max_length=2000, description="Professional biography (minimum 20 words)")
    consultation_fee: Decimal = Field(..., ge=0, le=50000, description="Fee in PKR")
    languages_spoken: List[str] = Field(..., min_items=1, description="Languages spoken (language codes)")
    
    # Specializations
    specializations: List[SpecializationItem] = Field(..., min_items=1, max_items=5)
    
    # Availability Slots  
    availability_slots: List[TimeSlotEnum] = Field(..., min_items=1, max_items=8, description="Available time slots (1-8 hours per day)")
    
    # Optional Professional Info
    website_url: Optional[str] = Field(None, description="Professional website (https://, http://, or www. format accepted)")
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
    
    @validator('availability_slots')
    def validate_availability_slots(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one availability slot must be selected')
        
        if len(v) > 8:
            raise ValueError('Maximum 8 availability slots allowed (8 hours per day)')
        
        # Check for duplicates
        unique_slots = set(v)
        if len(unique_slots) != len(v):
            raise ValueError('Duplicate time slots are not allowed')
        
        return v
    
    @validator('website_url')
    def validate_website_url(cls, v):
        if v and v.strip():
            v = v.strip()
            # Auto-add https:// if URL doesn't start with http:// or https://
            if not v.startswith(('http://', 'https://')):
                if v.startswith('www.'):
                    v = 'https://' + v
                else:
                    v = 'https://' + v
            
            # Basic URL format validation
            import re
            url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}([/\w.-]*)*/?$'
            if not re.match(url_pattern, v):
                raise ValueError('Please enter a valid website URL (e.g., www.example.com or https://example.com)')
            return v
        return v
    
    @validator('bio')
    def validate_bio_word_count(cls, v):
        if not v or not v.strip():
            raise ValueError('Bio is required')
        
        v = v.strip()
        # Count words (split by whitespace and filter out empty strings)
        words = [word for word in v.split() if word.strip()]
        word_count = len(words)
        
        if word_count < 20:
            raise ValueError(f'Bio must contain at least 20 words. Currently has {word_count} words.')
        
        if len(v) > 2000:
            raise ValueError('Bio cannot exceed 2000 characters')
            
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

# Profile completion calculation removed - now handled in frontend
# Profile completion calculation removed
    
# All profile completion calculation logic removed

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
        print(f"DEBUG: Profile completion request for specialist: {specialist.email}")
        print(f"DEBUG: Specialist ID: {specialist.id}")
        print(f"DEBUG: Request data: {request.dict()}")
        print(f"DEBUG: Request data type: {type(request)}")
        print(f"DEBUG: Current approval status: {specialist.approval_status}")
        
        # Log each field individually for debugging
        print(f"DEBUG: Phone: {request.phone}")
        print(f"DEBUG: Address: {request.address}")
        print(f"DEBUG: Clinic name: {request.clinic_name}")
        print(f"DEBUG: Bio: {request.bio}")
        print(f"DEBUG: Consultation fee: {request.consultation_fee}")
        print(f"DEBUG: Languages: {request.languages_spoken}")
        print(f"DEBUG: Website: {request.website_url}")
        print(f"DEBUG: Social media: {request.social_media_links}")
        print(f"DEBUG: Specializations count: {len(request.specializations)}")
        for i, spec in enumerate(request.specializations):
            print(f"DEBUG: Spec {i}: {spec.dict()}")
        
        # Comprehensive validation of all required fields
        print(f"DEBUG: Validating required fields")
        validation_errors = []
        
        # Phone validation
        if not request.phone or not request.phone.strip():
            validation_errors.append("Phone number is required and cannot be empty")
        
        # Address validation  
        if not request.address or not request.address.strip():
            validation_errors.append("Address is required and cannot be empty")
        elif len(request.address.strip()) < 10:
            validation_errors.append("Address must be at least 10 characters long")
        
        # Bio validation (word count will be checked by Pydantic validator)
        if not request.bio or not request.bio.strip():
            validation_errors.append("Bio is required and cannot be empty")
        
        # Consultation fee validation
        if not request.consultation_fee or request.consultation_fee <= 0:
            validation_errors.append("Consultation fee is required and must be greater than 0")
        
        # Languages validation
        if not request.languages_spoken or len(request.languages_spoken) == 0:
            validation_errors.append("At least one language must be selected")
        
        # Specializations validation
        if not request.specializations or len(request.specializations) == 0:
            validation_errors.append("At least one specialization is required")
        
        # Availability slots validation
        if not request.availability_slots or len(request.availability_slots) == 0:
            validation_errors.append("At least one availability slot must be selected")
        elif len(request.availability_slots) > 8:
            validation_errors.append("Maximum 8 availability slots allowed (8 hours per day)")
        
        # If any validation errors, return them all at once
        if validation_errors:
            error_message = "; ".join(validation_errors)
            raise HTTPException(status_code=400, detail=f"Validation failed: {error_message}")
        
        # Validate specialization structure
        print(f"DEBUG: Validating specialization structure")
        specialization_errors = []
        
        for i, spec in enumerate(request.specializations):
            if not spec.specialization:
                specialization_errors.append(f"Specialization {i+1}: specialization type is required")
            if spec.years_of_experience_in_specialization is None or spec.years_of_experience_in_specialization < 0:
                specialization_errors.append(f"Specialization {i+1}: years of experience must be 0 or greater")
            if not isinstance(spec.is_primary_specialization, bool):
                specialization_errors.append(f"Specialization {i+1}: is_primary_specialization must be a boolean")
        
        # Check for exactly one primary specialization
        primary_count = sum(1 for spec in request.specializations if spec.is_primary_specialization)
        if primary_count != 1:
            specialization_errors.append("Exactly one specialization must be marked as primary")
        
        # If any specialization errors, return them all
        if specialization_errors:
            error_message = "; ".join(specialization_errors)
            raise HTTPException(status_code=400, detail=f"Specialization validation failed: {error_message}")
        
        print(f"DEBUG: All required fields validated successfully")
        
        # Update specialist basic information
        print(f"DEBUG: Updating specialist basic information")
        specialist.phone = request.phone
        specialist.address = request.address
        specialist.clinic_name = request.clinic_name
        specialist.bio = request.bio
        specialist.consultation_fee = request.consultation_fee
        specialist.languages_spoken = request.languages_spoken
        specialist.website_url = request.website_url
        specialist.social_media_links = request.social_media_links if request.social_media_links else {}
        print(f"DEBUG: Basic information updated successfully")
        
        # Clear existing specializations to replace with new ones
        print(f"DEBUG: Clearing existing specializations")
        existing_specializations = db.query(SpecialistSpecializations).filter(
            SpecialistSpecializations.specialist_id == specialist.id
        ).all()
        print(f"DEBUG: Found {len(existing_specializations)} existing specializations to delete")
        
        for spec in existing_specializations:
            db.delete(spec)
        
        db.flush()  # Ensure deletions are committed before insertions
        print(f"DEBUG: Existing specializations cleared")
        
        # Add new specializations
        print(f"DEBUG: Adding {len(request.specializations)} new specializations")
        for spec_data in request.specializations:
            specialization = SpecialistSpecializations(
                specialist_id=specialist.id,
                specialization=spec_data.specialization,
                years_of_experience_in_specialization=spec_data.years_of_experience_in_specialization,
                is_primary_specialization=spec_data.is_primary_specialization,
                certification_date=spec_data.certification_date
            )
            db.add(specialization)
            print(f"DEBUG: Added specialization: {spec_data.specialization} (primary: {spec_data.is_primary_specialization})")
        
        # Clear existing availability slots to replace with new ones
        print(f"DEBUG: Clearing existing availability slots")
        existing_slots = db.query(SpecialistAvailability).filter(
            SpecialistAvailability.specialist_id == specialist.id
        ).all()
        for slot in existing_slots:
            db.delete(slot)
        db.flush()  # Ensure deletions are committed before insertions
        print(f"DEBUG: Existing availability slots cleared")
        
        # Add new availability slots
        print(f"DEBUG: Adding {len(request.availability_slots)} new availability slots")
        for slot_enum in request.availability_slots:
            availability_slot = SpecialistAvailability(
                specialist_id=specialist.id,
                time_slot=slot_enum,
                is_active=True
            )
            db.add(availability_slot)
            print(f"DEBUG: Added availability slot: {slot_enum.value}")
        
        # Update timestamps
        specialist.updated_at = datetime.now(timezone.utc)
        
        # Commit all changes
        print(f"DEBUG: Committing all changes to database")
        db.commit()
        print(f"DEBUG: Database commit successful")
        
        print(f"DEBUG: Profile completed successfully for specialist: {specialist.email}")
        
        # Profile completion calculation removed - now handled in frontend
        print(f"DEBUG: Profile completion calculation bypassed - validation handled in frontend")
        
        # Notify admins about profile completion
        print(f"DEBUG: Notifying admins about profile completion")
        try:
            from ..registeration.register import safe_notify_admins
            admin_notified = safe_notify_admins(db, {
                'email': specialist.email,
                'first_name': specialist.first_name,
                'last_name': specialist.last_name,
                'specialization': specialist.specialist_type.value if specialist.specialist_type else "Specialist",
                'profile_completed': True,
                'completion_percentage': 100  # Always 100% since validation is in frontend
            })
            if admin_notified:
                print(f"DEBUG: Admin notification sent successfully")
            else:
                print(f"DEBUG: Admin notification failed")
        except Exception as e:
            print(f"DEBUG: Error notifying admins: {str(e)}")
            # Don't fail the profile completion for admin notification errors
        
        # Determine next steps based on approval status
        next_steps = []
        next_steps.append("✅ Profile updated successfully!")
        
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
            profile_completion_percentage=100,  # Always 100% since validation is in frontend
            missing_fields=[],  # No missing fields since validation is in frontend
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
# DOCUMENT MANAGEMENT ENDPOINTS
# ============================================================================

@router.get(
    "/mandatory-documents",
    responses={
        200: {"description": "List of mandatory documents"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_mandatory_documents(
    specialist: Specialists = Depends(get_authenticated_specialist)
):
    """Get list of mandatory documents required for specialist verification"""
    try:
        return {
            "mandatory_documents": MANDATORY_DOCUMENTS,
            "total_required": len(MANDATORY_DOCUMENTS),
            "message": "Please upload all mandatory documents for verification"
        }
    except Exception as e:
        print(f"Error fetching mandatory documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch mandatory documents list"
        )

@router.get(
    "/document-status",
    responses={
        200: {"description": "Document submission status"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Specialist not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_document_status(
    db: Session = Depends(get_db),
    specialist: Specialists = Depends(get_authenticated_specialist)
):
    """Get current document submission status for the specialist"""
    try:
        # Get specialist's approval data
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        if not approval_data:
            return {
                "documents_submitted": [],
                "missing_documents": MANDATORY_DOCUMENTS,
                "submission_complete": False,
                "total_submitted": 0,
                "total_required": len(MANDATORY_DOCUMENTS)
            }
        
        # Get submitted documents
        submitted_docs = db.query(SpecialistDocuments).filter(
            SpecialistDocuments.approval_data_id == approval_data.id
        ).all()
        
        submitted_types = [doc.document_type for doc in submitted_docs]
        missing_types = [doc_type for doc_type in MANDATORY_DOCUMENT_TYPES if doc_type not in submitted_types]
        
        # Convert missing types to full document info
        missing_documents = [doc for doc in MANDATORY_DOCUMENTS if doc["type"] in missing_types]
        
        submitted_documents = []
        for doc in submitted_docs:
            doc_info = next((d for d in MANDATORY_DOCUMENTS if d["type"] == doc.document_type), None)
            submitted_documents.append({
                "id": str(doc.id),
                "type": doc.document_type.value,
                "label": doc_info["label"] if doc_info else doc.document_type.value.replace('_', ' ').title(),
                "name": doc.document_name,
                "status": doc.verification_status.value,
                "uploaded_at": doc.upload_date.isoformat(),
                "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
                "verification_notes": doc.verification_notes
            })
        
        return {
            "documents_submitted": submitted_documents,
            "missing_documents": missing_documents,
            "submission_complete": len(missing_types) == 0,
            "total_submitted": len(submitted_docs),
            "total_required": len(MANDATORY_DOCUMENTS)
        }
        
    except Exception as e:
        print(f"Error fetching document status for {specialist.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch document status"
        )

@router.delete(
    "/documents/{document_id}",
    responses={
        200: {"description": "Document deleted successfully"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    specialist: Specialists = Depends(get_authenticated_specialist)
):
    """Delete a submitted document to allow replacement"""
    try:
        # Convert string ID to UUID
        try:
            doc_uuid = uuid.UUID(document_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid document ID format"
            )
        
        # Get specialist's approval data
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        if not approval_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No approval data found for this specialist"
            )
        
        # Find the document
        document = db.query(SpecialistDocuments).filter(
            SpecialistDocuments.id == doc_uuid,
            SpecialistDocuments.approval_data_id == approval_data.id
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or does not belong to this specialist"
            )
        
        # Delete the physical file if it exists
        if os.path.exists(document.file_path):
            try:
                os.remove(document.file_path)
                print(f"DEBUG: Physical file deleted: {document.file_path}")
            except Exception as e:
                print(f"DEBUG: Failed to delete physical file {document.file_path}: {str(e)}")
                # Continue with database deletion even if file deletion fails
        
        # Get document info for response
        doc_info = next((doc for doc in MANDATORY_DOCUMENTS if doc["type"] == document.document_type), None)
        doc_label = doc_info["label"] if doc_info else document.document_type.value.replace('_', ' ').title()
        
        # Delete from database
        db.delete(document)
        db.commit()
        
        print(f"DEBUG: Document '{document.document_name}' deleted successfully for specialist {specialist.email}")
        
        return {
            "message": f"Document '{doc_label}' deleted successfully",
            "document_type": document.document_type.value,
            "document_name": document.document_name
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting document for {specialist.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
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
        print(f"DEBUG: Document submission for specialist: {specialist.email}")
        print(f"DEBUG: Specialist ID: {specialist.id}")
        print(f"DEBUG: Document type: {document_type}")
        print(f"DEBUG: Document name: {document_name}")
        print(f"DEBUG: File size: {file.size} bytes")
        print(f"DEBUG: File type: {file.content_type}")
        print(f"DEBUG: Expiry date: {expiry_date}")
        
        # Validate document type is mandatory
        print(f"DEBUG: Validating document type")
        if document_type not in MANDATORY_DOCUMENT_TYPES:
            available_types = [doc["label"] for doc in MANDATORY_DOCUMENTS]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document type '{document_type.value}' is not in the mandatory documents list. Please upload one of: {', '.join(available_types)}"
            )
        
        # Validate file
        print(f"DEBUG: Validating uploaded file")
        validate_file_upload(file)
        print(f"DEBUG: File validation passed")
        
        # Parse expiry date if provided
        parsed_expiry_date = None
        if expiry_date:
            print(f"DEBUG: Parsing expiry date: {expiry_date}")
            try:
                parsed_expiry_date = datetime.fromisoformat(expiry_date)
                if parsed_expiry_date <= datetime.now():
                    print(f"DEBUG: Expiry date validation failed - date is in the past")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Document expiry date must be in the future"
                    )
                print(f"DEBUG: Expiry date parsed successfully: {parsed_expiry_date}")
            except ValueError:
                print(f"DEBUG: Expiry date parsing failed - invalid format")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid expiry date format. Use YYYY-MM-DD."
                )
        
        # Get or create approval data
        print(f"DEBUG: Getting or creating approval data for specialist ID: {specialist.id}")
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        if not approval_data:
            print(f"DEBUG: No existing approval data found, creating new record")
            approval_data = SpecialistsApprovalData(
                specialist_id=specialist.id,
                submission_date=datetime.now(timezone.utc),
                background_check_status='pending'
            )
            db.add(approval_data)
            db.flush()  # Get the ID
        
        # Check for duplicate document type
        print(f"DEBUG: Checking for existing document of type: {document_type}")
        existing_doc = db.query(SpecialistDocuments).filter(
            SpecialistDocuments.approval_data_id == approval_data.id,
            SpecialistDocuments.document_type == document_type
        ).first()
        
        if existing_doc:
            doc_info = next((doc for doc in MANDATORY_DOCUMENTS if doc["type"] == document_type), None)
            doc_label = doc_info["label"] if doc_info else document_type.value.replace('_', ' ').title()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Document '{doc_label}' has already been uploaded. Please delete the existing document first if you want to replace it."
            )
        
        # Save new file
        print(f"DEBUG: Saving uploaded file")
        try:
            file_path = save_uploaded_file(file, str(specialist.id), document_type.value)
            print(f"DEBUG: File saved successfully at: {file_path}")
        except Exception as e:
            print(f"DEBUG: File save error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file. Please try again."
            )
        
        # Create document record
        print(f"DEBUG: Creating document record in database")
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
        print(f"DEBUG: Document record added to database")
        
        # Update approval data submission date
        approval_data.submission_date = datetime.now(timezone.utc)
        print(f"DEBUG: Approval data submission date updated")
        
        # Commit transaction
        print(f"DEBUG: Committing document submission transaction")
        db.commit()
        print(f"DEBUG: Document transaction committed successfully")
        
        print(f"DEBUG: Document saved successfully with ID: {document.id}")
        
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
# SUBMIT FOR APPROVAL ENDPOINT
# ============================================================================

class SubmissionResponse(BaseModel):
    """Response for application submission"""
    success: bool
    message: str
    submission_date: datetime
    approval_status: str
    estimated_review_time: str
    next_steps: List[str]

@router.post(
    "/submit-for-approval",
    response_model=SubmissionResponse,
    responses={
        200: {"description": "Application submitted successfully"},
        400: {"model": ErrorResponse, "description": "Profile incomplete or validation failed"},
        403: {"model": ErrorResponse, "description": "Access denied or already submitted"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def submit_for_approval(
    db: Session = Depends(get_db),
    specialist: Specialists = Depends(get_authenticated_specialist)
):
    """Submit completed profile and documents for admin approval"""
    try:
        print(f"DEBUG: Submit for approval request from specialist: {specialist.email}")
        
        # Profile completion check removed - now handled in frontend
        print(f"DEBUG: Profile completion check bypassed - validation handled in frontend")
        
        # Check availability slots
        if not specialist.availability_slots or len(specialist.availability_slots) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one availability slot must be selected before submitting for approval."
            )
        
        # Check if all mandatory documents are uploaded
        mandatory_docs = [DocumentTypeEnum.IDENTITY_CARD, DocumentTypeEnum.DEGREE, 
                         DocumentTypeEnum.LICENSE, DocumentTypeEnum.EXPERIENCE_LETTER]
        
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        if not approval_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No documents uploaded. Please upload all required documents before submitting."
            )
        
        uploaded_doc_types = [doc.document_type for doc in approval_data.documents]
        missing_docs = [doc for doc in mandatory_docs if doc not in uploaded_doc_types]
        
        if missing_docs:
            missing_doc_names = []
            for doc_type in missing_docs:
                if doc_type == DocumentTypeEnum.IDENTITY_CARD:
                    missing_doc_names.append("Identity Card")
                elif doc_type == DocumentTypeEnum.DEGREE:
                    missing_doc_names.append("Degree Certificate") 
                elif doc_type == DocumentTypeEnum.LICENSE:
                    missing_doc_names.append("Professional License")
                elif doc_type == DocumentTypeEnum.EXPERIENCE_LETTER:
                    missing_doc_names.append("Experience Letter")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required documents: {', '.join(missing_doc_names)}. Please upload all documents before submitting."
            )
        
        # Check if already submitted for review
        if specialist.approval_status == ApprovalStatusEnum.UNDER_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application already submitted for review. Please wait for admin approval."
            )
        
        if specialist.approval_status == ApprovalStatusEnum.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application already approved. No need to resubmit."
            )
        
        # Update specialist status to under review
        specialist.approval_status = ApprovalStatusEnum.UNDER_REVIEW
        specialist.updated_at = datetime.now(timezone.utc)
        
        # Update approval data submission date
        approval_data.submission_date = datetime.now(timezone.utc)
        approval_data.background_check_status = 'under_review'
        
        # Commit changes
        db.commit()
        print(f"DEBUG: Specialist {specialist.email} status updated to UNDER_REVIEW")
        
        # Send admin notification
        admin_notified = notify_admins_application_submission(db, specialist)
        
        # Prepare response
        next_steps = [
            "Your application has been submitted for admin review",
            "You will receive an email notification when review is complete",
            "Estimated review time: 3-5 business days",
            "You can log in to check your approval status",
            "If approved, you'll gain access to the specialist dashboard"
        ]
        
        return SubmissionResponse(
            success=True,
            message="Application submitted successfully for admin approval",
            submission_date=datetime.now(timezone.utc),
            approval_status="under_review",
            estimated_review_time="3-5 business days",
            next_steps=next_steps
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Unexpected error during submission for {specialist.email}: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during submission: {str(e)}"
        )

@router.get(
    "/approval-status",
    responses={
        200: {"description": "Approval status retrieved successfully"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_approval_status(
    db: Session = Depends(get_db),
    specialist: Specialists = Depends(get_authenticated_specialist)
):
    """Get current approval status and profile completion information"""
    try:
        print(f"DEBUG: Approval status check for specialist: {specialist.email}")
        
        # Profile completion calculation removed - now handled in frontend
        
        # Check document submission status
        approval_data = db.query(SpecialistsApprovalData).filter(
            SpecialistsApprovalData.specialist_id == specialist.id
        ).first()
        
        documents_uploaded = 0
        if approval_data:
            documents_uploaded = len(approval_data.documents)
        
        # Determine next action based on status
        next_action = "unknown"
        redirect_to = "/"
        
        if specialist.approval_status == ApprovalStatusEnum.PENDING:
            # Since profile completion is now handled in frontend, 
            # we only check documents for the next action
            if documents_uploaded < 4:
                next_action = "upload_documents" 
                redirect_to = "/complete-profile?tab=documents"
            else:
                next_action = "submit_for_approval"
                redirect_to = "/complete-profile?tab=documents"
        elif specialist.approval_status == ApprovalStatusEnum.UNDER_REVIEW:
            next_action = "pending_approval"
            redirect_to = "/pending-approval"
        elif specialist.approval_status == ApprovalStatusEnum.APPROVED:
            next_action = "access_dashboard"
            redirect_to = "/specialist-dashboard"
        elif specialist.approval_status == ApprovalStatusEnum.REJECTED:
            next_action = "application_rejected"
            redirect_to = "/application-rejected"
        
        return {
            "approval_status": specialist.approval_status.value,
            "profile_completion_percentage": 100,  # Always 100% since validation is in frontend
            "missing_fields": [],  # No missing fields since validation is in frontend
            "documents_uploaded": documents_uploaded,
            "documents_required": 4,
            "next_action": next_action,
            "redirect_to": redirect_to,
            "submission_date": approval_data.submission_date if approval_data else None,
            "can_access_dashboard": specialist.approval_status == ApprovalStatusEnum.APPROVED
        }
        
    except Exception as e:
        print(f"ERROR: Failed to get approval status for {specialist.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval status"
        )

def notify_admins_application_submission(db: Session, specialist: Specialists) -> bool:
    """Notify admins about new specialist application submission"""
    try:
        print(f"DEBUG: Sending admin notification for application submission: {specialist.email}")
        
        # Get admin emails
        admin_emails = get_admin_emails_for_notifications(db)
        if not admin_emails:
            print("WARNING: No admin emails found for notifications")
            return False
        
        # Get primary specialization
        primary_spec = None
        if specialist.specializations:
            primary_spec = next((spec for spec in specialist.specializations if spec.is_primary_specialization), None)
        
        specialization_name = safe_enum_to_string(primary_spec.specialization) if primary_spec else "Mental Health Specialist"
        
        # Send enhanced admin notification email to each admin
        success_count = 0
        for admin_email in admin_emails:
            try:
                email_sent = send_admin_specialist_registration_notification(
                    admin_email=admin_email,
                    specialist_email=specialist.email,
                    first_name=specialist.first_name,
                    last_name=specialist.last_name,
                    specialization=specialization_name,
                    registration_date=datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
                )
                if email_sent:
                    success_count += 1
                    print(f"DEBUG: Admin notification sent successfully to {admin_email}")
                else:
                    print(f"WARNING: Failed to send admin notification to {admin_email}")
            except Exception as e:
                print(f"ERROR: Failed to send admin notification to {admin_email}: {str(e)}")
        
        # Return True if at least one email was sent successfully
        return success_count > 0
        
    except Exception as e:
        print(f"ERROR: Failed to send admin notification for {specialist.email}: {str(e)}")
        return False

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "router",
    "complete_profile",
    "submit_documents",
    "submit_for_approval",
    "get_approval_status",
    "ProfileCompletionRequest",
    "DocumentSubmissionRequest",
    "SubmissionResponse",
    "ProfileCompletionResponse",
    "DocumentSubmissionResponse"
]
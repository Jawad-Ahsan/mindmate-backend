"""
Specialist Profile and Document Submission Pydantic Schemas
==========================================================
Schemas for specialist profile completion, document submission, and approval status
Updated for Pydantic v2
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator
from enum import Enum
import re


from models.sql_models.specialist_models import (
    SpecializationEnum, DocumentTypeEnum, SpecialistTypeEnum,
    ApprovalStatusEnum, EmailVerificationStatusEnum, DocumentStatusEnum
)



# ============================================================================
# ENUMS FOR VALIDATION (Mirror your SQLAlchemy enums)
# ============================================================================

class SpecializationEnum(str, Enum):
    """Specialization areas"""
    ANXIETY_DISORDERS = "anxiety_disorders"
    DEPRESSION = "depression"
    TRAUMA_PTSD = "trauma_ptsd"
    COUPLES_THERAPY = "couples_therapy"
    FAMILY_THERAPY = "family_therapy"
    ADDICTION = "addiction"
    EATING_DISORDERS = "eating_disorders"
    ADHD = "adhd"
    BIPOLAR_DISORDER = "bipolar_disorder"
    OCD = "ocd"
    PERSONALITY_DISORDERS = "personality_disorders"
    GRIEF_COUNSELING = "grief_counseling"

class DocumentTypeEnum(str, Enum):
    """Document types for approval"""
    # Mandatory Documents
    CNIC_FRONT = "cnic_front"
    CNIC_BACK = "cnic_back"
    DEGREE_CERTIFICATE = "degree_certificate"
    LICENSE_REGISTRATION = "license_registration"
    EXPERIENCE_CERTIFICATE = "experience_certificate"
    RECENT_PHOTOGRAPH = "recent_photograph"
    ETHICS_DECLARATION = "ethics_declaration"
    
    # Optional Documents
    DIPLOMA_CERTIFICATION = "diploma_certification"
    INTERNATIONAL_MEMBERSHIP = "international_membership"
    RESEARCH_PUBLICATION = "research_publication"
    REFERENCE_LETTER = "reference_letter"
    
    # Legacy/Other
    OTHER = "other"

class SpecialistTypeEnum(str, Enum):
    """Mental health specialist types"""
    PSYCHIATRIST = "psychiatrist"
    PSYCHOLOGIST = "psychologist"
    COUNSELOR = "counselor"
    THERAPIST = "therapist"
    SOCIAL_WORKER = "social_worker"

class ApprovalStatusEnum(str, Enum):
    """Admin approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"

class EmailVerificationStatusEnum(str, Enum):
    """Email verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class DocumentStatusEnum(str, Enum):
    """Document verification status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_RESUBMISSION = "needs_resubmission"

# ============================================================================
# COMPLETE PROFILE SCHEMAS
# ============================================================================

class ProfessionalMembership(BaseModel):
    """Professional membership details"""
    organization_name: str = Field(..., min_length=2, max_length=200, description="Name of professional organization")
    membership_id: Optional[str] = Field(None, max_length=50, description="Membership ID/Number")
    membership_type: Optional[str] = Field(None, max_length=100, description="Type of membership (e.g., Fellow, Member)")
    valid_from: Optional[date] = Field(None, description="Membership start date")
    valid_until: Optional[date] = Field(None, description="Membership expiry date")
    
    @field_validator('organization_name')
    @classmethod
    def validate_organization_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip()

class Certification(BaseModel):
    """Additional certification details"""
    certification_name: str = Field(..., min_length=2, max_length=200, description="Name of certification")
    issuing_authority: str = Field(..., min_length=2, max_length=200, description="Authority that issued the certification")
    certification_id: Optional[str] = Field(None, max_length=50, description="Certification ID/Number")
    issue_date: Optional[date] = Field(None, description="Date certification was issued")
    expiry_date: Optional[date] = Field(None, description="Date certification expires")
    
    @field_validator('certification_name', 'issuing_authority')
    @classmethod
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError('This field cannot be empty')
        return v.strip()

class SpecialistSpecialization(BaseModel):
    """Specialist's area of specialization"""
    specialization: SpecializationEnum = Field(..., description="Specialization area")
    years_of_experience: int = Field(0, ge=0, le=50, description="Years of experience in this specialization")
    certification_date: Optional[date] = Field(None, description="Date of specialization certification")
    is_primary: bool = Field(False, description="Whether this is the primary specialization")
    
    @field_validator('years_of_experience')
    @classmethod
    def validate_experience(cls, v):
        if v < 0 or v > 50:
            raise ValueError('Years of experience must be between 0 and 50')
        return v

class SocialMediaLinks(BaseModel):
    """Social media and professional links"""
    linkedin: Optional[str] = Field(None, max_length=500, description="LinkedIn profile URL")
    twitter: Optional[str] = Field(None, max_length=500, description="Twitter profile URL")
    facebook: Optional[str] = Field(None, max_length=500, description="Facebook profile URL")
    instagram: Optional[str] = Field(None, max_length=500, description="Instagram profile URL")
    professional_website: Optional[str] = Field(None, max_length=500, description="Professional website URL")
    
    @field_validator('linkedin', 'twitter', 'facebook', 'instagram', 'professional_website')
    @classmethod
    def validate_urls(cls, v):
        if v and not re.match(r'^https?://', v):
            raise ValueError('URL must start with http:// or https://')
        return v

# ============================================================================
# DOCUMENT SUBMISSION SCHEMAS  
# ============================================================================

class DocumentSubmission(BaseModel):
    """Individual document submission"""
    document_type: DocumentTypeEnum = Field(..., description="Type of document")
    document_name: str = Field(..., min_length=2, max_length=255, description="Document name/title")
    file_path: str = Field(..., min_length=5, max_length=500, description="File path or URL")
    file_size: int = Field(..., gt=0, le=50*1024*1024, description="File size in bytes (max 50MB)")
    mime_type: str = Field(..., description="MIME type of the file")
    expiry_date: Optional[date] = Field(None, description="Document expiry date (if applicable)")
    
    @field_validator('document_name')
    @classmethod
    def validate_document_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Document name cannot be empty')
        return v.strip()
    
    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        if not v or not v.strip():
            raise ValueError('File path cannot be empty')
        return v.strip()
    
    @field_validator('mime_type')
    @classmethod
    def validate_mime_type(cls, v):
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        if v not in allowed_types:
            raise ValueError(f'Unsupported file type: {v}. Allowed types: {", ".join(allowed_types)}')
        return v

class CompleteProfileRequest(BaseModel):
    """Comprehensive request schema for completing specialist profile and submitting documents"""
    
    # ============================================================================
    # PROFILE INFORMATION
    # ============================================================================
    
    # Contact & Location Details
    address: str = Field(..., min_length=10, max_length=500, description="Full address")
    clinic_name: Optional[str] = Field(None, max_length=200, description="Name of clinic/practice")
    website_url: Optional[str] = Field(None, max_length=500, description="Professional website URL")
    
    # Professional Information
    bio: str = Field(..., min_length=50, max_length=2000, description="Professional biography")
    consultation_fee: float = Field(..., gt=0, le=50000, description="Consultation fee in PKR")
    languages_spoken: List[str] = Field(..., min_items=1, description="Languages spoken (language codes)")
    
    # Specializations
    specializations: List[SpecialistSpecialization] = Field(
        ..., 
        min_items=1, 
        max_items=5, 
        description="Areas of specialization"
    )
    
    # Professional Credentials
    professional_memberships: Optional[List[ProfessionalMembership]] = Field(
        None, 
        max_items=10, 
        description="Professional organization memberships"
    )
    certifications: Optional[List[Certification]] = Field(
        None, 
        max_items=15, 
        description="Additional certifications"
    )
    
    # Social Media & Online Presence
    social_media_links: Optional[SocialMediaLinks] = Field(None, description="Social media links")
    
    # Profile Media
    profile_image_url: Optional[str] = Field(None, max_length=500, description="Profile image URL")
    
    # ============================================================================
    # DOCUMENT SUBMISSION
    # ============================================================================
    
    # Professional Credentials (from approval_data table)
    license_number: Optional[str] = Field(None, max_length=100, description="Professional license number")
    license_issuing_authority: Optional[str] = Field(None, max_length=200, description="Authority that issued the license")
    license_issue_date: Optional[date] = Field(None, description="License issue date")
    license_expiry_date: Optional[date] = Field(None, description="License expiry date")
    
    # Educational Information
    highest_degree: Optional[str] = Field(None, max_length=100, description="Highest educational degree")
    university_name: Optional[str] = Field(None, max_length=200, description="University/Institution name")
    graduation_year: Optional[int] = Field(None, ge=1950, le=datetime.now().year, description="Graduation year")
    
    # Identity Information
    cnic: Optional[str] = Field(None, description="CNIC number (Pakistani National ID)")
    passport_number: Optional[str] = Field(None, max_length=20, description="Passport number")
    
    # Documents
    documents: List[DocumentSubmission] = Field(
        ..., 
        min_items=1, 
        max_items=20, 
        description="List of documents to submit"
    )
    
    # Additional Notes
    submission_notes: Optional[str] = Field(None, max_length=1000, description="Additional notes for admin review")
    
    # ============================================================================
    # ETHICS DECLARATION
    # ============================================================================
    
    ethics_declaration_signed: bool = Field(..., description="Must be true to complete profile")
    
    # ============================================================================
    # VALIDATORS
    # ============================================================================
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Address must be at least 10 characters long')
        return v.strip()
    
    @field_validator('bio')
    @classmethod
    def validate_bio(cls, v):
        if not v or len(v.strip()) < 50:
            raise ValueError('Bio must be at least 50 characters long')
        if len(v.strip()) > 2000:
            raise ValueError('Bio cannot exceed 2000 characters')
        return v.strip()
    
    @field_validator('consultation_fee')
    @classmethod
    def validate_fee(cls, v):
        if v <= 0:
            raise ValueError('Consultation fee must be greater than 0')
        if v > 50000:
            raise ValueError('Consultation fee cannot exceed PKR 50,000')
        return round(float(v), 2)
    
    @field_validator('languages_spoken')
    @classmethod
    def validate_languages(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one language must be specified')
        
        valid_languages = [
            'en', 'ur', 'punjabi', 'sindhi', 'pashto', 'balochi', 
            'saraiki', 'hindko', 'brahui', 'arabic', 'persian'
        ]
        
        for lang in v:
            if lang.lower() not in valid_languages:
                raise ValueError(f'Invalid language code: {lang}')
        
        return [lang.lower() for lang in set(v)]  # Remove duplicates and normalize
    
    @field_validator('website_url', 'profile_image_url')
    @classmethod
    def validate_urls(cls, v):
        if v and not re.match(r'^https?://', v):
            raise ValueError('URL must start with http:// or https://')
        return v
    
    @field_validator('cnic')
    @classmethod
    def validate_cnic(cls, v):
        if v and not re.match(r'^\d{5}-\d{7}-\d{1}$', v):
            raise ValueError('CNIC must be in format: XXXXX-XXXXXXX-X')
        return v
    
    @field_validator('passport_number')
    @classmethod
    def validate_passport(cls, v):
        if v and (len(v.strip()) < 5 or len(v.strip()) > 20):
            raise ValueError('Passport number must be between 5 and 20 characters')
        return v.strip() if v else None
    
    @field_validator('license_number')
    @classmethod
    def validate_license_number(cls, v):
        if v and len(v.strip()) < 3:
            raise ValueError('License number must be at least 3 characters')
        return v.strip() if v else None
    
    @field_validator('graduation_year')
    @classmethod
    def validate_graduation_year(cls, v):
        current_year = datetime.now().year
        if v and (v < 1950 or v > current_year):
            raise ValueError(f'Graduation year must be between 1950 and {current_year}')
        return v
    
    @model_validator(mode='after')
    def validate_specializations(self):
        specializations = self.specializations
        if not specializations:
            return self
        
        # Check that only one primary specialization exists
        primary_count = sum(1 for s in specializations if s.is_primary)
        if primary_count > 1:
            raise ValueError('Only one primary specialization is allowed')
        
        # If no primary is set, make the first one primary
        if primary_count == 0 and specializations:
            specializations[0].is_primary = True
        
        return self
    
    @model_validator(mode='after')
    def validate_document_requirements(self):
        documents = self.documents
        if not documents:
            raise ValueError('At least one document must be submitted')
        
        # Check for required document types
        doc_types = [doc.document_type for doc in documents]
        
        # Ensure no duplicate document types
        if len(doc_types) != len(set(doc_types)):
            raise ValueError('Duplicate document types are not allowed')
        
        # Check for mandatory documents
        mandatory_docs = [
            DocumentTypeEnum.CNIC_FRONT,
            DocumentTypeEnum.CNIC_BACK,
            DocumentTypeEnum.DEGREE_CERTIFICATE,
            DocumentTypeEnum.LICENSE_REGISTRATION,
            DocumentTypeEnum.EXPERIENCE_CERTIFICATE,
            DocumentTypeEnum.RECENT_PHOTOGRAPH,
            DocumentTypeEnum.ETHICS_DECLARATION
        ]
        missing_mandatory = [doc_type for doc_type in mandatory_docs if doc_type not in doc_types]
        
        if missing_mandatory:
            missing_names = [doc_type.value.replace('_', ' ').title() for doc_type in missing_mandatory]
            raise ValueError(f'Mandatory documents missing: {", ".join(missing_names)}')
        
        return self
    
    @model_validator(mode='after')
    def validate_license_consistency(self):
        license_number = self.license_number
        documents = self.documents
        
        # If license document is provided, license number should also be provided
        has_license_doc = any(doc.document_type == DocumentTypeEnum.LICENSE_REGISTRATION for doc in documents)
        
        if has_license_doc and not license_number:
            raise ValueError('License number is required when submitting license document')
        
        return self
    
    @model_validator(mode='after')
    def validate_ethics_declaration(self):
        if not self.ethics_declaration_signed:
            raise ValueError('Ethics declaration must be signed to complete profile')
        return self

class CompleteProfileResponse(BaseModel):
    """Response schema for comprehensive profile completion and document submission"""
    message: str
    profile_complete: bool
    documents_submitted: bool
    ethics_declaration_signed: bool
    user_id: str
    submission_id: Optional[str]
    total_documents: int
    next_steps: List[str]
    profile_summary: Dict[str, Any]
    estimated_review_time: str
    admin_notified: bool


# ============================================================================
# APPROVAL STATUS SCHEMAS
# ============================================================================

class DocumentStatusInfo(BaseModel):
    """Document status information"""
    document_id: str
    document_type: str
    document_name: str
    verification_status: str
    uploaded_date: datetime
    verified_date: Optional[datetime]
    verification_notes: Optional[str]
    expiry_date: Optional[date]
    is_expired: bool

class ApprovalStatusResponse(BaseModel):
    """Response schema for getting approval status"""
    user_id: str
    email: str
    full_name: str
    
    # Overall Status
    approval_status: str
    email_verification_status: str
    can_practice: bool
    
    # Profile Status
    profile_complete: bool
    documents_submitted: bool
    
    # Submission Information
    submission_date: Optional[datetime]
    reviewed_date: Optional[datetime]
    reviewed_by: Optional[str]
    days_since_submission: Optional[int]
    
    # Documents Status
    total_documents: int
    documents_approved: int
    documents_pending: int
    documents_rejected: int
    documents: List[DocumentStatusInfo]
    
    # Review Information
    approval_notes: Optional[str]
    rejection_reason: Optional[str]
    background_check_status: Optional[str]
    background_check_date: Optional[datetime]
    
    # Professional Information
    license_number: Optional[str]
    license_expiry_date: Optional[date]
    license_valid: Optional[bool]
    
    # Next Steps
    next_steps: List[str]
    status_message: str
    estimated_review_time: Optional[str]

# ============================================================================
# ERROR RESPONSE SCHEMA
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str
    error_code: Optional[str] = None
    field_errors: Optional[Dict[str, List[str]]] = None

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "SpecializationEnum",
    "DocumentTypeEnum", 
    "SpecialistTypeEnum",
    "ApprovalStatusEnum",
    "EmailVerificationStatusEnum",
    "DocumentStatusEnum",
    
    # Profile Completion
    "ProfessionalMembership",
    "Certification",
    "SpecialistSpecialization",
    "SocialMediaLinks",
    "CompleteProfileRequest",
    "CompleteProfileResponse",
    
    # Document Submission
    "DocumentSubmission",
    
    # Approval Status
    "DocumentStatusInfo",
    "ApprovalStatusResponse",
    
    # Common
    "ErrorResponse"
]
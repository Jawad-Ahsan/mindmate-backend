"""
Specialists Models - Normalized Database Design
=============================================
Follows best practices with proper table normalization and naming conventions
Separates concerns into multiple related tables for better maintainability
"""

from typing import List, Optional
from sqlalchemy import (
    Column, String, DateTime, Boolean, Enum, JSON, Text, Integer, 
    Numeric, ForeignKey, UniqueConstraint, CheckConstraint, Index,
    func, text
)
from sqlalchemy.orm import validates, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta, timezone
import enum
import uuid
import re
import bcrypt

# Import base model
from .base_model import Base, BaseModel as SQLBaseModel, USERTYPE

# ============================================================================
# ENUMERATIONS
# ============================================================================

class GenderEnum(str, enum.Enum):
    """Gender identity options"""
    MALE = "male"
    FEMALE = "female"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"
    OTHER = "other"


class SpecialistTypeEnum(str, enum.Enum):
    """Mental health specialist types"""
    PSYCHIATRIST = "psychiatrist"
    PSYCHOLOGIST = "psychologist" 
    COUNSELOR = "counselor"
    THERAPIST = "therapist"
    SOCIAL_WORKER = "social_worker"

class SpecializationEnum(str, enum.Enum):
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

class AvailabilityStatusEnum(str, enum.Enum):
    """Patient acceptance status"""
    ACCEPTING_NEW_PATIENTS = "accepting_new_patients"
    WAITLIST_ONLY = "waitlist_only"
    NOT_ACCEPTING = "not_accepting_new_patients"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"

class ApprovalStatusEnum(str, enum.Enum):
    """Admin approval status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
    UNDER_REVIEW = "under_review"

class EmailVerificationStatusEnum(str, enum.Enum):
    """Email verification status"""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

class DocumentTypeEnum(str, enum.Enum):
    """Document types for approval"""
    DEGREE = "degree"
    LICENSE = "license"
    CERTIFICATION = "certification"
    IDENTITY_CARD = "identity_card"
    EXPERIENCE_LETTER = "experience_letter"
    OTHER = "other"

class DocumentStatusEnum(str, enum.Enum):
    """Document verification status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_RESUBMISSION = "needs_resubmission"

# ============================================================================
# CORE SPECIALIST TABLE
# ============================================================================

class Specialists(Base, SQLBaseModel):
    """
    Core specialist information table
    Contains basic professional and personal information
    """
    __tablename__ = "specialists"

    # Personal Information
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)  # Made nullable for new flow
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)  # Made nullable for new flow

    
    # Professional Information
    specialist_type = Column(SA_Enum(SpecialistTypeEnum), nullable=True, index=True)  # Made nullable for new flow
    years_experience = Column(Integer, default=0, nullable=True)  # Made nullable for new flow
    
    # Consent to policy
    accepts_terms_and_conditions = Column(Boolean, default=False)
    
    # Contact & Location
    city = Column(String(100), nullable=True, index=True)  # Made nullable for new flow
    address = Column(Text, nullable=True)
    clinic_name = Column(String(200), nullable=True)
    
    # Practice Information
    consultation_fee = Column(Numeric(10, 2), nullable=True)
    bio = Column(Text, nullable=True)
    languages_spoken = Column(JSON, nullable=True, comment="Array of language codes")
    
    # Status & Ratings
    availability_status = Column(
        SA_Enum(AvailabilityStatusEnum), 
        default=AvailabilityStatusEnum.ACCEPTING_NEW_PATIENTS,
        nullable=False,
        index=True
    )
    approval_status = Column(
        SA_Enum(ApprovalStatusEnum), 
        default=ApprovalStatusEnum.PENDING,
        nullable=False,
        index=True
    )
    average_rating = Column(Numeric(3, 2), default=0.0, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    total_appointments = Column(Integer, default=0, nullable=False)
    
    # Metadata
    profile_image_url = Column(String(500), nullable=True)
    website_url = Column(String(500), nullable=True)
    social_media_links = Column(JSON, nullable=True)
    
    # Relationships
    auth_info = relationship("SpecialistsAuthInfo", back_populates="specialist", uselist=False, cascade="all, delete-orphan")
    approval_data = relationship("SpecialistsApprovalData", back_populates="specialist", cascade="all, delete-orphan")
    specializations = relationship("SpecialistSpecializations", back_populates="specialist", cascade="all, delete-orphan")
    
    # External relationships (to be defined in other models)
    appointments = relationship("Appointment", back_populates="specialist", lazy="dynamic", cascade="all, delete-orphan")
    forum_answers = relationship("ForumAnswer", back_populates="specialist", lazy="dynamic", cascade="all, delete-orphan")  
    # reviews = relationship("Review", back_populates="specialist", lazy="dynamic")

    # Table Constraints
    __table_args__ = (
        # Only apply experience constraint if years_experience is not None
        CheckConstraint('(years_experience IS NULL) OR (years_experience >= 0 AND years_experience <= 60)', name='chk_specialists_experience_range'),
        CheckConstraint('average_rating >= 0.0 AND average_rating <= 5.0', name='chk_specialists_rating_range'),
        CheckConstraint('(consultation_fee IS NULL) OR (consultation_fee >= 0)', name='chk_specialists_fee_positive'),
        CheckConstraint('total_reviews >= 0', name='chk_specialists_reviews_positive'),
        CheckConstraint('total_appointments >= 0', name='chk_specialists_appointments_positive'),
        Index('idx_specialists_name', 'first_name', 'last_name'),
        Index('idx_specialists_status', 'approval_status', 'availability_status'),
        Index('idx_specialists_rating', 'average_rating', 'total_reviews'),
        {'extend_existing': True}
    )
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    @hybrid_property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @hybrid_property  
    def is_approved(self) -> bool:
        return self.approval_status == ApprovalStatusEnum.APPROVED

    @hybrid_property
    def is_accepting_patients(self) -> bool:
        return self.availability_status == AvailabilityStatusEnum.ACCEPTING_NEW_PATIENTS

    @hybrid_property
    def can_practice(self) -> bool:
        return (
            self.is_approved and 
            self.auth_info and 
            self.auth_info.is_email_verified and
            not self.is_deleted
        )
    
    # ============================================================================
    # VALIDATION METHODS - MODIFIED FOR NEW REGISTRATION FLOW
    # ============================================================================
    
    @validates('phone')
    def validate_phone(self, key, phone):
        # Phone is now optional during registration, only validate format if provided
        if phone and not re.match(r'^\+?92[0-9]{10}$', phone):
            raise ValueError("Phone must be in Pakistani format: +92XXXXXXXXXX")
        return phone

    @validates('years_experience')
    def validate_experience(self, key, experience):
        if experience is not None and (experience < 0 or experience > 60):
            raise ValueError("Years of experience must be between 0 and 60")
        return experience or 0

    @validates('consultation_fee')
    def validate_fee(self, key, fee):
        if fee is not None and fee < 0:
            raise ValueError("Consultation fee cannot be negative")
        return fee
    
    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    
    def update_rating(self, new_rating: float) -> None:
        """Update average rating with new review"""
        if not (1.0 <= new_rating <= 5.0):
            raise ValueError("Rating must be between 1.0 and 5.0")
        
        if self.total_reviews == 0:
            self.average_rating = new_rating
            self.total_reviews = 1
        else:
            total_rating = float(self.average_rating) * self.total_reviews
            self.total_reviews += 1
            self.average_rating = (total_rating + new_rating) / self.total_reviews

    def increment_appointment_count(self) -> None:
        """Increment total appointment count"""
        self.total_appointments += 1

    def __repr__(self) -> str:
        specialist_type_str = self.specialist_type.value if self.specialist_type else "Not Specified"
        city_str = self.city if self.city else "Not Specified"
        return f"<Specialist({self.full_name}, {specialist_type_str}, {city_str})>"

# ============================================================================
# AUTHENTICATION INFORMATION TABLE
# ============================================================================

class SpecialistsAuthInfo(Base, SQLBaseModel):
    """
    Authentication and security information for specialists
    Separated for security and performance reasons
    """
    __tablename__ = "specialists_auth_info"

    # Foreign Key
    specialist_id = Column(UUID(as_uuid=True), ForeignKey('specialists.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Authentication
    hashed_password = Column(String(128), nullable=True)  # Nullable for OAuth
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Login Tracking
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Email Verification
    email_verification_status = Column(
        SA_Enum(EmailVerificationStatusEnum),
        default=EmailVerificationStatusEnum.PENDING,
        nullable=False,
        index=True
    )
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # OTP for 2FA/Verification
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    otp_attempts = Column(Integer, default=0, nullable=False)
    
    # Session Management
    last_activity_at = Column(DateTime(timezone=True), nullable=True)
    user_type = Column(SA_Enum(USERTYPE), default=USERTYPE.SPECIALIST, nullable=False)
    
    # Security Settings
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(32), nullable=True)
    two_factor_expires = Column(DateTime(timezone=True), nullable=True) #after expiry time re-ask the secret for authentication
    
    
    # Relationship
    specialist = relationship("Specialists", back_populates="auth_info")

    # Table Constraints
    __table_args__ = (
        CheckConstraint('failed_login_attempts >= 0', name='chk_auth_failed_attempts_positive'),
        CheckConstraint('otp_attempts >= 0', name='chk_auth_otp_attempts_positive'),
        Index('idx_specialist_auth_last_login', 'last_login_at'), 
        Index('idx_auth_verification_status', 'email_verification_status'),
        {'extend_existing': True}
    )
    
    # ============================================================================
    # PROPERTIES 
    # ============================================================================
    
    @hybrid_property
    def is_email_verified(self) -> bool:
        return self.email_verification_status == EmailVerificationStatusEnum.VERIFIED
    
    @hybrid_property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
    
    @hybrid_property
    def needs_password_reset(self) -> bool:
        if self.password_reset_expires is None:
            return False
        return datetime.now(timezone.utc) < self.password_reset_expires
    
    # ============================================================================
    # AUTHENTICATION METHODS
    # ============================================================================
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Clear any password reset tokens
        self.password_reset_token = None
        self.password_reset_expires = None

    def check_password(self, password: str) -> bool:
        """Verify password"""
        if not self.hashed_password:
            return False
        return bcrypt.checkpw(
            password.encode('utf-8'), 
            self.hashed_password.encode('utf-8')
        )

    def increment_failed_login(self) -> None:
        """Track failed login attempts"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    def reset_failed_login(self) -> None:
        """Reset failed login counter on successful login"""
        self.failed_login_attempts = 0
        self.locked_until = None
        self.last_login_at = datetime.now(timezone.utc)

    def generate_otp(self) -> str:
        """Generate OTP for verification"""
        import random
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_code = otp
        self.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        self.otp_attempts = 0
        return otp

    def verify_otp(self, otp: str) -> bool:
        """Verify OTP code"""
        if not self.otp_code or not self.otp_expires_at:
            return False
        
        if datetime.now(timezone.utc) > self.otp_expires_at:
            return False
        
        if self.otp_attempts >= 3:
            return False
        
        if self.otp_code != otp:
            self.otp_attempts += 1
            return False
        
        # Clear OTP on successful verification
        self.otp_code = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        return True

    def mark_email_verified(self) -> None:
        """Mark email as verified"""
        self.email_verification_status = EmailVerificationStatusEnum.VERIFIED
        self.email_verified_at = datetime.now(timezone.utc)
        self.email_verification_token = None
        self.email_verification_expires = None

# ============================================================================
# APPROVAL DATA TABLE
# ============================================================================

class SpecialistsApprovalData(Base, SQLBaseModel):
    """
    Approval process data including documents, certifications, etc.
    Contains all information needed for admin approval
    """
    __tablename__ = "specialists_approval_data"

    # Foreign Key
    specialist_id = Column(UUID(as_uuid=True), ForeignKey('specialists.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Professional Credentials
    license_number = Column(String(100), nullable=True, index=True)
    license_issuing_authority = Column(String(200), nullable=True)
    license_issue_date = Column(DateTime(timezone=True), nullable=True)
    license_expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Educational Background
    highest_degree = Column(String(100), nullable=True)
    university_name = Column(String(200), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    
    # Professional Memberships
    professional_memberships = Column(JSON, nullable=True, comment="Array of professional body memberships")
    certifications = Column(JSON, nullable=True, comment="Array of additional certifications")
    
    # Identity Information
    cnic = Column(String(15), nullable=True, unique=True)  # Pakistani CNIC
    passport_number = Column(String(20), nullable=True)
    
    # Approval Process
    submission_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)  # Admin user ID
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Background Check
    background_check_status = Column(String(20), default='pending', nullable=False)
    background_check_date = Column(DateTime(timezone=True), nullable=True)
    background_check_notes = Column(Text, nullable=True)
    
    # Relationship
    specialist = relationship("Specialists", back_populates="approval_data")
    documents = relationship("SpecialistDocuments", back_populates="approval_data", cascade="all, delete-orphan")

    # Table Constraints
    __table_args__ = (
        CheckConstraint('graduation_year >= 1950 AND graduation_year <= EXTRACT(YEAR FROM NOW())', name='chk_approval_graduation_year_valid'),
        Index('idx_approval_license', 'license_number'),
        Index('idx_approval_cnic', 'cnic'),
        Index('idx_approval_submission', 'submission_date'),
        Index('idx_approval_review_status', 'reviewed_at'),
        {'extend_existing': True}
    )
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    @hybrid_property
    def is_license_valid(self) -> bool:
        if not self.license_expiry_date:
            return True  # No expiry date means permanent
        return datetime.now(timezone.utc) < self.license_expiry_date
    
    @hybrid_property
    def is_reviewed(self) -> bool:
        return self.reviewed_at is not None
    
    @hybrid_property
    def days_since_submission(self) -> int:
        return (datetime.now(timezone.utc) - self.submission_date).days
    
    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    @validates('cnic')
    def validate_cnic(self, key, cnic):
        if cnic and not re.match(r'^\d{5}-\d{7}-\d{1}$', cnic):
            raise ValueError("CNIC must be in format: XXXXX-XXXXXXX-X")
        return cnic
    
    @validates('license_number')
    def validate_license(self, key, license_number):
        if license_number and len(license_number.strip()) < 3:
            raise ValueError("License number must be at least 3 characters")
        return license_number.strip() if license_number else None

    def __repr__(self) -> str:
        return f"<ApprovalData(specialist_id={self.specialist_id}, license={self.license_number})>"

# ============================================================================
# SPECIALIST DOCUMENTS TABLE
# ============================================================================

class SpecialistDocuments(Base, SQLBaseModel):
    """
    Document storage for approval process
    Stores references to uploaded documents
    """
    __tablename__ = "specialist_documents"

    # Foreign Key
    approval_data_id = Column(UUID(as_uuid=True), ForeignKey('specialists_approval_data.id', ondelete='CASCADE'), nullable=False)
    
    # Document Information
    document_type = Column(SA_Enum(DocumentTypeEnum), nullable=False, index=True)
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Document Status
    verification_status = Column(
        SA_Enum(DocumentStatusEnum),
        default=DocumentStatusEnum.PENDING,
        nullable=False,
        index=True
    )
    verified_by = Column(UUID(as_uuid=True), nullable=True)  # Admin user ID
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # Metadata
    upload_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    expiry_date = Column(DateTime(timezone=True), nullable=True)  # For documents that expire
    
    # Relationship
    approval_data = relationship("SpecialistsApprovalData", back_populates="documents")

    # Table Constraints
    __table_args__ = (
        CheckConstraint('file_size > 0', name='chk_documents_file_size_positive'),
        Index('idx_documents_type_status', 'document_type', 'verification_status'),
        Index('idx_documents_upload_date', 'upload_date'),
        {'extend_existing': True}
    )
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    @hybrid_property
    def is_verified(self) -> bool:
        return self.verification_status == DocumentStatusEnum.APPROVED
    
    @hybrid_property
    def is_expired(self) -> bool:
        if not self.expiry_date:
            return False
        return datetime.now(timezone.utc) > self.expiry_date
    
    @hybrid_property
    def file_size_mb(self) -> float:
        return round(self.file_size / (1024 * 1024), 2)

    def __repr__(self) -> str:
        return f"<Document({self.document_type.value}, {self.document_name})>"

# ============================================================================
# SPECIALIST SPECIALIZATIONS TABLE (Many-to-Many)
# ============================================================================

class SpecialistSpecializations(Base, SQLBaseModel):
    """
    Junction table for specialist specializations
    Allows multiple specializations per specialist
    """
    __tablename__ = "specialist_specializations"

    # Foreign Key
    specialist_id = Column(UUID(as_uuid=True), ForeignKey('specialists.id', ondelete='CASCADE'), nullable=False)
    
    # Specialization
    specialization = Column(SA_Enum(SpecializationEnum), nullable=False)
    
    # Additional Information
    years_of_experience_in_specialization = Column(Integer, default=0, nullable=False)
    certification_date = Column(DateTime(timezone=True), nullable=True)
    is_primary_specialization = Column(Boolean, default=False, nullable=False)
    
    # Relationship
    specialist = relationship("Specialists", back_populates="specializations")

    # Table Constraints
    __table_args__ = (
        UniqueConstraint('specialist_id', 'specialization', name='uq_specialist_specializations'),
        CheckConstraint('years_of_experience_in_specialization >= 0', name='chk_specialization_experience_positive'),
        Index('idx_specializations_specialist', 'specialist_id'),
        Index('idx_specializations_type', 'specialization'),
        Index('idx_specializations_primary', 'is_primary_specialization'),
        {'extend_existing': True}
    )
    
    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    @validates('years_of_experience_in_specialization')
    def validate_specialization_experience(self, key, experience):
        if experience is not None and experience < 0:
            raise ValueError("Years of experience in specialization cannot be negative")
        return experience or 0

    def __repr__(self) -> str:
        return f"<Specialization({self.specialist_id}, {self.specialization.value})>"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_specialist_by_email(db_session, email: str) -> Optional[Specialists]:
    """Get specialist by email address"""
    return db_session.query(Specialists).filter(
        Specialists.email == email.lower(),
        Specialists.is_deleted == False
    ).first()

def get_approved_specialists(db_session, limit: int = None) -> List[Specialists]:
    """Get all approved and verified specialists"""
    query = db_session.query(Specialists).join(
        SpecialistsAuthInfo
    ).filter(
        Specialists.approval_status == ApprovalStatusEnum.APPROVED,
        SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED,
        Specialists.is_deleted == False
    )
    
    if limit:
        query = query.limit(limit)
    
    return query.all()

def search_specialists_by_criteria(
    db_session,
    city: Optional[str] = None,
    specialist_type: Optional[SpecialistTypeEnum] = None,
    specialization: Optional[SpecializationEnum] = None,
    min_rating: Optional[float] = None,
    accepting_patients: bool = True
) -> List[Specialists]:
    """Search specialists by multiple criteria"""
    query = db_session.query(Specialists).join(
        SpecialistsAuthInfo
    ).filter(
        Specialists.approval_status == ApprovalStatusEnum.APPROVED,
        SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED,
        Specialists.is_deleted == False
    )
    
    if accepting_patients:
        query = query.filter(
            Specialists.availability_status == AvailabilityStatusEnum.ACCEPTING_NEW_PATIENTS
        )
    
    if city:
        query = query.filter(Specialists.city.ilike(f"%{city}%"))
    
    if specialist_type:
        query = query.filter(Specialists.specialist_type == specialist_type)
    
    if min_rating:
        query = query.filter(Specialists.average_rating >= min_rating)
    
    if specialization:
        query = query.join(SpecialistSpecializations).filter(
            SpecialistSpecializations.specialization == specialization
        )
    
    return query.all()

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "SpecialistTypeEnum",
    "SpecializationEnum",
    "AvailabilityStatusEnum", 
    "ApprovalStatusEnum",
    "EmailVerificationStatusEnum",
    "DocumentTypeEnum",
    "DocumentStatusEnum",
    
    # Models
    "Specialists",
    "SpecialistsAuthInfo",
    "SpecialistsApprovalData", 
    "SpecialistDocuments",
    "SpecialistSpecializations",
    
    # Utility Functions
    "get_specialist_by_email",
    "get_approved_specialists",
    "search_specialists_by_criteria",
]
"""
Patient Registration Router - Simplified with Email-based Operations
===================================================================

Author: Mental Health Platform Team
Version: 4.0.0 - Updated to use Patient Models and Email-based operations
"""

from datetime import datetime, date, timezone
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import BaseModel, Field, ValidationError, field_validator
import logging
import uuid
import re
import bcrypt

# Import database and models
from database.database import get_db
from models.sql_models.patient_models import (
    Patient, PatientAuthInfo, PatientPreferences,
    GenderEnum, RecordStatusEnum, LanguageEnum,
    ConsultationModeEnum, UrgencyLevelEnum, USERTYPE
)

# Import Pydantic models
from models.pydantic_models.patient_pydantic_models import (
    BasePatientModel, PatientCreateRequest, PatientResponse
)

# Import email utilities
from utils.email_utils import send_verification_email, generate_otp, get_otp_expiry

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/auth/register", tags=["Patient Registration"])

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_error_response(status_code: int, message: str) -> HTTPException:
    """Create standardized error response"""
    return HTTPException(status_code=status_code, detail=message)

def validate_email_format(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def get_patient_by_email(db: Session, email: str) -> Optional[Patient]:
    """Get patient by email"""
    return db.query(Patient).filter(
        Patient.email == email.lower(),
        Patient.is_deleted == False
    ).first()

def is_otp_valid(auth_info: PatientAuthInfo, otp: str) -> bool:
    """Check if OTP is valid and not expired"""
    if not auth_info.otp or not auth_info.otp_expiry:
        return False
    
    if auth_info.otp != otp:
        return False
    
    if datetime.now(timezone.utc) > auth_info.otp_expiry:
        return False
    
    return True

# ============================================================================
# PYDANTIC MODELS FOR REGISTRATION
# ============================================================================

class MinimalPatientRegistrationRequest(BasePatientModel):
    """Minimal patient registration request model"""
    
    # Basic Personal Information (Required)
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    
    # Demographics (Required)
    date_of_birth: date = Field(..., description="Date of birth")
    gender: GenderEnum = Field(..., description="Gender identity")
    
    # Contact Information (Required)
    email: str = Field(..., description="Email address")
    
    # Authentication (Required)
    password: str = Field(..., min_length=8, description="Password")
    
    # Legal Agreement (Required)
    accepts_terms_and_conditions: bool = Field(..., description="Accept terms and conditions")
    
    @field_validator('accepts_terms_and_conditions')
    @classmethod
    def validate_terms_acceptance(cls, v: bool) -> bool:
        if not v:
            raise ValueError('You must accept the terms and conditions to register')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        if not validate_email_format(v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "email": "john.doe@gmail.com",
                "password": "SecurePass123#",
                "accepts_terms_and_conditions": True
            }
        }


class RegistrationResponse(BasePatientModel):
    """Registration response model"""
    success: bool
    message: str
    email: str
    verification_required: bool
    next_steps: List[str]


class EmailVerificationRequest(BasePatientModel):
    """Email verification request model"""
    email: str = Field(..., description="Email address")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not validate_email_format(v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('otp')
    @classmethod
    def validate_otp_format(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('OTP must contain only digits')
        if len(v) != 6:
            raise ValueError('OTP must be exactly 6 digits')
        return v


class EmailVerificationResponse(BasePatientModel):
    """Email verification response model"""
    success: bool
    message: str
    email: str
    account_status: str
    next_steps: List[str]


class ResendOTPRequest(BasePatientModel):
    """Resend OTP request model"""
    email: str = Field(..., description="Email address")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not validate_email_format(v):
            raise ValueError('Invalid email format')
        return v.lower().strip()


class ResendOTPResponse(BasePatientModel):
    """Resend OTP response model"""
    success: bool
    message: str
    email: str
    retry_after_minutes: int = 1


class RegistrationStatusResponse(BasePatientModel):
    """Registration status response model"""
    email: str
    is_verified: bool
    is_active: bool
    registration_date: datetime
    verification_status: str
    account_status: str
    next_steps: List[str]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_complete_patient_record(
    db: Session,
    registration_data: MinimalPatientRegistrationRequest,
    hashed_password: str
) -> Patient:
    """Create complete patient record with auth info and default preferences"""
    
    # Create core patient record
    patient = Patient(
        user_type=USERTYPE.PATIENT,
        first_name=registration_data.first_name.strip(),
        last_name=registration_data.last_name.strip(),
        email=registration_data.email.lower().strip(),
        date_of_birth=registration_data.date_of_birth,
        gender=registration_data.gender,
        primary_language=LanguageEnum.URDU,
        country="Pakistan",
        record_status=RecordStatusEnum.ACTIVE,
        accepts_terms_and_conditions=registration_data.accepts_terms_and_conditions
    )
    
    db.add(patient)
    db.flush()  # Get the patient ID
    
    # Create auth info
    otp = generate_otp()
    otp_expiry = get_otp_expiry()
    
    auth_info = PatientAuthInfo(
        patient_id=patient.id,
        hashed_password=hashed_password,
        is_active=False,  # Inactive until verified
        is_verified=False,
        otp=otp,
        otp_expiry=otp_expiry,
        theme_preference="light",
        max_concurrent_sessions=3
    )
    
    db.add(auth_info)
    
    # Create default preferences
    default_preferences = PatientPreferences(
        patient_id=patient.id,
        consultation_mode=ConsultationModeEnum.VIRTUAL,
        urgency_level=UrgencyLevelEnum.STANDARD,
        max_budget=5000.0,
        notes="Default preferences created during registration",
        is_active=True
    )
    
    db.add(default_preferences)
    
    return patient

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/patient", response_model=RegistrationResponse)
async def register_patient(
    registration_data: MinimalPatientRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new patient with minimal required information
    
    Creates patient account with default preferences and sends verification email.
    """
    
    try:
        logger.info(f"Patient registration attempt: {registration_data.email}")
        
        email = registration_data.email.lower().strip()
        
        # Check for existing account
        existing_patient = get_patient_by_email(db, email)
        if existing_patient:
            if existing_patient.auth_info and existing_patient.auth_info.is_verified:
                raise create_error_response(
                    status.HTTP_409_CONFLICT,
                    "An account with this email already exists"
                )
            else:
                # Update existing unverified account
                logger.info(f"Updating existing unverified account: {email}")
                
                # Update basic information
                existing_patient.first_name = registration_data.first_name.strip()
                existing_patient.last_name = registration_data.last_name.strip()
                existing_patient.date_of_birth = registration_data.date_of_birth
                existing_patient.gender = registration_data.gender
                existing_patient.accepts_terms_and_conditions = registration_data.accepts_terms_and_conditions
                existing_patient.updated_at = datetime.now(timezone.utc)
                
                # Update authentication info
                if existing_patient.auth_info:
                    existing_patient.auth_info.hashed_password = get_password_hash(registration_data.password)
                    existing_patient.auth_info.otp = generate_otp()
                    existing_patient.auth_info.otp_expiry = get_otp_expiry()
                    existing_patient.auth_info.updated_at = datetime.now(timezone.utc)
                
                db.commit()
                
                # Send verification email
                if existing_patient.auth_info:
                    background_tasks.add_task(
                        send_verification_email,
                        email,
                        existing_patient.auth_info.otp
                    )
                
                return RegistrationResponse(
                    success=True,
                    message="Account updated successfully! Please check your email for verification.",
                    email=email,
                    verification_required=True,
                    next_steps=[
                        "Check your email for the verification code",
                        "Verify your email using the code provided",
                        "Complete your profile setup when ready"
                    ]
                )
        
        # Create new patient account
        try:
            hashed_password = get_password_hash(registration_data.password)
            patient = create_complete_patient_record(db, registration_data, hashed_password)
            
            db.commit()
            db.refresh(patient)
            
            logger.info(f"Patient created successfully: {patient.id}")
            
        except IntegrityError as e:
            logger.error(f"Database integrity error: {e}")
            db.rollback()
            if "email" in str(e).lower():
                raise create_error_response(
                    status.HTTP_409_CONFLICT,
                    "An account with this email already exists"
                )
            else:
                raise create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Registration failed due to data conflict"
                )
        
        except SQLAlchemyError as e:
            logger.error(f"Database error during patient creation: {e}")
            db.rollback()
            raise create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Registration failed. Please try again."
            )
        
        # Send verification email
        try:
            if patient.auth_info:
                background_tasks.add_task(
                    send_verification_email,
                    email,
                    patient.auth_info.otp
                )
                logger.info(f"Verification email queued for: {email}")
        except Exception as e:
            logger.error(f"Failed to queue verification email: {e}")
        
        return RegistrationResponse(
            success=True,
            message="Registration successful! Please verify your email to continue.",
            email=email,
            verification_required=True,
            next_steps=[
                "Check your email for the verification code",
                "Verify your email to activate your account",
                "Complete your profile information when ready"
            ]
        )
    
    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise create_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Please check your information and try again"
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Registration failed. Please try again later."
        )


@router.post("/patient/verify-email", response_model=EmailVerificationResponse)
async def verify_patient_email(
    verification_data: EmailVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify patient email using OTP
    
    Activates the patient account after successful email verification.
    """
    
    try:
        logger.info(f"Email verification attempt for: {verification_data.email}")
        
        email = verification_data.email.lower().strip()
        
        # Get patient by email
        patient = get_patient_by_email(db, email)
        if not patient or not patient.auth_info:
            raise create_error_response(
                status.HTTP_404_NOT_FOUND,
                "Patient not found"
            )
        
        # Check if already verified
        if patient.auth_info.is_verified:
            return EmailVerificationResponse(
                success=True,
                message="Email is already verified",
                email=email,
                account_status="active",
                next_steps=[
                    "Your account is ready to use",
                    "Complete your profile when convenient"
                ]
            )
        
        # Validate OTP
        if not is_otp_valid(patient.auth_info, verification_data.otp):
            # Check if OTP is expired
            if (patient.auth_info.otp_expiry and 
                datetime.now(timezone.utc) > patient.auth_info.otp_expiry):
                raise create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Verification code has expired. Please request a new one."
                )
            else:
                raise create_error_response(
                    status.HTTP_400_BAD_REQUEST,
                    "Invalid verification code"
                )
        
        # Verify account
        try:
            patient.auth_info.is_verified = True
            patient.auth_info.is_active = True
            patient.auth_info.otp = None  # Clear OTP after successful verification
            patient.auth_info.otp_expiry = None
            patient.auth_info.updated_at = datetime.now(timezone.utc)
            
            # Update patient record
            patient.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            
            logger.info(f"Patient email verified successfully: {patient.id}")
            
            return EmailVerificationResponse(
                success=True,
                message="Email verified successfully! Your account is now active.",
                email=email,
                account_status="active",
                next_steps=[
                    "Your account is ready to use",
                    "Complete your profile information",
                    "Browse available mental health specialists"
                ]
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error during email verification: {e}")
            db.rollback()
            raise create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Verification failed. Please try again."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during email verification: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Verification failed. Please try again later."
        )


@router.post("/patient/resend-otp", response_model=ResendOTPResponse)
async def resend_verification_otp(
    resend_data: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Resend OTP for email verification
    
    Generates a new OTP and sends it to the patient's email address.
    """
    
    try:
        logger.info(f"OTP resend request for email: {resend_data.email}")
        
        email = resend_data.email.lower().strip()
        
        # Get patient
        patient = get_patient_by_email(db, email)
        if not patient or not patient.auth_info:
            # Don't reveal if email exists or not for security
            return ResendOTPResponse(
                success=True,
                message="If an account with this email exists, a new verification code has been sent.",
                email=email,
                retry_after_minutes=1
            )
        
        # Check if already verified
        if patient.auth_info.is_verified:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "Email is already verified"
            )
        
        # Generate new OTP
        try:
            patient.auth_info.otp = generate_otp()
            patient.auth_info.otp_expiry = get_otp_expiry()
            patient.auth_info.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            
            # Send verification email
            background_tasks.add_task(
                send_verification_email,
                email,
                patient.auth_info.otp
            )
            
            logger.info(f"New OTP generated and queued for: {email}")
            
            return ResendOTPResponse(
                success=True,
                message="A new verification code has been sent to your email.",
                email=email,
                retry_after_minutes=1
            )
            
        except SQLAlchemyError as e:
            logger.error(f"Database error during OTP resend: {e}")
            db.rollback()
            raise create_error_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                "Failed to resend verification code. Please try again."
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during OTP resend: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to resend verification code. Please try again later."
        )


@router.get("/patient/status", response_model=RegistrationStatusResponse)
async def get_patient_registration_status(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Get patient registration and verification status by email
    
    Returns current status of patient account registration and verification.
    """
    
    try:
        email = email.lower().strip()
        
        # Get patient
        patient = get_patient_by_email(db, email)
        if not patient or not patient.auth_info:
            raise create_error_response(
                status.HTTP_404_NOT_FOUND,
                "Patient not found"
            )
        
        # Determine next steps based on status
        next_steps = []
        if not patient.auth_info.is_verified:
            next_steps = [
                "Check your email for the verification code",
                "Verify your email to activate your account"
            ]
        elif patient.auth_info.is_verified and patient.auth_info.is_active:
            next_steps = [
                "Complete your profile information when convenient",
                "Browse available specialists",
                "Schedule your first consultation"
            ]
        
        return RegistrationStatusResponse(
            email=patient.email,
            is_verified=patient.auth_info.is_verified,
            is_active=patient.auth_info.is_active,
            registration_date=patient.created_at,
            verification_status="verified" if patient.auth_info.is_verified else "pending",
            account_status="active" if patient.auth_info.is_active else "inactive",
            next_steps=next_steps
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient status: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Unable to retrieve patient status"
        )


# ============================================================================
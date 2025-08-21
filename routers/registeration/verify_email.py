"""
Email Verification Endpoint for MindMate
=======================================
Handles email verification for patients, specialists, and admins
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional

# Import database models
from models.sql_models.patient_models import Patient, PatientAuthInfo
from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, EmailVerificationStatusEnum
)
from models.sql_models.admin_models import Admin
from models.sql_models.base_model import USERTYPE

# Import utilities
from utils.email_utils import is_otp_valid
from database.database import get_db

# Import the helper functions from register.py
from .register import (
    complete_patient_registration_after_verification,
    complete_specialist_registration_after_verification
)

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class VerifyUserRequest(BaseModel):
    email: EmailStr
    otp: str
    usertype: str  # "patient", "specialist", or "admin"
    
    class Config:
        str_strip_whitespace = True
        
    def __init__(self, **data):
        # Normalize usertype to lowercase
        if 'usertype' in data:
            data['usertype'] = data['usertype'].lower().strip()
        super().__init__(**data)

class VerifyUserResponse(BaseModel):
    success: bool
    message: str
    user_id: str
    email: str
    usertype: str
    verification_completed_at: datetime
    next_steps: list[str]

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

# ============================================================================
# VERIFICATION ROUTER
# ============================================================================

router = APIRouter(prefix="/auth", tags=["Email Verification"])

@router.post(
    "/verify-email",
    response_model=VerifyUserResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid OTP or user not found"},
        410: {"model": ErrorResponse, "description": "OTP expired"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def verify_user(
    request: VerifyUserRequest,
    db: Session = Depends(get_db)
):
    """
    Verify user email with OTP for patients, specialists, and admins
    Completes the registration process after successful verification
    """
    try:
        email = request.email.lower()
        otp = request.otp.strip()
        usertype = request.usertype
        
        # Validate usertype
        if usertype not in ["patient", "specialist", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid usertype. Must be 'patient', 'specialist', or 'admin'"
            )
        
        # Route to appropriate verification function
        if usertype == "patient":
            return await verify_patient_email(db, email, otp)
        elif usertype == "specialist":
            return await verify_specialist_email(db, email, otp)
        elif usertype == "admin":
            return await verify_admin_email(db, email, otp)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}"
        )

# ============================================================================
# PATIENT EMAIL VERIFICATION
# ============================================================================

async def verify_patient_email(db: Session, email: str, otp: str) -> VerifyUserResponse:
    """Verify patient email with OTP"""
    try:
        # Find patient by email
        patient = db.query(Patient).filter(
            Patient.email == email,
            Patient.is_deleted == False
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient not found with this email address"
            )
        
        # Get authentication info
        auth_info = db.query(PatientAuthInfo).filter(
            PatientAuthInfo.patient_id == patient.id
        ).first()
        
        if not auth_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication information not found"
            )
        
        # Check if already verified
        if auth_info.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified"
            )
        
        # Validate OTP
        if not auth_info.otp or auth_info.otp != otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        # Check OTP expiry
        if not is_otp_valid(auth_info.otp_expiry):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Verification code has expired. Please request a new one"
            )
        
        # Mark as verified and active
        auth_info.is_verified = True
        auth_info.is_active = True  # Activate account after verification
        auth_info.otp = None  # Clear OTP after successful verification
        auth_info.otp_expiry = None
        auth_info.verified_at = datetime.utcnow()
        
        db.commit()
        
        # Complete registration (send completion email)
        complete_patient_registration_after_verification(db, patient)
        
        return VerifyUserResponse(
            success=True,
            message="Email verified successfully! Your patient account is now active.",
            user_id=str(patient.id),
            email=patient.email,
            usertype="patient",
            verification_completed_at=auth_info.verified_at,
            next_steps=[
                "Login to your account",
                "Complete your profile information",
                "Set up your preferences",
                "Start searching for mental health specialists",
                "Book your first consultation"
            ]
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Patient verification failed: {str(e)}"
        )

# ============================================================================
# SPECIALIST EMAIL VERIFICATION
# ============================================================================

async def verify_specialist_email(db: Session, email: str, otp: str) -> VerifyUserResponse:
    """Verify specialist email with OTP"""
    try:
        # Find specialist by email
        specialist = db.query(Specialists).filter(
            Specialists.email == email,
            Specialists.is_deleted == False
        ).first()
        
        if not specialist:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specialist not found with this email address"
            )
        
        # Get authentication info
        auth_info = db.query(SpecialistsAuthInfo).filter(
            SpecialistsAuthInfo.specialist_id == specialist.id
        ).first()
        
        if not auth_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authentication information not found"
            )
        
        # Check if already verified
        if auth_info.email_verification_status == EmailVerificationStatusEnum.VERIFIED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified"
            )
        
        # Validate OTP
        print(f"DEBUG: Stored OTP: '{auth_info.otp_code}', Received OTP: '{otp}'")
        print(f"DEBUG: OTP types - Stored: {type(auth_info.otp_code)}, Received: {type(otp)}")
        
        if not auth_info.otp_code or str(auth_info.otp_code).strip() != str(otp).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        # Check OTP expiry
        if not is_otp_valid(auth_info.otp_expires_at):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Verification code has expired. Please request a new one"
            )
        
        # Mark as verified
        auth_info.email_verification_status = EmailVerificationStatusEnum.VERIFIED
        auth_info.otp_code = None  # Clear OTP after successful verification
        auth_info.otp_expires_at = None
        auth_info.email_verified_at = datetime.utcnow()
        
        db.commit()
        
        # Complete registration (send completion email and notify admins)
        complete_specialist_registration_after_verification(db, specialist)
        
        return VerifyUserResponse(
            success=True,
            message="Email verified successfully! Your specialist account is now pending admin approval.",
            user_id=str(specialist.id),
            email=specialist.email,
            usertype="specialist",
            verification_completed_at=auth_info.email_verified_at,
            next_steps=[
                "Upload required documents for verification",
                "Wait for admin approval (typically 2-3 business days)",
                "You will receive an email notification once approved",
                "Complete your profile setup after approval",
                "Start accepting patient consultations"
            ]
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Specialist verification failed: {str(e)}"
        )

# ============================================================================
# ADMIN EMAIL VERIFICATION (if needed)
# ============================================================================

async def verify_admin_email(db: Session, email: str, otp: str) -> VerifyUserResponse:
    """Verify admin email with OTP (if admin verification is implemented)"""
    # Note: Current admin creation doesn't use email verification
    # This is a placeholder for future admin verification implementation
    
    admin = db.query(Admin).filter(
        Admin.email == email,
        Admin.is_deleted == False
    ).first()
    
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin not found with this email address"
        )
    
    # For now, admins are directly activated
    # This would need to be implemented if admin email verification is required
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Admin email verification is not currently implemented"
    )

# ============================================================================
# RESEND OTP ENDPOINT (BONUS)
# ============================================================================

class ResendOTPRequest(BaseModel):
    email: EmailStr
    usertype: str
    
    def __init__(self, **data):
        if 'usertype' in data:
            data['usertype'] = data['usertype'].lower().strip()
        super().__init__(**data)

class ResendOTPResponse(BaseModel):
    success: bool
    message: str
    email: str
    usertype: str

@router.post(
    "/resend-otp",
    response_model=ResendOTPResponse,
    responses={
        400: {"model": ErrorResponse, "description": "User not found or already verified"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def resend_otp(
    request: ResendOTPRequest,
    db: Session = Depends(get_db)
):
    """Resend OTP for email verification"""
    try:
        from utils.email_utils import generate_otp, get_otp_expiry, send_verification_email
        from models.sql_models.base_model import USERTYPE
        
        email = request.email.lower()
        usertype = request.usertype
        
        if usertype not in ["patient", "specialist"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid usertype. Must be 'patient' or 'specialist'"
            )
        
        if usertype == "patient":
            # Find unverified patient
            patient = db.query(Patient).filter(
                Patient.email == email,
                Patient.is_deleted == False
            ).first()
            
            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patient not found"
                )
            
            auth_info = db.query(PatientAuthInfo).filter(
                PatientAuthInfo.patient_id == patient.id,
                PatientAuthInfo.is_verified == False
            ).first()
            
            if not auth_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patient is already verified or not found"
                )
            
            # Generate new OTP
            new_otp = generate_otp()
            new_expiry = get_otp_expiry()
            
            auth_info.otp = new_otp
            auth_info.otp_expiry = new_expiry
            
            first_name = patient.first_name
            user_type_enum = USERTYPE.PATIENT
            
        elif usertype == "specialist":
            # Find unverified specialist
            specialist = db.query(Specialists).filter(
                Specialists.email == email,
                Specialists.is_deleted == False
            ).first()
            
            if not specialist:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Specialist not found"
                )
            
            auth_info = db.query(SpecialistsAuthInfo).filter(
                SpecialistsAuthInfo.specialist_id == specialist.id,
                SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.PENDING
            ).first()
            
            if not auth_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Specialist is already verified or not found"
                )
            
            # Generate new OTP
            new_otp = generate_otp()
            new_expiry = get_otp_expiry()
            
            auth_info.otp_code = new_otp
            auth_info.otp_expires_at = new_expiry
            
            first_name = specialist.first_name
            user_type_enum = USERTYPE.SPECIALIST
        
        db.commit()
        
        # Send new OTP email
        email_sent = send_verification_email(email, new_otp, user_type_enum, first_name)
        
        if not email_sent:
            print(f"Warning: Failed to send OTP email to {email}")
        
        return ResendOTPResponse(
            success=True,
            message="New verification code sent to your email",
            email=email,
            usertype=usertype
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend OTP: {str(e)}"
        )

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "router",
    "verify_user",
    "resend_otp",
    "VerifyUserRequest",
    "VerifyUserResponse",
    "ResendOTPRequest", 
    "ResendOTPResponse"
]
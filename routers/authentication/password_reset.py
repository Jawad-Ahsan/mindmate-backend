"""
Password Reset Router - Complete Password Reset System
====================================================

Author: Mental Health Platform Team  
Version: 1.0.0 - Secure password reset with OTP verification
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
import logging
import re
import bcrypt
import secrets
import hashlib

from database.database import get_db
from models.sql_models.patient_models import Patient, PatientAuthInfo
from models.sql_models.specialist_models import Specialists, SpecialistsAuthInfo
from utils.email_utils import send_password_reset_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Password Reset"])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    user_type: str = Field(..., description="User type: patient, specialist, or admin")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v.lower()
    
    @field_validator('user_type')
    @classmethod
    def validate_user_type(cls, v):
        if v not in ['patient', 'specialist', 'admin']:
            raise ValueError('Invalid user type')
        return v

class PasswordResetResponse(BaseModel):
    success: bool
    message: str
    cooldown_until: Optional[datetime] = None

class ResendOTPRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    user_type: str = Field(..., description="User type")

class VerifyOTPRequest(BaseModel):
    email: str = Field(..., description="User's email address")
    user_type: str = Field(..., description="User type")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")

class VerifyOTPResponse(BaseModel):
    success: bool
    message: str
    reset_token: str
    expires_at: datetime

class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., description="Reset token from OTP verification")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirm new password")
    
    @field_validator('confirm_password')
    @classmethod
    def validate_password_match(cls, v, info):
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v

class ResetPasswordResponse(BaseModel):
    success: bool
    message: str
    changed_at: datetime

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_otp() -> str:
    """Generate cryptographically secure 6-digit OTP"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def hash_otp(otp: str) -> str:
    """Hash OTP for secure storage"""
    return hashlib.sha256(otp.encode()).hexdigest()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def get_user_by_email(db: Session, email: str, user_type: str):
    """Get user by email and type"""
    try:
        if user_type == 'patient':
            return db.query(Patient).filter(
                Patient.email == email.lower(),
                Patient.is_deleted == False
            ).first()
        elif user_type == 'specialist':
            return db.query(Specialists).filter(
                Specialists.email == email.lower(),
                Specialists.is_deleted == False
            ).first()
        elif user_type == 'admin':
            from models.sql_models.admin_models import Admin
            return db.query(Admin).filter(
                Admin.email == email.lower(),
                Admin.is_deleted == False
            ).first()
        return None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

def get_auth_info(db: Session, user, user_type: str):
    """Get authentication info for user"""
    try:
        if user_type == 'patient':
            return db.query(PatientAuthInfo).filter(
                PatientAuthInfo.patient_id == user.id
            ).first()
        elif user_type == 'specialist':
            return db.query(SpecialistsAuthInfo).filter(
                SpecialistsAuthInfo.specialist_id == user.id
            ).first()
        elif user_type == 'admin':
            return user
        return None
    except Exception as e:
        logger.error(f"Error getting auth info: {e}")
        return None

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/request-password-reset", response_model=PasswordResetResponse)
async def request_password_reset(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset - sends OTP via email"""
    
    try:
        logger.info(f"Password reset request for {request.email} ({request.user_type})")
        
        # Get user and auth info
        user = get_user_by_email(db, request.email, request.user_type)
        if not user:
            return PasswordResetResponse(
                success=True,
                message="If an account with this email exists, you will receive password reset instructions."
            )
        
        auth_info = get_auth_info(db, user, request.user_type)
        if not auth_info:
            return PasswordResetResponse(
                success=True,
                message="If an account with this email exists, you will receive password reset instructions."
            )
        
        # Generate OTP and set expiry
        otp = generate_otp()
        otp_hash = hash_otp(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Update auth info
        auth_info.password_reset_token = otp_hash
        auth_info.password_reset_expires = expires_at
        
        db.commit()
        
        # Send email in background
        user_name = getattr(user, 'first_name', None) or getattr(user, 'full_name', None)
        background_tasks.add_task(
            send_password_reset_email,
            request.email,
            otp,
            user_name
        )
        
        logger.info(f"Password reset OTP sent to {request.email}")
        
        return PasswordResetResponse(
            success=True,
            message="If an account with this email exists, you will receive password reset instructions."
        )
        
    except Exception as e:
        logger.error(f"Error in password reset request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process password reset request. Please try again later."
        )

@router.post("/resend-reset-otp", response_model=PasswordResetResponse)
async def resend_reset_otp(
    request: ResendOTPRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Resend password reset OTP"""
    
    try:
        logger.info(f"OTP resend request for {request.email} ({request.user_type})")
        
        # Get user and auth info
        user = get_user_by_email(db, request.email, request.user_type)
        if not user:
            return PasswordResetResponse(
                success=False,
                message="Account not found."
            )
        
        auth_info = get_auth_info(db, user, request.user_type)
        if not auth_info:
            return PasswordResetResponse(
                success=False,
                message="Authentication information not found."
            )
        
        # Check if OTP was requested
        if not auth_info.password_reset_token or not auth_info.password_reset_expires:
            return PasswordResetResponse(
                success=False,
                message="No password reset request found. Please request a password reset first."
            )
        
        # Check if OTP expired
        if datetime.now(timezone.utc) >= auth_info.password_reset_expires:
            return PasswordResetResponse(
                success=False,
                message="Password reset request has expired. Please request a new one."
            )
        
        # Generate new OTP
        otp = generate_otp()
        otp_hash = hash_otp(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Update auth info
        auth_info.password_reset_token = otp_hash
        auth_info.password_reset_expires = expires_at
        
        db.commit()
        
        # Send email in background
        user_name = getattr(user, 'first_name', None) or getattr(user, 'full_name', None)
        background_tasks.add_task(
            send_password_reset_email,
            request.email,
            otp,
            user_name
        )
        
        logger.info(f"Password reset OTP resent to {request.email}")
        
        return PasswordResetResponse(
            success=True,
            message="A new OTP has been sent to your email."
        )
        
    except Exception as e:
        logger.error(f"Error in OTP resend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend OTP. Please try again later."
        )

@router.post("/verify-reset-otp", response_model=VerifyOTPResponse)
async def verify_reset_otp(
    request: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """Verify password reset OTP and generate reset token"""
    
    try:
        logger.info(f"OTP verification for {request.email} ({request.user_type})")
        
        # Get user and auth info
        user = get_user_by_email(db, request.email, request.user_type)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found."
            )
        
        auth_info = get_auth_info(db, user, request.user_type)
        if not auth_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Authentication information not found."
            )
        
        # Check if OTP was requested
        if not auth_info.password_reset_token or not auth_info.password_reset_expires:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No password reset request found. Please request a password reset first."
            )
        
        # Check if OTP expired
        if datetime.now(timezone.utc) >= auth_info.password_reset_expires:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Password reset request has expired. Please request a new one."
            )
        
        # Verify OTP
        otp_hash = hash_otp(request.otp)
        if auth_info.password_reset_token != otp_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP. Please check and try again."
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        token_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        # Store reset token
        auth_info.password_reset_token = reset_token
        auth_info.password_reset_expires = token_expires
        
        db.commit()
        
        logger.info(f"OTP verified successfully for {request.email}")
        
        return VerifyOTPResponse(
            success=True,
            message="OTP verified successfully. You can now reset your password.",
            reset_token=reset_token,
            expires_at=token_expires
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OTP verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP. Please try again later."
        )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    
    try:
        logger.info("Password reset request received")
        
        # Find user with this reset token
        user = None
        auth_info = None
        user_type = None
        
        # Search in patient auth info
        auth_info = db.query(PatientAuthInfo).filter(
            PatientAuthInfo.password_reset_token == request.reset_token
        ).first()
        if auth_info:
            user = db.query(Patient).filter(Patient.id == auth_info.patient_id).first()
            user_type = 'patient'
        
        if not user:
            # Search in specialist auth info
            auth_info = db.query(SpecialistsAuthInfo).filter(
                SpecialistsAuthInfo.password_reset_token == request.reset_token
            ).first()
            if auth_info:
                user = db.query(Specialists).filter(Specialists.id == auth_info.specialist_id).first()
                user_type = 'specialist'
        
        if not user:
            # Search in admin table
            from models.sql_models.admin_models import Admin
            user = db.query(Admin).filter(
                Admin.password_reset_token == request.reset_token
            ).first()
            if user:
                auth_info = user
                user_type = 'admin'
        
        if not user or not auth_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token."
            )
        
        # Check if token expired
        if not auth_info.password_reset_expires or datetime.now(timezone.utc) >= auth_info.password_reset_expires:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Reset token has expired. Please request a new password reset."
            )
        
        # Hash new password
        new_hashed_password = hash_password(request.new_password)
        
        # Update password
        if user_type == 'admin':
            auth_info.hashed_password = new_hashed_password
        else:
            auth_info.hashed_password = new_hashed_password
        
        # Clear all reset-related fields
        auth_info.password_reset_token = None
        auth_info.password_reset_expires = None
        
        # Set password change timestamp
        if hasattr(auth_info, 'password_changed_at'):
            auth_info.password_changed_at = datetime.now(timezone.utc)
        if hasattr(auth_info, 'updated_at'):
            auth_info.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"Password reset successfully for {user.email}")
        
        return ResetPasswordResponse(
            success=True,
            message="Password reset successfully. You can now log in with your new password.",
            changed_at=datetime.now(timezone.utc)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again later."
        )

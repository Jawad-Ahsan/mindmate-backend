
"""
Patient Login Router - Complete Authentication System
===================================================

Author: Mental Health Platform Team  
Version: 4.0.0 - Email-based authentication with secret code management
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, ValidationError, field_validator
import logging
import uuid
import re
import bcrypt
import jwt
from secrets import token_urlsafe
import hashlib

# Import database and models
from database.database import get_db
from models.sql_models.patient_models import (
    Patient, PatientAuthInfo, GenderEnum, RecordStatusEnum, 
    LanguageEnum, ConsultationModeEnum, UrgencyLevelEnum, USERTYPE
)

# Import Pydantic models
from models.pydantic_models.patient_pydantic_models import (
    BasePatientModel, PatientResponse
)

# Import email utilities
from utils.email_utils import send_login_notification_email, send_secret_code_email, generate_otp, get_otp_expiry

# Import configuration
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/auth/", tags=["Patient Authentication"])
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS or 7


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

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def get_patient_by_email(db: Session, email: str) -> Optional[Patient]:
    """Get patient by email"""
    return db.query(Patient).filter(
        Patient.email == email.lower(),
        Patient.is_deleted == False
    ).first()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

def generate_secret_code() -> str:
    """Generate a 6-digit secret code"""
    return generate_otp()

def hash_secret_code(code: str) -> str:
    """Hash secret code for storage"""
    return hashlib.sha256(code.encode()).hexdigest()

def is_account_locked(auth_info: PatientAuthInfo) -> bool:
    """Check if account is locked"""
    if auth_info.is_locked:
        return True
    
    if auth_info.locked_until and auth_info.locked_until > datetime.now(timezone.utc):
        return True
        
    return False

def increment_failed_attempts(db: Session, auth_info: PatientAuthInfo):
    """Increment failed login attempts and lock if necessary"""
    auth_info.failed_login_attempts += 1
    auth_info.updated_at = datetime.now(timezone.utc)
    
    # Lock account after 5 failed attempts
    if auth_info.failed_login_attempts >= 5:
        auth_info.is_locked = True
        auth_info.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)
        logger.warning(f"Account locked for patient: {auth_info.patient.email}")
    
    db.commit()

def reset_failed_attempts(db: Session, auth_info: PatientAuthInfo):
    """Reset failed login attempts after successful login"""
    auth_info.failed_login_attempts = 0
    auth_info.is_locked = False
    auth_info.locked_until = None
    auth_info.last_login = datetime.now(timezone.utc)
    auth_info.updated_at = datetime.now(timezone.utc)
    db.commit()


@router.post("/verify-account-access")
async def verify_account_access(
    email: str = Field(..., description="Email address"),
    secret_code: str = Field(..., min_length=6, max_length=6, description="Secret code"),
    db: Session = Depends(get_db)
):
    """
    Verify account access using email and secret code
    
    Alternative verification method for account recovery or sensitive operations.
    """
    
    try:
        logger.info(f"Account access verification for email: {email}")
        
        # Get patient by email
        patient = get_patient_by_email(db, email.lower().strip())
        if not patient or not patient.auth_info:
            raise create_error_response(
                status.HTTP_404_NOT_FOUND,
                "Account not found"
            )
        
        auth_info = patient.auth_info
        
        # Check if secret code is set
        if not auth_info.two_factor_code:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "No secret code is set for this account"
            )
        
        # Verify secret code
        provided_code_hash = hash_secret_code(secret_code)
        if provided_code_hash != auth_info.two_factor_code:
            raise create_error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Invalid secret code"
            )
        
        return {
            "success": True,
            "message": "Account access verified successfully",
            "patient_id": str(patient.id),
            "email": patient.email,
            "verified_at": datetime.now(timezone.utc)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying account access: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Account verification failed. Please try again later."
        )

class SetSecretCodeRequest(BasePatientModel):
    """Set secret code request model"""
    secret_code: str = Field(..., min_length=6, max_length=6, description="6-digit secret code")
    
    @field_validator('secret_code')
    @classmethod
    def validate_secret_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('Secret code must contain only digits')
        if len(v) != 6:
            raise ValueError('Secret code must be exactly 6 digits')
        return v

class UpdateSecretCodeRequest(BasePatientModel):
    """Update secret code request model"""
    current_secret_code: str = Field(..., min_length=6, max_length=6, description="Current 6-digit secret code")
    new_secret_code: str = Field(..., min_length=6, max_length=6, description="New 6-digit secret code")
    
    @field_validator('current_secret_code', 'new_secret_code')
    @classmethod
    def validate_secret_codes(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('Secret code must contain only digits')
        if len(v) != 6:
            raise ValueError('Secret code must be exactly 6 digits')
        return v

class SecretCodeResponse(BasePatientModel):
    """Secret code response model"""
    success: bool
    message: str
    has_secret_code: bool = False
    secret_code_set_date: Optional[datetime] = None
    next_steps: List[str]

class ValidateSecretCodeRequest(BasePatientModel):
    """Validate secret code request model"""
    secret_code: str = Field(..., min_length=6, max_length=6, description="6-digit secret code")
    
    @field_validator('secret_code')
    @classmethod
    def validate_secret_code(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError('Secret code must contain only digits')
        if len(v) != 6:
            raise ValueError('Secret code must be exactly 6 digits')
        return v

class ValidateSecretCodeResponse(BasePatientModel):
    """Validate secret code response model"""
    success: bool
    message: str
    is_valid: bool
    verification_timestamp: Optional[datetime] = None



async def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Patient:
    """Get current authenticated patient from JWT token"""
    
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if not payload:
        raise create_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Could not validate credentials"
        )
    
    patient_id = payload.get("sub")
    if not patient_id:
        raise create_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid token payload"
        )
    
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise create_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid patient ID format"
        )
    
    patient = db.query(Patient).filter(
        Patient.id == patient_uuid,
        Patient.is_deleted == False
    ).first()
    
    if not patient or not patient.auth_info:
        raise create_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Patient not found"
        )
    
    if not patient.auth_info.is_active:
        raise create_error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Account is deactivated"
        )
    
    # Update last activity
    patient.auth_info.last_activity = datetime.now(timezone.utc)
    db.commit()
    
    return patient



@router.post("/set-secret-code", response_model=SecretCodeResponse)
async def set_secret_code(
    secret_code_data: SetSecretCodeRequest,
    background_tasks: BackgroundTasks,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Set secret code for additional account security
    
    Requires valid authentication. Sets a 6-digit secret code for the patient.
    """
    
    try:
        logger.info(f"Set secret code request for patient: {current_patient.id}")
        
        auth_info = current_patient.auth_info
        
        # Check if secret code is already set
        if auth_info.two_factor_code:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "Secret code is already set. Use update-secret-code to change it."
            )
        
        # Hash and store the secret code
        hashed_code = hash_secret_code(secret_code_data.secret_code)
        auth_info.two_factor_code = hashed_code
        auth_info.two_factor_enabled = True
        auth_info.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        # Send confirmation email
        try:
            background_tasks.add_task(
                send_secret_code_email,
                current_patient.email,
                current_patient.first_name,
                "set",
                datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to queue secret code email: {e}")
        
        logger.info(f"Secret code set successfully for patient: {current_patient.id}")
        
        return SecretCodeResponse(
            success=True,
            message="Secret code set successfully",
            has_secret_code=True,
            secret_code_set_date=datetime.now(timezone.utc),
            next_steps=[
                "Secret code has been set",
                "You can use it for additional verification when needed",
                "Remember to keep your secret code secure"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting secret code: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to set secret code. Please try again later."
        )


@router.put("/update-secret-code", response_model=SecretCodeResponse)
async def update_secret_code(
    update_data: UpdateSecretCodeRequest,
    background_tasks: BackgroundTasks,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Update existing secret code
    
    Requires valid authentication and current secret code for verification.
    """
    
    try:
        logger.info(f"Update secret code request for patient: {current_patient.id}")
        
        auth_info = current_patient.auth_info
        
        # Check if secret code exists
        if not auth_info.two_factor_code:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "No secret code is currently set. Use set-secret-code to create one."
            )
        
        # Verify current secret code
        current_code_hash = hash_secret_code(update_data.current_secret_code)
        if current_code_hash != auth_info.two_factor_code:
            raise create_error_response(
                status.HTTP_401_UNAUTHORIZED,
                "Current secret code is incorrect"
            )
        
        # Update to new secret code
        new_code_hash = hash_secret_code(update_data.new_secret_code)
        auth_info.two_factor_code = new_code_hash
        auth_info.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        # Send confirmation email
        try:
            background_tasks.add_task(
            send_secret_code_email,
            current_patient.email,
            current_patient.first_name,
            "update",
            datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to queue secret code email: {e}")
        
        logger.info(f"Secret code updated successfully for patient: {current_patient.id}")
        
        return SecretCodeResponse(
            success=True,
            message="Secret code updated successfully",
            has_secret_code=True,
            secret_code_set_date=datetime.now(timezone.utc),
            next_steps=[
                "Secret code has been updated",
                "Your new secret code is now active",
                "Remember to keep your new secret code secure"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating secret code: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to update secret code. Please try again later."
        )


@router.get("/get-secret-code-status", response_model=SecretCodeResponse)
async def get_secret_code_status(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Get secret code status for the authenticated patient
    
    Returns information about whether a secret code is set and when.
    """
    
    try:
        auth_info = current_patient.auth_info
        
        has_secret_code = bool(auth_info.two_factor_code)
        
        # Get the date when two-factor was enabled (use updated_at as proxy)
        secret_code_date = None
        if has_secret_code and auth_info.two_factor_enabled:
            secret_code_date = auth_info.updated_at
        
        next_steps = []
        if has_secret_code:
            next_steps = [
                "Secret code is already set",
                "You can update it if needed",
                "Use it for additional verification when required"
            ]
        else:
            next_steps = [
                "No secret code is currently set",
                "Consider setting up a secret code for additional security",
                "Use set-secret-code endpoint to create one"
            ]
        
        return SecretCodeResponse(
            success=True,
            message="Secret code status retrieved successfully",
            has_secret_code=has_secret_code,
            secret_code_set_date=secret_code_date,
            next_steps=next_steps
        )
        
    except Exception as e:
        logger.error(f"Error getting secret code status: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to get secret code status. Please try again later."
        )


@router.post("/validate-secret-code", response_model=ValidateSecretCodeResponse)
async def validate_secret_code(
    validation_data: ValidateSecretCodeRequest,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """
    Validate secret code for the authenticated patient
    
    Verifies the provided secret code against the stored hash.
    """
    
    try:
        logger.info(f"Secret code validation request for patient: {current_patient.id}")
        
        auth_info = current_patient.auth_info
        
        # Check if secret code is set
        if not auth_info.two_factor_code:
            raise create_error_response(
                status.HTTP_400_BAD_REQUEST,
                "No secret code is set for this account"
            )
        
        # Validate the secret code
        provided_code_hash = hash_secret_code(validation_data.secret_code)
        is_valid = provided_code_hash == auth_info.two_factor_code
        
        # Update last activity
        auth_info.last_activity = datetime.now(timezone.utc)
        db.commit()
        
        verification_timestamp = datetime.now(timezone.utc) if is_valid else None
        
        message = "Secret code is valid" if is_valid else "Secret code is invalid"
        
        logger.info(f"Secret code validation result for patient {current_patient.id}: {is_valid}")
        
        return ValidateSecretCodeResponse(
            success=True,
            message=message,
            is_valid=is_valid,
            verification_timestamp=verification_timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating secret code: {e}")
        raise create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Failed to validate secret code. Please try again later."
        )


# @router.post("/disable-secret-code")
# async def disable_secret_code(
#     current_secret_code: str = Field(..., min_length=6, max_length=6, description="Current secret code"),
#     password: str = Field(..., description="Account password for verification"),
#     current_patient: Patient = Depends(get_current_patient),
#     background_tasks: BackgroundTasks,
#     db: Session = Depends(get_db)
# ):
#     """
#     Disable secret code feature
    
#     Requires both secret code and password verification for security.
#     """
    
#     try:
#         logger.info(f"Disable secret code request for patient: {current_patient.id}")
        
#         auth_info = current_patient.auth_info
        
#         # Check if secret code exists
#         if not auth_info.two_factor_code:
#             raise create_error_response(
#                 status.HTTP_400_BAD_REQUEST,
#                 "No secret code is currently set"
#             )
        
#         # Verify current secret code
#         current_code_hash = hash_secret_code(current_secret_code)
#         if current_code_hash != auth_info.two_factor_code:
#             raise create_error_response(
#                 status.HTTP_401_UNAUTHORIZED,
#                 "Current secret code is incorrect"
#             )
        
#         # Verify password
#         if not auth_info.hashed_password or not verify_password(password, auth_info.hashed_password):
#             raise create_error_response(
#                 status.HTTP_401_UNAUTHORIZED,
#                 "Password is incorrect"
#             )
        
#         # Disable secret code
#         auth_info.two_factor_code = None
#         auth_info.two_factor_enabled = False
#         auth_info.two_factor_expires = None
#         auth_info.updated_at = datetime.now(timezone.utc)
        
#         db.commit()
        
#         # Send notification email
#         try:
#             background_tasks.add_task(
#                 send_secret_code_email,
#                 current_patient.email,
#                 current_patient.first_name,
#                 "disabled",
#                 datetime.now(timezone.utc)
#             )
#         except Exception as e:
#             logger.error(f"Failed to queue secret code disabled email: {e}")
        
#         logger.info(f"Secret code disabled successfully for patient: {current_patient.id}")
        
#         return {
#             "success": True,
#             "message": "Secret code has been disabled successfully",
#             "disabled_at": datetime.now(timezone.utc),
#             "next_steps": [
#                 "Secret code feature has been disabled",
#                 "You can re-enable it anytime using set-secret-code",
#                 "Your account is now using password-only authentication"
#             ]
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error disabling secret code: {e}")
#         raise create_error_response(
#             status.HTTP_500_INTERNAL_SERVER_ERROR,
#             "Failed to disable secret code. Please try again later."
#         )


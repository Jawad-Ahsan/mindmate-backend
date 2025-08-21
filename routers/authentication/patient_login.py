"""
Patient Authentication Router - Clean Implementation
==================================================

Author: Mental Health Platform Team  
Version: 4.1.0 - Simplified and clean authentication system
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
import logging
import uuid
import re
import bcrypt
import jwt  # Make sure you have PyJWT installed: pip install PyJWT
import hashlib

# Import your database and models (adjust imports as needed)
from database.database import get_db
from models.sql_models.patient_models import Patient, PatientAuthInfo
from models.pydantic_models.patient_pydantic_models import PatientResponse
from utils.email_utils import send_login_notification_email
from core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router and security
router = APIRouter(prefix="/auth", tags=["Patient Authentication"])
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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
    
    # Lock account after 5 failed attempts for 30 minutes
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

def get_client_ip(request: Request) -> str:
    """Get client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LoginRequest(BaseModel):
    """Patient login request model"""
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="Password")
    remember_me: bool = Field(False, description="Remember login for longer period")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not validate_email_format(v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

class LoginResponse(BaseModel):
    """Login response model"""
    success: bool
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    patient_info: Dict[str, Any]

class LogoutResponse(BaseModel):
    """Logout response model"""
    success: bool
    message: str
    logged_out_at: datetime

class TokenRefreshRequest(BaseModel):
    """Token refresh request model"""
    refresh_token: str = Field(..., description="Refresh token")

class TokenRefreshResponse(BaseModel):
    """Token refresh response model"""
    success: bool
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

class ChangePasswordResponse(BaseModel):
    """Change password response model"""
    success: bool
    message: str
    changed_at: datetime

# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

async def get_current_patient(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Patient:
    """Get current authenticated patient from JWT token"""
    
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    patient_id = payload.get("sub")
    if not patient_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    try:
        patient_uuid = uuid.UUID(patient_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid patient ID format"
        )
    
    patient = db.query(Patient).filter(
        Patient.id == patient_uuid,
        Patient.is_deleted == False
    ).first()
    
    if not patient or not patient.auth_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Patient not found"
        )
    
    if not patient.auth_info.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Update last activity
    patient.auth_info.last_activity = datetime.now(timezone.utc)
    db.commit()
    
    return patient

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/login", response_model=LoginResponse)
async def patient_login(
    login_data: LoginRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """Patient login with email and password"""
    
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        
        email = login_data.email.lower().strip()
        client_ip = get_client_ip(request)
        
        # Get patient by email
        patient = get_patient_by_email(db, email)
        if not patient or not patient.auth_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        auth_info = patient.auth_info
        
        # Check if account is verified
        if not auth_info.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Please verify your email before logging in"
            )
        
        # Check if account is locked
        if is_account_locked(auth_info):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to multiple failed attempts. Please try again later."
            )
        
        # Verify password
        if not auth_info.hashed_password or not verify_password(login_data.password, auth_info.hashed_password):
            increment_failed_attempts(db, auth_info)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Reset failed attempts on successful authentication
        reset_failed_attempts(db, auth_info)
        
        # Update login information
        auth_info.last_login_ip = client_ip
        auth_info.login_attempts += 1
        db.commit()
        
        # Create JWT tokens
        token_data = {
            "sub": str(patient.id),
            "email": patient.email,
            "user_type": "patient"
        }
        
        # Adjust token expiration if remember_me is enabled
        if login_data.remember_me:
            access_token_expires = timedelta(hours=24)
            expires_in = 24 * 60 * 60
        else:
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        access_token = create_access_token(token_data, access_token_expires)
        refresh_token = create_refresh_token(token_data)
        
        # Prepare patient info for response
        patient_info = {
            "id": str(patient.id),
            "email": patient.email,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "full_name": f"{patient.first_name} {patient.last_name}".strip(),
            "last_login": auth_info.last_login.isoformat() if auth_info.last_login else None
        }
        
        # Send login notification email in background
        try:
            background_tasks.add_task(
                send_login_notification_email,
                email,
                patient.first_name,
                client_ip,
                datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to queue login notification email: {e}")
        
        logger.info(f"Successful login for patient: {patient.id}")
        
        return LoginResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
            patient_info=patient_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )

@router.post("/refresh-token", response_model=TokenRefreshResponse)
async def refresh_access_token(
    refresh_data: TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        patient_id = payload.get("sub")
        email = payload.get("email")
        
        # Verify patient still exists and is active
        patient = db.query(Patient).filter(
            Patient.id == uuid.UUID(patient_id),
            Patient.email == email,
            Patient.is_deleted == False
        ).first()
        
        if not patient or not patient.auth_info or not patient.auth_info.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Patient not found or inactive"
            )
        
        # Create new access token
        token_data = {
            "sub": str(patient.id),
            "email": patient.email,
            "user_type": "patient"
        }
        
        access_token = create_access_token(token_data)
        expires_in = ACCESS_TOKEN_EXPIRE_MINUTES * 60
        
        return TokenRefreshResponse(
            success=True,
            access_token=access_token,
            expires_in=expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh token. Please login again."
        )

@router.post("/logout", response_model=LogoutResponse)
async def patient_logout(
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Logout patient"""
    
    try:
        logger.info(f"Logout request for patient: {current_patient.id}")
        
        # Update last activity
        auth_info = current_patient.auth_info
        logout_time = datetime.now(timezone.utc)
        auth_info.last_activity = logout_time
        auth_info.updated_at = logout_time
        
        db.commit()
        
        logger.info(f"Patient logged out successfully: {current_patient.id}")
        
        return LogoutResponse(
            success=True,
            message="Logged out successfully",
            logged_out_at=logout_time
        )
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )

@router.get("/me", response_model=PatientResponse)
async def get_current_patient_info(
    current_patient: Patient = Depends(get_current_patient)
):
    """Get current authenticated patient information"""
    
    try:
        # Convert Patient SQLAlchemy model to PatientResponse
        patient_data = {
            "id": str(current_patient.id),
            "user_type": current_patient.user_type,
            "first_name": current_patient.first_name,
            "last_name": current_patient.last_name,
            "email": current_patient.email,
            "phone": current_patient.phone,
            "date_of_birth": current_patient.date_of_birth,
            "gender": current_patient.gender,
            "primary_language": current_patient.primary_language,
            "city": current_patient.city,
            "district": current_patient.district,
            "province": current_patient.province,
            "country": current_patient.country,
            "record_status": current_patient.record_status,
            "accepts_terms_and_conditions": current_patient.accepts_terms_and_conditions,
            "created_at": current_patient.created_at,
            "updated_at": current_patient.updated_at
        }
        
        return PatientResponse(**patient_data)
        
    except Exception as e:
        logger.error(f"Error getting patient info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get patient information"
        )

@router.post("/change-password", response_model=ChangePasswordResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_patient: Patient = Depends(get_current_patient),
    db: Session = Depends(get_db)
):
    """Change patient password"""
    
    try:
        logger.info(f"Password change request for patient: {current_patient.id}")
        auth_info = current_patient.auth_info
        
        # Verify current password
        if not auth_info.hashed_password or not verify_password(request.current_password, auth_info.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        new_hashed_password = hash_password(request.new_password)
        
        # Update password
        auth_info.hashed_password = new_hashed_password
        auth_info.password_changed_at = datetime.now(timezone.utc)
        auth_info.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        
        logger.info(f"Password changed successfully for patient: {current_patient.id}")
        
        change_time = datetime.now(timezone.utc)
        return ChangePasswordResponse(
            success=True,
            message="Password changed successfully",
            changed_at=change_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password. Please try again later."
        )

@router.get("/session-status")
async def check_session_status(
    current_patient: Patient = Depends(get_current_patient)
):
    """Check current session status"""
    
    try:
        auth_info = current_patient.auth_info
        
        return {
            "authenticated": True,
            "patient_id": str(current_patient.id),
            "email": current_patient.email,
            "last_login": auth_info.last_login.isoformat() if auth_info.last_login else None,
            "last_activity": auth_info.last_activity.isoformat() if auth_info.last_activity else None,
            "is_verified": auth_info.is_verified,
            "session_valid": True
        }
        
    except Exception as e:
        logger.error(f"Error checking session status: {e}")
        return {
            "authenticated": False,
            "session_valid": False,
            "error": "Session check failed"
        }

@router.get("/health")
async def authentication_health_check():
    """Health check for authentication service"""
    
    return {
        "status": "healthy",
        "service": "patient-authentication",
        "timestamp": datetime.now(timezone.utc),
        "version": "4.1.0",
        "features": {
            "login": "active",
            "token_refresh": "active",
            "password_change": "active",
            "logout": "active"
        }
    }

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    "router",
    "get_current_patient",
    "LoginResponse",
    "LoginRequest",
    "TokenRefreshResponse",
    "TokenRefreshRequest",
    "LogoutResponse",
    "ChangePasswordRequest",
    "ChangePasswordResponse"
]
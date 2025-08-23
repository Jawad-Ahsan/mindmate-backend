"""
MindMate Authentication API - Login and Session Management
=========================================================
Handles user login, JWT token generation, and session management for all user types.
Includes login notifications and current user retrieval.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import bcrypt

# Import database models
from models.sql_models.patient_models import Patient, PatientAuthInfo
from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, 
    EmailVerificationStatusEnum, ApprovalStatusEnum
)
from models.sql_models.admin_models import Admin, AdminStatusEnum
from models.sql_models.base_model import USERTYPE

# Import authentication schemas
from models.pydantic_models.authentication_schemas import (
    PatientLoginResponse, SpecialistLoginResponse, AdminLoginResponse,
    ErrorResponse
)

# Import utilities
from utils.email_utils import send_login_notification_email, send_notification_email
from database.database import get_db

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# Platform admin key for admin login
PLATFORM_ADMIN_KEY = os.getenv("ADMIN_REGISTRATION_KEY", "default_secure_key")

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

# ============================================================================
# PYDANTIC MODELS FOR LOGIN
# ============================================================================

from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    """Universal login request"""
    email: EmailStr
    password: str
    user_type: str = Field(..., description="User type: patient, specialist, or admin")
    secret_key: Optional[str] = Field(None, description="Required for admin login")

class CurrentUserResponse(BaseModel):
    """Current user information response"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    user_type: str
    is_active: bool
    verification_status: Optional[str] = None
    approval_status: Optional[str] = None
    last_login: Optional[datetime] = None
    profile_complete: bool = False

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    # Check for forwarded headers first (proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    if hasattr(request, "client") and request.client:
        return request.client.host
    
    return "Unknown"

def safe_enum_to_string(enum_value) -> str:
    """Safely convert enum to string"""
    if enum_value is None:
        return "Unknown"
    
    if hasattr(enum_value, 'value'):
        return str(enum_value.value)
    
    return str(enum_value)

def send_login_notification(email: str, first_name: str, client_ip: str, user_type: str) -> bool:
    """Send login notification email to user"""
    try:
        login_time = datetime.now()
        
        if user_type in ["patient", "specialist"]:
            # Use the specific login notification function
            return send_login_notification_email(email, first_name, client_ip, login_time)
        else:
            # For admins, use general notification email
            return send_notification_email(
                to_email=email,
                subject="Admin Login Notification - MindMate Platform",
                content=f"""
                <h2>Admin Login Notification</h2>
                <p>Dear {first_name},</p>
                <p>A successful login to your admin account was detected:</p>
                <ul>
                    <li><strong>Time:</strong> {login_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                    <li><strong>IP Address:</strong> {client_ip}</li>
                    <li><strong>Account Type:</strong> Administrator</li>
                </ul>
                <p>If this wasn't you, please contact support immediately.</p>
                <p>Best regards,<br>MindMate Security Team</p>
                """
            )
    except Exception as e:
        print(f"Login notification failed for {email}: {str(e)}")
        return False

# ============================================================================
# AUTHENTICATION FUNCTIONS
# ============================================================================

def authenticate_patient(db: Session, email: str, password: str) -> tuple:
    """Authenticate patient and return patient, auth_info tuple or raise specific error"""
    try:
        patient = db.query(Patient).filter(
            Patient.email == email.lower(),
            Patient.is_deleted == False
        ).first()
        
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No patient account found with this email address"
            )
        
        auth_info = db.query(PatientAuthInfo).filter(
            PatientAuthInfo.patient_id == patient.id
        ).first()
        
        if not auth_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Patient authentication data not found. Please contact support."
            )
        
        if not auth_info.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email address not verified. Please check your email and verify your account first."
            )
        
        # Note: is_active is False for unverified accounts, which is correct behavior
        # We only check is_active after verification
        
        if not verify_password(password, auth_info.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. Please check your password and try again."
            )
        
        return patient, auth_info
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Patient authentication error for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error. Please try again later."
        )

def authenticate_specialist(db: Session, email: str, password: str) -> tuple:
    """Authenticate specialist and return specialist, auth_info tuple or raise specific error"""
    try:
        print(f"DEBUG: Specialist authentication attempt for email: {email}")
        specialist = db.query(Specialists).filter(
            Specialists.email == email.lower(),
            Specialists.is_deleted == False
        ).first()
        
        print(f"DEBUG: Specialist found: {specialist is not None}")
        if specialist:
            print(f"DEBUG: Specialist ID: {specialist.id}, Approval status: {specialist.approval_status}")
        
        if not specialist:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No specialist account found with this email address"
            )
        
        auth_info = db.query(SpecialistsAuthInfo).filter(
            SpecialistsAuthInfo.specialist_id == specialist.id
        ).first()
        
        print(f"DEBUG: Auth info found: {auth_info is not None}")
        if auth_info:
            print(f"DEBUG: Email verification status: {auth_info.email_verification_status}")
            print(f"DEBUG: Has password: {auth_info.hashed_password is not None}")
        
        if not auth_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Specialist authentication data not found. Please contact support."
            )
        
        # MODIFIED: Allow login for verified specialists, even if profile is incomplete
        print(f"DEBUG: Checking email verification status: {auth_info.email_verification_status}")
        if auth_info.email_verification_status != EmailVerificationStatusEnum.VERIFIED:
            verification_status = safe_enum_to_string(auth_info.email_verification_status)
            print(f"DEBUG: Email verification failed. Status: {verification_status}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Email verification required. Current status: {verification_status}. Please verify your email first."
            )
        print(f"DEBUG: Email verification check passed")
        
        # MODIFIED: Only reject if explicitly REJECTED or SUSPENDED
        # Allow PENDING, UNDER_REVIEW, and APPROVED to login
        print(f"DEBUG: Checking approval status: {specialist.approval_status}")
        
        if specialist.approval_status == ApprovalStatusEnum.REJECTED:
            print(f"DEBUG: Specialist rejected, blocking login")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your specialist application has been rejected. Please contact support for more information."
            )
        
        # Check if there's a SUSPENDED status (add this if your enum has it)
        if hasattr(ApprovalStatusEnum, 'SUSPENDED') and specialist.approval_status == ApprovalStatusEnum.SUSPENDED:
            print(f"DEBUG: Specialist suspended, blocking login")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your specialist account has been suspended. Please contact support."
            )
        
        print(f"DEBUG: Approval status check passed: {specialist.approval_status}")
        # Allow login for PENDING, UNDER_REVIEW, and APPROVED statuses
        # The frontend will handle showing appropriate messages based on approval_status
        
        print(f"DEBUG: Verifying password for specialist ID: {specialist.id}")
        if not verify_password(password, auth_info.hashed_password):
            print(f"DEBUG: Password verification failed for specialist ID: {specialist.id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. Please check your password and try again."
            )
        
        print(f"DEBUG: Password verification successful for specialist ID: {specialist.id}")
        print(f"DEBUG: Specialist authentication successful, returning specialist and auth_info")
        return specialist, auth_info
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Specialist authentication error for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error. Please try again later."
        )

def authenticate_admin(db: Session, email: str, password: str, secret_key: str) -> Admin:
    """Authenticate admin and return admin object or raise specific error"""
    try:
        # Verify secret key first
        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin secret key is required for authentication"
            )
        
        if secret_key != PLATFORM_ADMIN_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin secret key"
            )
        
        admin = db.query(Admin).filter(
            Admin.email == email.lower(),
            Admin.is_deleted == False
        ).first()
        
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No admin account found with this email address"
            )
        
        if not admin.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin account has been deactivated. Please contact super admin."
            )
        
        if admin.status != AdminStatusEnum.ACTIVE:
            status_str = safe_enum_to_string(admin.status)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Admin account status is {status_str}. Please contact super admin."
            )
        
        if not verify_password(password, admin.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password. Please check your password and try again."
            )
        
        return admin
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Admin authentication error for {email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system error. Please try again later."
        )

# ============================================================================
# LOGIN ENDPOINT
# ============================================================================

@router.post(
    "/login-user",
    responses={
        200: {"description": "Login successful"},
        400: {"model": ErrorResponse, "description": "Invalid input or missing required fields"},
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account not verified, approved, or active"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def login_user(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """Universal login endpoint for all user types"""
    try:
        user_type = request.user_type.lower().strip()
        email = request.email.lower().strip()
        
        # Validate user type
        if user_type not in ["patient", "specialist", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user type. Must be one of: patient, specialist, admin"
            )
        
        # Validate email format (basic check since EmailStr should handle this)
        if not email or "@" not in email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate password
        if not request.password or len(request.password.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password cannot be empty"
            )
        
        # For admin login, secret_key is required
        if user_type == "admin" and not request.secret_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Secret key is required for admin login"
            )
        
        print(f"Login attempt: {email} as {user_type}")
        
        # Authenticate based on user type
        authenticated_user = None
        auth_info = None
        
        try:
            print(f"DEBUG: Attempting authentication for {email} as {user_type}")
            if user_type == "patient":
                authenticated_user, auth_info = authenticate_patient(db, email, request.password)
                print(f"DEBUG: Patient authentication successful")
                
            elif user_type == "specialist":
                authenticated_user, auth_info = authenticate_specialist(db, email, request.password)
                print(f"DEBUG: Specialist authentication successful")
                
            elif user_type == "admin":
                authenticated_user = authenticate_admin(db, email, request.password, request.secret_key)
                print(f"DEBUG: Admin authentication successful")
                
        except HTTPException as auth_error:
            # Re-raise authentication errors with proper logging
            print(f"DEBUG: Authentication failed for {email} as {user_type}: {auth_error.detail}")
            print(f"DEBUG: HTTP status: {auth_error.status_code}")
            raise auth_error
        
        # This should not happen with our new authentication functions, but keep as safety
        if not authenticated_user:
            print(f"Unexpected: No user returned for {email} as {user_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        # Update last login time
        try:
            now = datetime.now()
            if user_type == "patient" and auth_info:
                auth_info.last_login = now
            elif user_type == "specialist" and auth_info:
                auth_info.last_login = now
            elif user_type == "admin":
                authenticated_user.last_login = now
            
            db.commit()
            print(f"Login successful for {email} as {user_type}")
            
        except Exception as db_error:
            print(f"Failed to update last login for {email}: {str(db_error)}")
            # Don't fail the login for this, just log it
            db.rollback()
        
        # Create JWT tokens
        try:
            token_data = {
                "sub": str(authenticated_user.id),
                "email": authenticated_user.email,
                "user_type": user_type,
                "iat": datetime.utcnow()
            }
            
            access_token = create_access_token(token_data)
            refresh_token = create_refresh_token(token_data)
            
        except Exception as token_error:
            print(f"Token creation failed for {email}: {str(token_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create authentication tokens"
            )
        
        # Get client IP and send login notification
        try:
            client_ip = get_client_ip(http_request)
            notification_sent = send_login_notification(
                authenticated_user.email,
                authenticated_user.first_name,
                client_ip,
                user_type
            )
            
            if notification_sent:
                print(f"Login notification sent to {authenticated_user.email}")
            else:
                print(f"Warning: Login notification failed for {authenticated_user.email}")
                
        except Exception as notification_error:
            print(f"Login notification error for {authenticated_user.email}: {str(notification_error)}")
            # Don't fail the login for notification errors
        
        # Prepare response based on user type
        full_name = f"{authenticated_user.first_name} {authenticated_user.last_name}"
        
        try:
            if user_type == "patient":
                # Check profile completeness (basic check)
                profile_complete = bool(
                    authenticated_user.phone and 
                    authenticated_user.city and
                    authenticated_user.district
                )
                
                print(f"DEBUG: Creating patient login response")
                print(f"DEBUG: Patient ID: {authenticated_user.id}")
                print(f"DEBUG: Patient email: {authenticated_user.email}")
                print(f"DEBUG: Patient full_name: {full_name}")
                print(f"DEBUG: Profile complete: {profile_complete}")
                
                response = PatientLoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    user_id=str(authenticated_user.id),
                    email=authenticated_user.email,
                    full_name=full_name,
                    profile_complete=profile_complete,
                    verification_status="verified",
                    has_active_appointments=False  # TODO: Check actual appointments
                )
                
                print(f"DEBUG: Patient response created: {response}")
                return response
            
            elif user_type == "specialist":
                print(f"DEBUG: Creating specialist login response for ID: {authenticated_user.id}")
                
                # MODIFIED: Only approved AND verified specialists can practice
                can_practice = (
                    authenticated_user.approval_status == ApprovalStatusEnum.APPROVED and
                    auth_info.email_verification_status == EmailVerificationStatusEnum.VERIFIED
                )
                print(f"DEBUG: Can practice: {can_practice} (approved: {authenticated_user.approval_status == ApprovalStatusEnum.APPROVED}, verified: {auth_info.email_verification_status == EmailVerificationStatusEnum.VERIFIED})")
                
                # Check profile completeness - more comprehensive check
                profile_complete = bool(
                    authenticated_user.phone and
                    authenticated_user.address and
                    authenticated_user.bio and
                    authenticated_user.consultation_fee and
                    authenticated_user.languages_spoken and
                    authenticated_user.specializations and
                    len(authenticated_user.specializations) > 0
                )
                print(f"DEBUG: Profile complete: {profile_complete}")
                print(f"DEBUG: Profile fields - phone: {bool(authenticated_user.phone)}, address: {bool(authenticated_user.address)}, bio: {bool(authenticated_user.bio)}, fee: {bool(authenticated_user.consultation_fee)}, languages: {bool(authenticated_user.languages_spoken)}, specializations: {len(authenticated_user.specializations) if authenticated_user.specializations else 0}")
                
                # MODIFIED: Add status messages for different approval states
                status_message = None
                if authenticated_user.approval_status == ApprovalStatusEnum.PENDING:
                    if not profile_complete:
                        status_message = "Please complete your profile and submit required documents before admin approval."
                    else:
                        status_message = "Your specialist application is pending admin approval. We'll notify you once approved."
                elif authenticated_user.approval_status == ApprovalStatusEnum.UNDER_REVIEW:
                    status_message = "Your application is currently under review by our team. We'll notify you once the review is complete."
                elif authenticated_user.approval_status == ApprovalStatusEnum.APPROVED:
                    if not profile_complete:
                        status_message = "Your account is approved but profile is incomplete. Please complete your profile to start accepting appointments."
                    else:
                        status_message = "Your account has been approved! You can now start accepting appointments."
                
                return SpecialistLoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    user_id=str(authenticated_user.id),
                    email=authenticated_user.email,
                    full_name=full_name,
                    approval_status=safe_enum_to_string(authenticated_user.approval_status),
                    verification_status=safe_enum_to_string(auth_info.email_verification_status),
                    can_practice=can_practice,
                    profile_complete=profile_complete,
                    status_message=status_message  # MODIFIED: Added status message
                )
            
            elif user_type == "admin":
                # Admin permissions (simplified)
                permissions = {
                    "manage_users": True,
                    "approve_specialists": True,
                    "view_analytics": True,
                    "system_config": authenticated_user.role.value == "super_admin"
                }
                
                return AdminLoginResponse(
                    access_token=access_token,
                    refresh_token=refresh_token,
                    user_id=str(authenticated_user.id),
                    email=authenticated_user.email,
                    full_name=full_name,
                    role=safe_enum_to_string(authenticated_user.role),
                    permissions=permissions,
                    last_login=authenticated_user.last_login
                )
                
        except Exception as response_error:
            print(f"Response creation failed for {email}: {str(response_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create login response"
            )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Unexpected login error for {request.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login. Please try again."
        )

# ============================================================================
# CURRENT USER ENDPOINT
# ============================================================================

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """Extract current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as jwt_err:
            print(f"JWT decode error: {str(jwt_err)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        user_type: str = payload.get("user_type")
        
        if user_id is None or email is None or user_type is None:
            print(f"Invalid token payload: user_id={user_id}, email={email}, user_type={user_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload - missing required fields"
            )
        
        # Fetch user based on type
        user = None
        auth_info = None
        
        try:
            if user_type == "patient":
                user = db.query(Patient).filter(
                    Patient.id == user_id,
                    Patient.email == email,
                    Patient.is_deleted == False
                ).first()
                
                if user:
                    auth_info = db.query(PatientAuthInfo).filter(
                        PatientAuthInfo.patient_id == user.id
                    ).first()
                    
                    if not auth_info:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Patient authentication data not found"
                        )
                    
                    # Allow login for verified accounts, but provide verification status
                    if not auth_info.is_verified:
                        # Return user data but indicate verification is needed
                        # This allows the frontend to handle unverified accounts gracefully
                        pass
            
            elif user_type == "specialist":
                user = db.query(Specialists).filter(
                    Specialists.id == user_id,
                    Specialists.email == email,
                    Specialists.is_deleted == False
                ).first()
                
                if user:
                    auth_info = db.query(SpecialistsAuthInfo).filter(
                        SpecialistsAuthInfo.specialist_id == user.id,
                        SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED
                    ).first()
                    
                    # MODIFIED: Allow specialists with verified email but any approval status (except rejected/suspended)
                    if not auth_info:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Specialist account not verified"
                        )
                    
                    # Check if specialist is rejected or suspended
                    if user.approval_status == ApprovalStatusEnum.REJECTED:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Specialist account has been rejected"
                        )
                    
                    if hasattr(ApprovalStatusEnum, 'SUSPENDED') and user.approval_status == ApprovalStatusEnum.SUSPENDED:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Specialist account has been suspended"
                        )
            
            elif user_type == "admin":
                user = db.query(Admin).filter(
                    Admin.id == user_id,
                    Admin.email == email,
                    Admin.is_deleted == False,
                    Admin.is_active == True,
                    Admin.status == AdminStatusEnum.ACTIVE
                ).first()
            
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid user type in token: {user_type}"
                )
        
        except HTTPException:
            raise
        except Exception as db_error:
            print(f"Database error during user lookup: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during authentication"
            )
        
        if not user:
            print(f"User not found: id={user_id}, email={email}, type={user_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found, deleted, or inactive"
            )
        
        return {
            "user": user,
            "auth_info": auth_info,
            "user_type": user_type,
            "token_payload": payload
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Unexpected error in token validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed due to unexpected error"
        )

        

@router.get(
    "/get-current-user",
    response_model=CurrentUserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_current_user(
    current_user_data: dict = Depends(get_current_user_from_token)
):
    """Get current authenticated user information"""
    try:
        user = current_user_data["user"]
        auth_info = current_user_data["auth_info"]
        user_type = current_user_data["user_type"]
        
        print(f"Getting current user info for {user.email} as {user_type}")
        
        # Build response
        response_data = {
            "user_id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": f"{user.first_name} {user.last_name}",
            "user_type": user_type,
            "is_active": True
        }
        
        # Add type-specific information
        try:
            if user_type == "patient":
                response_data.update({
                    "verification_status": "verified" if auth_info and auth_info.is_verified else "pending",
                    "last_login": auth_info.last_login if auth_info else None,
                    "profile_complete": bool(
                        getattr(user, 'phone', None) and 
                        getattr(user, 'address', None) and 
                        getattr(user, 'emergency_contact', None)
                    )
                })
            
            elif user_type == "specialist":
                response_data.update({
                    "verification_status": safe_enum_to_string(auth_info.email_verification_status) if auth_info else "pending",
                    "approval_status": safe_enum_to_string(getattr(user, 'approval_status', 'unknown')),
                    "last_login": auth_info.last_login if auth_info else None,
                    "profile_complete": bool(
                        getattr(user, 'phone', None) and 
                        getattr(user, 'address', None) and 
                        getattr(user, 'bio', None) and 
                        getattr(user, 'consultation_fee', None) and 
                        getattr(user, 'languages_spoken', None) and 
                        getattr(user, 'specializations', None) and 
                        len(getattr(user, 'specializations', [])) > 0
                    )
                })
            
            elif user_type == "admin":
                response_data.update({
                    "verification_status": "verified",
                    "approval_status": safe_enum_to_string(getattr(user, 'status', 'active')),
                    "last_login": getattr(user, 'last_login', None),
                    "profile_complete": True
                })
        
        except Exception as profile_error:
            print(f"Error building profile info for {user.email}: {str(profile_error)}")
            # Set safe defaults if profile building fails
            response_data.update({
                "verification_status": "verified" if user_type == "admin" else "unknown",
                "last_login": None,
                "profile_complete": False
            })
        
        return CurrentUserResponse(**response_data)
    
    except Exception as e:
        print(f"Failed to get current user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

# ============================================================================
# EXPORTS 
# ============================================================================

__all__ = [
    "router",
    "login_user",
    "get_current_user",
    "get_current_user_from_token",
    "create_access_token",
    "create_refresh_token",
    "verify_password"
]
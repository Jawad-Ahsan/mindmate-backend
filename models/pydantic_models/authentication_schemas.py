"""
Authentication Request/Response Schemas
======================================
Minimum required fields for register and login endpoints
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, Literal
from datetime import datetime, date
from enum import Enum
import re

# Import enums from your models
from models.sql_models.patient_models import GenderEnum, LanguageEnum
from models.sql_models.specialist_models import SpecialistTypeEnum, GenderEnum as SpecialistGenderEnum
from models.sql_models.admin_models import AdminRoleEnum

# ============================================================================
# SHARED MODELS
# ============================================================================

class BaseAuthModel(BaseModel):
    """Base authentication model configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        extra='forbid'
    )

class LoginResponse(BaseAuthModel):
    """Common login response for all user types"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    user_type: Literal["patient", "specialist", "admin"]
    email: str
    full_name: str
    expires_in: int = 3600  # Token expiry in seconds

# ============================================================================
# PATIENT AUTHENTICATION
# ============================================================================

class PatientRegisterRequest(BaseAuthModel):
    """Patient registration request - minimum required fields"""
    # Personal Information
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    
    # Required demographic info
    date_of_birth: date
    gender: GenderEnum
    city: str = Field(min_length=2, max_length=100)
        
    # Terms acceptance
    accepts_terms_and_conditions: bool = True
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        if (date.today() - v).days > 36500:  # ~100 years
            raise ValueError('Date of birth seems unrealistic')
        return v
    
    @field_validator('accepts_terms_and_conditions')
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v

class PatientRegisterResponse(BaseAuthModel):
    """Patient registration response"""
    message: str = "Registration successful"
    user_id: str
    email: str
    full_name: str
    verification_required: bool = True
    next_steps: list[str] = Field(default_factory=lambda: [
        "Check your email for verification link",
        "Complete your profile setup"
    ])

class PatientLoginRequest(BaseAuthModel):
    """Patient login request"""
    email: EmailStr
    password: str
    remember_me: bool = False

class PatientLoginResponse(LoginResponse):
    """Patient login response"""
    user_type: Literal["patient"] = "patient"
    profile_complete: bool
    verification_status: str
    has_active_appointments: bool = False

# ============================================================================
# SPECIALIST AUTHENTICATION
# ============================================================================

class SpecialistRegisterRequest(BaseAuthModel):
    """Specialist registration request - minimum required fields for new simplified flow"""
    # Personal Information - only basic fields required
    first_name: str = Field(min_length=2, max_length=100)
    last_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)
    
    # Terms acceptance
    accepts_terms_and_conditions: bool = True
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
    
    @field_validator('accepts_terms_and_conditions')
    @classmethod
    def validate_terms(cls, v: bool) -> bool:
        if not v:
            raise ValueError('You must accept the terms and conditions')
        return v

class SpecialistRegisterResponse(BaseAuthModel):
    """Specialist registration response"""
    message: str = "Registration successful"
    user_id: str
    email: str
    full_name: str
    approval_required: bool = True
    next_steps: list[str] = Field(default_factory=lambda: [
        "Check your email for verification link",
        "Upload required documents for approval",
        "Wait for admin approval (typically 2-3 business days)",
        "Complete your profile setup once approved"
    ])

class SpecialistLoginRequest(BaseAuthModel):
    """Specialist login request"""
    email: EmailStr
    password: str
    remember_me: bool = False

class SpecialistLoginResponse(LoginResponse):
    """Specialist login response"""
    user_type: Literal["specialist"] = "specialist"
    approval_status: str
    verification_status: str
    can_practice: bool
    profile_complete: bool
    status_message: Optional[str] = None 

# ============================================================================
# ADMIN AUTHENTICATION
# ============================================================================

class AdminRegisterRequest(BaseAuthModel):
    """Admin registration request - minimum required fields"""
    # Personal Information
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    
    # Admin specific
    security_key: str = Field(min_length=10)  # Special platform key
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class AdminRegisterResponse(BaseAuthModel):
    """Admin registration response"""
    message: str = "Admin registration successful"
    user_id: str
    email: str
    full_name: str
    role: str
    next_steps: list[str] = Field(default_factory=lambda: [
        "Login with your credentials",
        "Access admin dashboard",
        "Review pending specialist approvals"
    ])

class AdminLoginRequest(BaseAuthModel):
    """Admin login request"""
    email: EmailStr
    password: str
    security_key: str  # Additional security for admin login

class AdminLoginResponse(LoginResponse):
    """Admin login response"""
    user_type: Literal["admin"] = "admin"
    role: str
    permissions: dict[str, bool]
    last_login: Optional[datetime] = None

# ============================================================================
# GENERAL REQUEST/RESPONSE MODELS
# ============================================================================

class RefreshTokenRequest(BaseAuthModel):
    """Refresh token request"""
    refresh_token: str

class RefreshTokenResponse(BaseAuthModel):
    """Refresh token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class LogoutRequest(BaseAuthModel):
    """Logout request"""
    refresh_token: Optional[str] = None

class LogoutResponse(BaseAuthModel):
    """Logout response"""
    message: str = "Successfully logged out"

class PasswordResetRequest(BaseAuthModel):
    """Password reset request"""
    email: EmailStr

class PasswordResetResponse(BaseAuthModel):
    """Password reset response"""
    message: str = "Password reset instructions sent to your email"

class PasswordResetConfirmRequest(BaseAuthModel):
    """Password reset confirmation request"""
    reset_token: str
    new_password: str = Field(min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class PasswordResetConfirmResponse(BaseAuthModel):
    """Password reset confirmation response"""
    message: str = "Password reset successful"

class EmailVerificationRequest(BaseAuthModel):
    """Email verification request"""
    verification_token: str

class EmailVerificationResponse(BaseAuthModel):
    """Email verification response"""
    message: str = "Email verified successfully"
    user_id: str

# ============================================================================
# ERROR RESPONSE MODELS
# ============================================================================

class ErrorResponse(BaseAuthModel):
    """Standard error response"""
    error: str
    message: str
    details: Optional[dict] = None

class ValidationErrorResponse(BaseAuthModel): 
    """Validation error response"""
    error: str = "validation_error"
    message: str = "Invalid input data"
    field_errors: dict[str, list[str]]

# ============================================================================
# EXPORTS 
# ============================================================================

__all__ = [
    # Patient Auth
    "PatientRegisterRequest",
    "PatientRegisterResponse", 
    "PatientLoginRequest",
    "PatientLoginResponse",
    
    # Specialist Auth
    "SpecialistRegisterRequest",
    "SpecialistRegisterResponse",
    "SpecialistLoginRequest", 
    "SpecialistLoginResponse",
    
    # Admin Auth
    "AdminRegisterRequest",
    "AdminRegisterResponse",
    "AdminLoginRequest",
    "AdminLoginResponse",
    
    # General Auth
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "LogoutResponse",
    "PasswordResetRequest",
    "PasswordResetResponse",
    "PasswordResetConfirmRequest",
    "PasswordResetConfirmResponse",
    "EmailVerificationRequest",
    "EmailVerificationResponse",
    
    # Error Responses
    "ErrorResponse",
    "ValidationErrorResponse",
]
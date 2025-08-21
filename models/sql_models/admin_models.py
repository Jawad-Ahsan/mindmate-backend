"""
Simple Admin Model - Platform Moderation
========================================

Simplified admin model with only two admin types: admin and super_admin
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Enum, 
    Index, UniqueConstraint
)
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional
from datetime import datetime
import enum
import uuid
import bcrypt

# Import your base model
from .base_model import Base, BaseModel as SQLAlchemyBaseModel

# ============================================================================
# ENUMERATIONS
# ============================================================================

class AdminRoleEnum(str, enum.Enum):
    """Simple admin role hierarchy"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"

class AdminStatusEnum(str, enum.Enum):
    """Admin account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class BaseModelConfig(BaseModel):
    """Base Pydantic model with V2 configuration"""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True,
        extra='forbid'
    )

class AdminCreate(BaseModelConfig):
    """Create admin user"""
    first_name: str = Field(min_length=2, max_length=50)
    last_name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    role: AdminRoleEnum = Field(default=AdminRoleEnum.ADMIN)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Basic password validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class AdminUpdate(BaseModelConfig):
    """Update admin user"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    role: Optional[AdminRoleEnum] = None
    status: Optional[AdminStatusEnum] = None
    is_active: Optional[bool] = None

class AdminResponse(BaseModelConfig):
    """Admin response model"""
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    role: AdminRoleEnum
    status: AdminStatusEnum
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    @property
    def full_name(self) -> str:
        """Full name for display"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.role == AdminRoleEnum.SUPER_ADMIN

class PasswordChangeRequest(BaseModelConfig):
    """Change password request"""
    current_password: str
    new_password: str = Field(min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Password strength validation"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

# ============================================================================
# SQLALCHEMY MODEL
# ============================================================================

class Admin(Base, SQLAlchemyBaseModel):
    """
    Simple admin model for platform moderation.
    Two roles: admin and super_admin
    """
    
    __tablename__ = "admins"
    
    # Basic Information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    
    # Admin Configuration
    role = Column(Enum(AdminRoleEnum), nullable=False, default=AdminRoleEnum.ADMIN)
    status = Column(Enum(AdminStatusEnum), nullable=False, default=AdminStatusEnum.ACTIVE)
    
    
    # Authentication & Security 
    security_key = Column(String(255), nullable=False)  #special key by the plateform for admin
    hashed_password = Column(String(255), nullable=False)
    failed_login_attempts = Column(Integer, default=0)

    
    
    # Account Management
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    
    # Constraints and Indexes
    __table_args__ = (
        Index('idx_admin_email', 'email'),
        Index('idx_admin_role', 'role'),
        Index('idx_admin_status', 'status'),
        Index('idx_admin_active', 'is_active'),
        UniqueConstraint('email', name='uq_admin_email'),
    )
    
    # Properties
    @property
    def full_name(self) -> str:
        """Full name for display"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.role == AdminRoleEnum.SUPER_ADMIN
    
    @property
    def can_login(self) -> bool:
        """Check if user can login"""
        return (
            self.is_active and 
            self.status == AdminStatusEnum.ACTIVE and
            self.failed_login_attempts < 5
        )
    
    @property
    def is_account_locked(self) -> bool:
        """Check if account is locked due to failed attempts"""
        return self.failed_login_attempts >= 5
    
    # Password Management
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        salt = bcrypt.gensalt()
        self.hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Check if password is correct"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
        except Exception:
            return False
    
    def reset_failed_attempts(self) -> None:
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
    
    def increment_failed_attempts(self) -> None:
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
    
    # Permission Management (Role-based)
    def can_manage_admins(self) -> bool:
        """Only super admins can manage other admins"""
        return self.role == AdminRoleEnum.SUPER_ADMIN
    
    def can_moderate_content(self) -> bool:
        """Both admin types can moderate content"""
        return self.role in [AdminRoleEnum.ADMIN, AdminRoleEnum.SUPER_ADMIN]
    
    def can_view_reports(self) -> bool:
        """Both admin types can view reports"""
        return self.role in [AdminRoleEnum.ADMIN, AdminRoleEnum.SUPER_ADMIN]
    
    def can_manage_users(self) -> bool:
        """Both admin types can manage users"""
        return self.role in [AdminRoleEnum.ADMIN, AdminRoleEnum.SUPER_ADMIN]
    
    def can_access_system_settings(self) -> bool:
        """Only super admins can access system settings"""
        return self.role == AdminRoleEnum.SUPER_ADMIN
    
    # Account Management Methods
    def activate_account(self) -> None:
        """Activate admin account"""
        self.is_active = True
        self.status = AdminStatusEnum.ACTIVE
    
    def deactivate_account(self) -> None:
        """Deactivate admin account"""
        self.is_active = False
        self.status = AdminStatusEnum.INACTIVE
    
    def suspend_account(self) -> None:
        """Suspend admin account"""
        self.status = AdminStatusEnum.SUSPENDED
        self.is_active = False
    
    def login_success(self) -> None:
        """Record successful login"""
        self.last_login = func.now()
        self.reset_failed_attempts()
    
    # Pydantic Integration
    @classmethod
    def from_pydantic(cls, pydantic_model: AdminCreate) -> 'Admin':
        """Create from Pydantic model"""
        admin_data = pydantic_model.model_dump(exclude={'password'})
        admin = cls(**admin_data)
        admin.set_password(pydantic_model.password)
        return admin
    
    def to_pydantic(self) -> AdminResponse:
        """Convert to Pydantic model"""
        return AdminResponse.model_validate(self)
    
    def update_from_pydantic(self, pydantic_model: AdminUpdate) -> 'Admin':
        """Update from Pydantic model"""
        update_data = pydantic_model.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(self, field):
                setattr(self, field, value)
        
        return self

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_admin(admin_data: AdminCreate) -> Admin:
    """Create a new admin user"""
    return Admin.from_pydantic(admin_data)

def get_admin_permissions(role: AdminRoleEnum) -> dict:
    """Get permissions for each admin role"""
    permissions = {
        AdminRoleEnum.SUPER_ADMIN: {
            "manage_admins": True,
            "moderate_content": True,
            "view_reports": True,
            "manage_users": True,
            "system_settings": True,
        },
        AdminRoleEnum.ADMIN: {
            "manage_admins": False,
            "moderate_content": True,
            "view_reports": True,
            "manage_users": True,
            "system_settings": False,
        }
    }
    return permissions.get(role, {})

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "AdminRoleEnum",
    "AdminStatusEnum",
    
    # Pydantic Models
    "AdminCreate",
    "AdminUpdate",
    "AdminResponse",
    "PasswordChangeRequest",
    
    # SQLAlchemy Models
    "Admin",
    
    # Utility Functions
    "create_admin",
    "get_admin_permissions"
]
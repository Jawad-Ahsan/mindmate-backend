"""
Specialist Profile Routes
========================
API endpoints for accessing specialist profiles with different access levels:
- Public: Accessible to patients (basic info, specializations, ratings)
- Protected: Accessible to admins (complete profile with documents and approval data)
- Private: Accessible to specialist only (personal details and account info)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

# Import dependencies
from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from models.sql_models.specialist_models import Specialists
from models.sql_models.admin_models import Admin

# Import services
from services.specialists.specialist_profiles import (
    create_specialist_public_profile_response,
    create_specialist_protected_profile_response,
    create_specialist_private_profile_response
)

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/specialist-profiles", tags=["Specialist Profiles"])

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_current_specialist(current_user_data: dict = Depends(get_current_user_from_token)) -> Specialists:
    """Dependency to get current authenticated specialist"""
    user = current_user_data["user"]
    user_type = current_user_data["user_type"]
    
    if user_type != "specialist":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Specialist access required"
        )
    
    if not isinstance(user, Specialists):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid specialist user"
        )
    
    return user

def get_current_admin(current_user_data: dict = Depends(get_current_user_from_token)) -> Admin:
    """Dependency to get current authenticated admin"""
    user = current_user_data["user"]
    user_type = current_user_data["user_type"]
    
    if user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    if not isinstance(user, Admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin user"
        )
    
    return user

# ============================================================================
# PUBLIC PROFILE ENDPOINTS (Patient Access)
# ============================================================================

@router.get(
    "/public/{specialist_id}",
    summary="Get Specialist Public Profile",
    description="""
    Get specialist's public profile accessible to patients.
    
    **Includes:**
    - Basic specialist information (name, type, experience)
    - Bio and consultation fee
    - Specializations and primary specialization
    - Availability status and ratings
    - Contact information (optional)
    
    **Access:** All authenticated users
    """,
    responses={
        200: {
            "description": "Public profile retrieved successfully"
        },
        404: {
            "description": "Specialist not found or not approved"
        }
    }
)
async def get_specialist_public_profile(
    specialist_id: uuid.UUID,
    include_contact: bool = False,
    db: Session = Depends(get_db)
):
    """Get specialist public profile - accessible to all authenticated users"""
    
    # Get public profile
    profile_response = create_specialist_public_profile_response(db, specialist_id)
    
    if not profile_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialist not found or not approved"
        )
    
    return profile_response

# ============================================================================
# PROTECTED PROFILE ENDPOINTS (Admin Access)
# ============================================================================

@router.get(
    "/protected/{specialist_id}",
    summary="Get Specialist Protected Profile",
    description="""
    Get specialist's protected profile accessible to admins only.
    
    **Includes:**
    - Complete specialist information
    - Authentication status and login history
    - Approval data and documents
    - Document verification status
    - Profile completeness metrics
    
    **Access:** Admins only
    """,
    responses={
        200: {
            "description": "Protected profile retrieved successfully"
        },
        403: {
            "description": "Access denied - admin access required"
        },
        404: {
            "description": "Specialist not found"
        }
    }
)
async def get_specialist_protected_profile(
    specialist_id: uuid.UUID,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specialist protected profile - accessible to admins only"""
    
    # Get protected profile
    profile_response = create_specialist_protected_profile_response(db, specialist_id)
    
    if not profile_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialist not found"
        )
    
    logger.info(f"Admin {current_admin.id} retrieved protected profile for specialist {specialist_id}")
    return profile_response

# ============================================================================
# PRIVATE PROFILE ENDPOINTS (Specialist Access)
# ============================================================================

@router.get(
    "/private/me",
    summary="Get My Private Profile",
    description="""
    Get specialist's own private profile.
    
    **Includes:**
    - Complete personal information
    - Account and authentication details
    - Approval data and documents
    - Profile completion percentage
    - All personal and professional details
    
    **Access:** Specialist only (own profile)
    """,
    responses={
        200: {
            "description": "Private profile retrieved successfully"
        },
        403: {
            "description": "Access denied - specialist access required"
        },
        404: {
            "description": "Profile not found"
        }
    }
)
async def get_my_private_profile(
    current_specialist: Specialists = Depends(get_current_specialist),
    db: Session = Depends(get_db)
):
    """Get specialist's own private profile"""
    
    # Get private profile for current specialist
    profile_response = create_specialist_private_profile_response(db, current_specialist.id)
    
    if not profile_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    logger.info(f"Specialist {current_specialist.id} retrieved their private profile")
    return profile_response

@router.get(
    "/private/{specialist_id}",
    summary="Get Specialist Private Profile (Admin Access)",
    description="""
    Get specialist's private profile - admin access only.
    
    **Includes:**
    - Complete personal information
    - Account and authentication details
    - Approval data and documents
    - Profile completion percentage
    - All personal and professional details
    
    **Access:** Admins only
    """,
    responses={
        200: {
            "description": "Private profile retrieved successfully"
        },
        403: {
            "description": "Access denied - admin access required"
        },
        404: {
            "description": "Specialist not found"
        }
    }
)
async def get_specialist_private_profile(
    specialist_id: uuid.UUID,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get specialist private profile - accessible to admins only"""
    
    # Get private profile
    profile_response = create_specialist_private_profile_response(db, specialist_id)
    
    if not profile_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specialist not found"
        )
    
    logger.info(f"Admin {current_admin.id} retrieved private profile for specialist {specialist_id}")
    return profile_response

# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get(
    "/health",
    summary="Health Check",
    description="Health check endpoint for specialist profile service"
)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "specialist_profiles",
        "message": "Specialist profile service is running"
    }

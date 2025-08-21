"""
MindMate Registration API - Fixed with Email Verification Flow
============================================================
Proper email verification flow where registration is only complete after email verification.
Only sends OTP verification emails during registration, completion emails after verification.
"""

import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import bcrypt

# Import database models
from models.sql_models.patient_models import (
    Patient, PatientAuthInfo, PatientPreferences, 
    RecordStatusEnum, LanguageEnum, GenderEnum
)
from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, SpecialistsApprovalData,
    ApprovalStatusEnum, EmailVerificationStatusEnum, AvailabilityStatusEnum,
    SpecialistTypeEnum, GenderEnum as SpecialistGenderEnum
)
from models.sql_models.admin_models import Admin, AdminRoleEnum, AdminStatusEnum
from models.sql_models.base_model import USERTYPE

# Import authentication schemas
from models.pydantic_models.authentication_schemas import (
    PatientRegisterRequest, PatientRegisterResponse,
    SpecialistRegisterRequest, SpecialistRegisterResponse,
    AdminRegisterRequest, AdminRegisterResponse,
    ErrorResponse
)

# Import utilities with safe error handling
from utils.email_utils import (
    send_verification_email, generate_otp, get_otp_expiry,
    send_patient_registration_completion_email,
    send_specialist_registration_completion_email,
    send_admin_specialist_registration_notification,
    send_notification_email,
    safe_enum_to_string
)

from database.database import get_db

# Environment variables for super admin
SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD") 
SUPER_ADMIN_FIRST_NAME = os.getenv("SUPER_ADMIN_FIRST_NAME", "Super")
SUPER_ADMIN_LAST_NAME = os.getenv("SUPER_ADMIN_LAST_NAME", "Admin")
PLATFORM_ADMIN_KEY = os.getenv("ADMIN_REGISTRATION_KEY", "default_secure_key")

router = APIRouter(prefix="/auth", tags=["Registration"])

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_verified_email_exists_for_user_type(db: Session, email: str, user_type: USERTYPE) -> bool:
    """Check if VERIFIED email exists for specific user type"""
    email = email.lower()
    
    if user_type == USERTYPE.PATIENT:
        patient = db.query(Patient).filter(
            Patient.email == email,
            Patient.is_deleted == False
        ).first()
        if patient:
            auth_info = db.query(PatientAuthInfo).filter(
                PatientAuthInfo.patient_id == patient.id,
                PatientAuthInfo.is_verified == True
            ).first()
            return auth_info is not None
        return False
    
    elif user_type == USERTYPE.SPECIALIST:
        specialist = db.query(Specialists).filter(
            Specialists.email == email,
            Specialists.is_deleted == False
        ).first()
        if specialist:
            auth_info = db.query(SpecialistsAuthInfo).filter(
                SpecialistsAuthInfo.specialist_id == specialist.id,
                SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED
            ).first()
            return auth_info is not None
        return False
    
    elif user_type == USERTYPE.ADMIN:
        return db.query(Admin).filter(
            Admin.email == email,
            Admin.is_deleted == False,
            Admin.is_active == True
        ).first() is not None
    
    return False

def check_pending_email_exists_for_user_type(db: Session, email: str, user_type: USERTYPE) -> bool:
    """Check if email exists but is pending verification for specific user type"""
    email = email.lower()
    
    if user_type == USERTYPE.PATIENT:
        patient = db.query(Patient).filter(
            Patient.email == email,
            Patient.is_deleted == False
        ).first()
        if patient:
            auth_info = db.query(PatientAuthInfo).filter(
                PatientAuthInfo.patient_id == patient.id,
                PatientAuthInfo.is_verified == False
            ).first()
            return auth_info is not None
        return False
    
    elif user_type == USERTYPE.SPECIALIST:
        specialist = db.query(Specialists).filter(
            Specialists.email == email,
            Specialists.is_deleted == False
        ).first()
        if specialist:
            auth_info = db.query(SpecialistsAuthInfo).filter(
                SpecialistsAuthInfo.specialist_id == specialist.id,
                SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.PENDING
            ).first()
            return auth_info is not None
        return False
    
    return False

def get_admin_emails_for_notifications(db: Session) -> List[str]:
    """Get all active admin emails for notifications"""
    try:
        return [
            admin.email for admin in db.query(Admin).filter(
                Admin.is_active == True,
                Admin.status == AdminStatusEnum.ACTIVE,
                Admin.is_deleted == False
            ).all()
        ]
    except:
        return []

def create_default_patient_preferences(patient_id: str) -> PatientPreferences:
    """Create default preferences for new patient"""
    return PatientPreferences(
        patient_id=patient_id,
        location_preferences={'consultation_mode': 'virtual'},
        cultural_preferences={'language_preference': 'urdu'},
        therapy_preferences={'session_duration': 60, 'frequency': 'weekly'},
        financial_preferences={'max_budget': 5000.0},
        specialist_preferences={'min_rating': 4.0, 'min_experience': 3},
        availability_preferences={'urgency': 'standard'},
        priority_weights={
            'cultural_fit': 0.25, 'clinical_match': 0.20, 'location': 0.15,
            'cost': 0.15, 'availability': 0.10, 'ratings': 0.08, 'experience': 0.07
        },
        consultation_mode='virtual',
        urgency_level='standard'
    )

# ============================================================================
# ENUM CONVERSION HELPERS
# ============================================================================

def convert_string_to_enum(value, enum_class):
    """Convert string value to enum safely"""
    if value is None:
        return None
        
    # If it's already the right enum type, return it
    if isinstance(value, enum_class):
        return value
    
    # If it's a string, try to convert
    if isinstance(value, str):
        # First try by value
        for enum_item in enum_class:
            if enum_item.value == value:
                return enum_item
        
        # Then try by name (case insensitive)
        try:
            return enum_class[value.upper()]
        except (KeyError, AttributeError):
            pass
        
        # Last try - direct conversion
        try:
            return enum_class(value)
        except (ValueError, TypeError):
            pass
    
    raise ValueError(f"Cannot convert {value} to {enum_class.__name__}")

# ============================================================================
# EMAIL UTILITY WRAPPERS - CONSISTENT WITH EMAIL_UTILS.PY
# ============================================================================

def safe_send_verification_email(email: str, otp: str, user_type_enum, user_name: str) -> bool:
    """Safely send verification email with proper enum handling"""
    try:
        # Convert user_type to safe string for email function
        user_type_str = safe_enum_to_string(user_type_enum) if user_type_enum else "User"
        return send_verification_email(email, otp, user_type_enum, user_name)
    except Exception as e:
        print(f"Verification email failed for {email}: {str(e)}")
        return False

def safe_send_completion_email(email: str, first_name: str, last_name: str, 
                              specialization_enum=None, user_type: str = "patient") -> bool:
    """Safely send completion email with proper enum handling"""
    try:
        if user_type == "patient":
            return send_patient_registration_completion_email(email, first_name, last_name)
        elif user_type == "specialist":
            # Pass the enum directly - email function will handle conversion using safe_enum_to_string
            specialization_str = safe_enum_to_string(specialization_enum) if specialization_enum else "Specialist"
            return send_specialist_registration_completion_email(
                email, first_name, last_name, specialization_str
            )
        return False
    except Exception as e:
        print(f"Completion email failed for {email}: {str(e)}")
        return False

def safe_notify_admins(db: Session, specialist_data: dict) -> bool:
    """Safely notify admins about new specialist registration"""
    try:
        admin_emails = get_admin_emails_for_notifications(db)
        
        if not admin_emails:
            print("No admin emails found for notifications")
            return False
        
        # Convert specialization enum to string safely
        specialization_str = safe_enum_to_string(specialist_data.get('specialization', ''))
        
        success_count = 0
        for admin_email in admin_emails:
            try:
                if send_admin_specialist_registration_notification(
                    admin_email=admin_email,
                    specialist_email=specialist_data['email'],
                    first_name=specialist_data['first_name'],
                    last_name=specialist_data['last_name'],
                    specialization=specialization_str,
                    registration_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ):
                    success_count += 1
            except Exception as e:
                print(f"Failed to notify admin {admin_email}: {str(e)}")
                continue
        
        return success_count > 0
    except Exception as e:
        print(f"Admin notification failed: {str(e)}")
        return False

# ============================================================================
# PATIENT REGISTRATION - FIXED WITH PROPER VERIFICATION FLOW
# ============================================================================

@router.post(
    "/register-patient", 
    response_model=PatientRegisterResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation or conflict error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def register_patient(
    request: PatientRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new patient with email verification (registration complete only after verification)"""
    try:
        # Check if email is already verified for this user type
        if check_verified_email_exists_for_user_type(db, request.email, USERTYPE.PATIENT):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered and verified as a patient"
            )
        
        # Check if email exists but is pending verification
        if check_pending_email_exists_for_user_type(db, request.email, USERTYPE.PATIENT):
            # Delete the existing pending registration to allow re-registration
            existing_patient = db.query(Patient).filter(
                Patient.email == request.email.lower(),
                Patient.is_deleted == False
            ).first()
            
            if existing_patient:
                # Delete auth info and preferences first due to foreign key constraints
                db.query(PatientAuthInfo).filter(
                    PatientAuthInfo.patient_id == existing_patient.id
                ).delete()
                
                db.query(PatientPreferences).filter(
                    PatientPreferences.patient_id == existing_patient.id
                ).delete()
                
                # Delete the patient record
                db.delete(existing_patient)
                db.flush()
        
        # Convert gender to enum safely
        gender_enum = convert_string_to_enum(request.gender, GenderEnum)
        
        # Create patient record (NOT VERIFIED YET)
        patient = Patient(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email.lower(),
            date_of_birth=request.date_of_birth,
            gender=gender_enum,
            city=request.city,
            user_type=USERTYPE.PATIENT,
            record_status=RecordStatusEnum.ACTIVE,
            accepts_terms_and_conditions=request.accepts_terms_and_conditions
        )
        db.add(patient)
        db.flush()
        
        # Generate OTP
        otp = generate_otp()
        otp_expiry = get_otp_expiry()
        
        # Create authentication info (UNVERIFIED)
        auth_info = PatientAuthInfo(
            patient_id=patient.id,
            hashed_password=hash_password(request.password),
            is_active=True,
            is_verified=False,  # KEY: Not verified until email verification
            otp=otp,
            otp_expiry=otp_expiry
        )
        db.add(auth_info)
        
        # Create default preferences
        preferences = create_default_patient_preferences(patient.id)
        db.add(preferences)
        
        # Commit transaction
        db.commit()
        
        # Send ONLY verification email (no completion email yet)
        verification_sent = safe_send_verification_email(
            request.email, otp, USERTYPE.PATIENT, request.first_name
        )
        
        if not verification_sent:
            # Log warning but don't fail registration
            print(f"Warning: Verification email failed to send to {request.email}")
        
        return PatientRegisterResponse(
            user_id=str(patient.id),
            email=request.email,
            full_name=f"{request.first_name} {request.last_name}",
            next_steps=[
                "Check your email for the 6-digit verification code",
                "Complete email verification to activate your account",
                "Login after verification is complete",
                "Complete your profile and preferences",
                "Start searching for mental health specialists"
            ]
        )
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as ve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(ve)}"
        )
    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration conflict - please try again"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# ============================================================================
# SPECIALIST REGISTRATION - FIXED WITH PROPER VERIFICATION FLOW
# ============================================================================

@router.post(
    "/register-specialist",
    response_model=SpecialistRegisterResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation or conflict error"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def register_specialist(
    request: SpecialistRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new specialist with email verification and admin approval (registration complete only after verification)"""
    try:
        # Check if email is already verified for this user type
        if check_verified_email_exists_for_user_type(db, request.email, USERTYPE.SPECIALIST):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered and verified as a specialist"
            )
        
        # Check if email exists but is pending verification
        if check_pending_email_exists_for_user_type(db, request.email, USERTYPE.SPECIALIST):
            # Delete the existing pending registration to allow re-registration
            existing_specialist = db.query(Specialists).filter(
                Specialists.email == request.email.lower(),
                Specialists.is_deleted == False
            ).first()
            
            if existing_specialist:
                # Delete related records first due to foreign key constraints
                db.query(SpecialistsAuthInfo).filter(
                    SpecialistsAuthInfo.specialist_id == existing_specialist.id
                ).delete()
                
                db.query(SpecialistsApprovalData).filter(
                    SpecialistsApprovalData.specialist_id == existing_specialist.id
                ).delete()
                
                # Delete the specialist record
                db.delete(existing_specialist)
                db.flush()
        
        # Convert enums safely
        gender_enum = convert_string_to_enum(request.gender, SpecialistGenderEnum)
        specialist_type_enum = convert_string_to_enum(request.specialist_type, SpecialistTypeEnum)
        
        # Create specialist record (NOT VERIFIED YET)
        specialist = Specialists(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email.lower(),
            phone=request.phone,
            gender=gender_enum,
            city=request.city,
            specialist_type=specialist_type_enum,
            years_experience=request.years_experience,
            availability_status=AvailabilityStatusEnum.NOT_ACCEPTING,
            approval_status=ApprovalStatusEnum.PENDING,
            accepts_terms_and_conditions=request.accepts_terms_and_conditions
        )
        db.add(specialist)
        db.flush()
        
        # Generate OTP
        otp = generate_otp()
        otp_expiry = get_otp_expiry()
        
        # Create authentication info (UNVERIFIED)
        auth_info = SpecialistsAuthInfo(
            specialist_id=specialist.id,
            hashed_password=hash_password(request.password),
            email_verification_status=EmailVerificationStatusEnum.PENDING,  # KEY: Not verified
            otp_code=otp,
            otp_expires_at=otp_expiry,
            user_type=USERTYPE.SPECIALIST
        )
        db.add(auth_info)
        
        # Create approval data record
        approval_data = SpecialistsApprovalData(
            specialist_id=specialist.id,
            license_number=request.license_number,
            submission_date=datetime.now(),
            background_check_status='pending'
        )
        db.add(approval_data)
        
        # Commit transaction
        db.commit()
        
        # Send ONLY verification email (no completion or admin notification emails yet)
        verification_sent = safe_send_verification_email(
            request.email, otp, USERTYPE.SPECIALIST, request.first_name
        )
        
        if not verification_sent:
            # Log warning but don't fail registration
            print(f"Warning: Verification email failed to send to {request.email}")
        
        return SpecialistRegisterResponse(
            message="Specialist registration successful",
            user_id=str(specialist.id),
            email=request.email,
            full_name=f"{request.first_name} {request.last_name}",
            next_steps=[
                "Check your email for the 6-digit verification code",
                "Complete email verification to activate your account",
                "Upload required documents for approval after verification", 
                "Wait for admin approval (typically 2-3 business days)",
                "Complete your profile setup once approved"
            ]
        )
        
    except HTTPException:
        db.rollback()
        raise
    except ValueError as ve:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(ve)}"
        )
    except IntegrityError as ie:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration conflict - please try again"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# ============================================================================
# HELPER FUNCTIONS FOR VERIFICATION COMPLETION (to be called after email verification)
# ============================================================================

def complete_patient_registration_after_verification(db: Session, patient: Patient) -> bool:
    """Complete patient registration after email verification - send completion email"""
    try:
        # Send completion email
        completion_sent = safe_send_completion_email(
            patient.email, 
            patient.first_name, 
            patient.last_name,
            None,  # No specialization for patients
            "patient"
        )
        
        if completion_sent:
            print(f"Patient registration completion email sent to {patient.email}")
        else:
            print(f"Warning: Failed to send completion email to {patient.email}")
        
        return True
    except Exception as e:
        print(f"Error completing patient registration for {patient.email}: {str(e)}")
        return False

def complete_specialist_registration_after_verification(db: Session, specialist: Specialists) -> bool:
    """Complete specialist registration after email verification - send completion and admin notification emails"""
    try:
        # Send completion email
        completion_sent = safe_send_completion_email(
            specialist.email, 
            specialist.first_name, 
            specialist.last_name,
            specialist.specialist_type,
            "specialist"
        )
        
        # Send admin notification
        admin_notified = safe_notify_admins(db, {
            'email': specialist.email,
            'first_name': specialist.first_name,
            'last_name': specialist.last_name,
            'specialization': specialist.specialist_type
        })
        
        if completion_sent:
            print(f"Specialist registration completion email sent to {specialist.email}")
        else:
            print(f"Warning: Failed to send completion email to {specialist.email}")
            
        if admin_notified:
            print(f"Admin notification sent for specialist {specialist.email}")
        else:
            print(f"Warning: Failed to send admin notification for {specialist.email}")
        
        return True
    except Exception as e:
        print(f"Error completing specialist registration for {specialist.email}: {str(e)}")
        return False

# ============================================================================
# SUPER ADMIN CREATION - UNCHANGED
# ============================================================================

@router.post(
    "/create-super-admin",
    response_model=AdminRegisterResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Super admin already exists"},
        500: {"model": ErrorResponse, "description": "Environment not configured"}
    }
)
async def create_super_admin(db: Session = Depends(get_db)):
    """Create super admin using environment credentials (one-time setup)"""
    try:
        # Validate environment configuration
        if not SUPER_ADMIN_EMAIL or not SUPER_ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Super admin credentials not configured in environment"
            )
        
        # Check if super admin already exists
        existing_super_admin = db.query(Admin).filter(
            Admin.role == AdminRoleEnum.SUPER_ADMIN,
            Admin.is_deleted == False
        ).first()
        
        if existing_super_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super admin already exists"
            )
        
        # Check if email exists as any user type
        if check_verified_email_exists_for_user_type(db, SUPER_ADMIN_EMAIL, USERTYPE.ADMIN):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Super admin email is already registered"
            )
        
        # Create super admin (directly active - no email verification needed)
        admin = Admin(
            first_name=SUPER_ADMIN_FIRST_NAME,
            last_name=SUPER_ADMIN_LAST_NAME,
            email=SUPER_ADMIN_EMAIL.lower(),
            role=AdminRoleEnum.SUPER_ADMIN,
            status=AdminStatusEnum.ACTIVE,
            security_key=PLATFORM_ADMIN_KEY,
            is_active=True,
            hashed_password=hash_password(SUPER_ADMIN_PASSWORD)
        )
        db.add(admin)
        db.commit()
        
        # Send notification email
        try:
            send_notification_email(
                to_email=SUPER_ADMIN_EMAIL,
                subject="Super Admin Account Created - MindMate Platform",
                content=f"""
                <h2>Super Admin Account Created</h2>
                <p>Dear {SUPER_ADMIN_FIRST_NAME} {SUPER_ADMIN_LAST_NAME},</p>
                <p>Your super admin account has been successfully created on the MindMate platform.</p>
                <p>You now have full administrative privileges including:</p>
                <ul>
                    <li>User management</li>
                    <li>System configuration</li>
                    <li>Admin management</li>
                    <li>Platform oversight</li>
                </ul>
                <p><strong>Login Email:</strong> {SUPER_ADMIN_EMAIL}</p>
                <p>Best regards,<br>MindMate Platform Team</p>
                """
            )
        except Exception as e:
            print(f"Admin notification email failed: {str(e)}")
        
        return AdminRegisterResponse(
            message="Super admin created successfully",
            user_id=str(admin.id),
            email=SUPER_ADMIN_EMAIL,
            full_name=f"{SUPER_ADMIN_FIRST_NAME} {SUPER_ADMIN_LAST_NAME}",
            role="super_admin",
            next_steps=[
                "Login with your credentials",
                "Configure platform settings",
                "Set up other admin accounts",
                "Review system status"
            ]
        )
        
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Super admin email is already registered"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Super admin creation failed: {str(e)}"
        )

# ============================================================================
# EXPORTS 
# ============================================================================

__all__ = [
    "router",
    "register_patient",
    "register_specialist", 
    "create_super_admin",
    "complete_patient_registration_after_verification",
    "complete_specialist_registration_after_verification"
]
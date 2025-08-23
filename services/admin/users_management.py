"""
Users Management Service for Approving, Rejecting, suspending, deactivating etc of specialists, patients, admins for now 

all methods will be in this file
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from datetime import datetime, timezone
import uuid
import logging

# Import models
from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, SpecialistsApprovalData, 
    SpecialistDocuments, SpecialistSpecializations,
    ApprovalStatusEnum, DocumentStatusEnum, AvailabilityStatusEnum,
    EmailVerificationStatusEnum
)
from models.sql_models.patient_models import (
    Patient, PatientAuthInfo, RecordStatusEnum
)

# Import schemas
from models.pydantic_models.users_management_schema import (
    SpecialistProfileResponse, SpecialistActionRequest, SpecialistActionResponse,
    PatientProfileResponse, PatientActionRequest, PatientActionResponse,
    ActionTypeEnum, UserTypeEnum
)

# Setup logging
logger = logging.getLogger(__name__)

class UsersManagementService:
    """Service for managing users (specialists, patients, admins)"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ============================================================================
    # 1. GET SPECIALIST PROFILE WITH DOCUMENTS
    # ============================================================================
    
    def get_specialist_profile_with_documents(self, specialist_id: uuid.UUID) -> Optional[SpecialistProfileResponse]:
        """
        Get complete specialist profile including all documents for approval/rejection
        """
        try:
            # Use the unified specialist profile service
            from services.specialists.specialist_profiles import SpecialistProfileService
            
            service = SpecialistProfileService(self.db)
            profile_data = service.create_specialist_protected_profile(specialist_id)
            
            if not profile_data:
                logger.warning(f"Specialist not found: {specialist_id}")
                return None
            
            # Convert to response model
            return SpecialistProfileResponse(**profile_data)
            
        except Exception as e:
            logger.error(f"Error getting specialist profile: {str(e)}")
            raise
    
    # ============================================================================
    # 2. APPROVE/REJECT/SUSPEND SPECIALIST
    # ============================================================================
    
    def approve_reject_specialist(
        self, 
        request: SpecialistActionRequest, 
        admin_id: uuid.UUID
    ) -> SpecialistActionResponse:
        """
        Approve, reject, or suspend a specialist with reason and admin notes
        """
        try:
            # Get specialist
            specialist = self.db.query(Specialists).filter(
                Specialists.id == request.specialist_id,
                Specialists.is_deleted == False
            ).first()
            
            if not specialist:
                raise ValueError(f"Specialist not found: {request.specialist_id}")
            
            previous_status = specialist.approval_status
            
            # Determine new status based on action
            if request.action == ActionTypeEnum.APPROVE:
                new_status = ApprovalStatusEnum.APPROVED
                message = "Specialist approved successfully"
            elif request.action == ActionTypeEnum.REJECT:
                new_status = ApprovalStatusEnum.REJECTED
                message = "Specialist rejected"
            elif request.action == ActionTypeEnum.SUSPEND:
                new_status = ApprovalStatusEnum.SUSPENDED
                message = "Specialist suspended"
            else:
                raise ValueError(f"Invalid action for specialist: {request.action}")
            
            # Update specialist status
            specialist.approval_status = new_status
            
            # Update approval data if exists
            if specialist.approval_data:
                specialist.approval_data.reviewed_by = admin_id
                specialist.approval_data.reviewed_at = datetime.now(timezone.utc)
                specialist.approval_data.approval_notes = request.admin_notes
                
                if request.action == ActionTypeEnum.REJECT:
                    specialist.approval_data.rejection_reason = request.reason
            
            # Log the action
            self._log_user_action(
                user_id=specialist.id,
                user_type=UserTypeEnum.SPECIALIST,
                action=request.action,
                previous_status=previous_status.value,
                new_status=new_status.value,
                reason=request.reason,
                admin_notes=request.admin_notes,
                performed_by=admin_id
            )
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Specialist {request.action.value}: {specialist.id} by admin {admin_id}")
            
            return SpecialistActionResponse(
                specialist_id=specialist.id,
                action=request.action,
                previous_status=previous_status,
                new_status=new_status,
                reason=request.reason,
                admin_notes=request.admin_notes,
                action_performed_by=admin_id,
                action_performed_at=datetime.now(timezone.utc),
                success=True,
                message=message
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error performing specialist action: {str(e)}")
            raise
    
    # ============================================================================
    # 3. ACTIVATE/DEACTIVATE PATIENT
    # ============================================================================
    
    def activate_deactivate_patient(
        self,
        request: PatientActionRequest,
        admin_id: uuid.UUID
    ) -> PatientActionResponse:
        """
        Activate, deactivate, or suspend a patient with reason and admin notes
        """
        try:
            # Get patient
            patient = self.db.query(Patient).filter(
                Patient.id == request.patient_id,
                Patient.is_deleted == False
            ).first()
            
            if not patient:
                raise ValueError(f"Patient not found: {request.patient_id}")
            
            previous_status = patient.record_status
            
            # Determine new status based on action
            if request.action == ActionTypeEnum.ACTIVATE:
                new_status = RecordStatusEnum.ACTIVE
                message = "Patient activated successfully"
            elif request.action == ActionTypeEnum.DEACTIVATE:
                new_status = RecordStatusEnum.INACTIVE
                message = "Patient deactivated"
            elif request.action == ActionTypeEnum.SUSPEND:
                new_status = RecordStatusEnum.INACTIVE  # Treat suspend as deactivate for patients
                message = "Patient suspended"
            elif request.action == ActionTypeEnum.UNSUSPEND:
                new_status = RecordStatusEnum.ACTIVE
                message = "Patient unsuspended"
            else:
                raise ValueError(f"Invalid action for patient: {request.action}")
            
            # Update patient status
            patient.record_status = new_status
            
            # Update auth info if exists
            if patient.auth_info:
                if request.action in [ActionTypeEnum.ACTIVATE, ActionTypeEnum.UNSUSPEND]:
                    patient.auth_info.is_active = True
                    patient.auth_info.is_locked = False
                elif request.action in [ActionTypeEnum.DEACTIVATE, ActionTypeEnum.SUSPEND]:
                    patient.auth_info.is_active = False
            
            # Log the action
            self._log_user_action(
                user_id=patient.id,
                user_type=UserTypeEnum.PATIENT,
                action=request.action,
                previous_status=previous_status.value,
                new_status=new_status.value,
                reason=request.reason,
                admin_notes=request.admin_notes,
                performed_by=admin_id
            )
            
            # Commit changes
            self.db.commit()
            
            logger.info(f"Patient {request.action.value}: {patient.id} by admin {admin_id}")
            
            return PatientActionResponse(
                patient_id=patient.id,
                action=request.action,
                previous_status=previous_status,
                new_status=new_status,
                reason=request.reason,
                admin_notes=request.admin_notes,
                action_performed_by=admin_id,
                action_performed_at=datetime.now(timezone.utc),
                success=True,
                message=message
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error performing patient action: {str(e)}")
            raise
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _log_user_action(
        self,
        user_id: uuid.UUID,
        user_type: UserTypeEnum,
        action: ActionTypeEnum,
        previous_status: str,
        new_status: str,
        reason: str,
        admin_notes: Optional[str],
        performed_by: uuid.UUID
    ) -> None:
        """Log user management actions for audit trail"""
        try:
            # This would typically save to a separate audit log table
            # For now, we'll just log it
            log_entry = {
                "user_id": user_id,
                "user_type": user_type.value,
                "action": action.value,
                "previous_status": previous_status,
                "new_status": new_status,
                "reason": reason,
                "admin_notes": admin_notes,
                "performed_by": performed_by,
                "performed_at": datetime.now(timezone.utc)
            }
            
            logger.info(f"User management action logged: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging user action: {str(e)}")
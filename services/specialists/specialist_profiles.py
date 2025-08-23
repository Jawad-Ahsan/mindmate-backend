"""
Specialist Profile Service
=========================
Unified service for retrieving specialist profiles with different access levels:
- Public: Accessible to patients (basic info, specializations, ratings)
- Protected: Accessible to admins (complete profile with documents and approval data)
- Private: Accessible to specialist only (personal details and account info)
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, desc
from datetime import datetime, timezone
import uuid
import logging

from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, SpecialistsApprovalData,
    SpecialistDocuments, SpecialistSpecializations,
    DocumentTypeEnum, DocumentStatusEnum, ApprovalStatusEnum,
    EmailVerificationStatusEnum
)

# Setup logging
logger = logging.getLogger(__name__)

class SpecialistProfileService:
    """Service class for managing specialist profiles with different access levels"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_specialist_with_relations(self, specialist_id: uuid.UUID, load_relations: List[str] = None) -> Optional[Specialists]:
        """Get specialist with specified relations loaded"""
        query = self.db.query(Specialists).filter(
            Specialists.id == specialist_id,
            Specialists.is_deleted == False
        )
        
        if load_relations:
            for relation in load_relations:
                query = query.options(selectinload(getattr(Specialists, relation)))
        
        return query.first()
    
    def create_specialist_public_profile(self, specialist_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Create public specialist profile accessible to patients
        Includes: basic info, specializations, ratings, availability
        """
        try:
            # Load specialist with required relations
            specialist = self._get_specialist_with_relations(
                specialist_id, 
                ['auth_info', 'specializations']
            )
            
            if not specialist:
                logger.warning(f"Specialist not found: {specialist_id}")
                return None
            
            # Check if specialist is approved and email verified
            if (specialist.approval_status != ApprovalStatusEnum.APPROVED or 
                not specialist.auth_info or 
                not specialist.auth_info.is_email_verified):
                logger.warning(f"Specialist {specialist_id} not approved or email not verified")
                return None
            
            # Build specializations
            specializations = []
            for spec in specialist.specializations:
                specializations.append({
                    "specialization": spec.specialization.value,
                    "years_experience": spec.years_of_experience_in_specialization,
                    "is_primary": spec.is_primary_specialization
                })
            
            primary_specialization = next(
                (spec.specialization.value for spec in specialist.specializations if spec.is_primary_specialization),
                None
            )
            
            return {
                "specialist_id": str(specialist.id),
                "full_name": specialist.full_name,
                "specialist_type": specialist.specialist_type.value,
                "years_experience": specialist.years_experience,
                "bio": specialist.bio,
                "consultation_fee": float(specialist.consultation_fee) if specialist.consultation_fee else None,
                "languages_spoken": specialist.languages_spoken or [],
                "city": specialist.city,
                "clinic_name": specialist.clinic_name,
                "profile_image_url": specialist.profile_image_url,
                "website_url": specialist.website_url,
                "availability_status": specialist.availability_status.value,
                "average_rating": float(specialist.average_rating) if specialist.average_rating else 0.0,
                "total_reviews": specialist.total_reviews,
                "total_appointments": specialist.total_appointments,
                "specializations": specializations,
                "primary_specialization": primary_specialization,
                "can_practice": specialist.can_practice,
                "profile_complete": bool(specialist.bio and specialist.consultation_fee and specialist.address)
            }
            
        except Exception as e:
            logger.error(f"Error creating public specialist profile: {str(e)}")
            return None
    
    def create_specialist_protected_profile(self, specialist_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Create protected specialist profile accessible to admins only
        Includes: complete profile with documents and approval data
        """
        try:
            # Load specialist with all relations
            specialist = self._get_specialist_with_relations(
                specialist_id, 
                ['auth_info', 'approval_data', 'specializations']
            )
            
            if not specialist:
                logger.warning(f"Specialist not found: {specialist_id}")
                return None
            
            # Build specializations
            specializations = []
            for spec in specialist.specializations:
                specializations.append({
                    "specialization": spec.specialization.value,
                    "years_experience": spec.years_of_experience_in_specialization,
                    "certification_date": spec.certification_date.isoformat() if spec.certification_date else None,
                    "is_primary": spec.is_primary_specialization
                })
            
            primary_specialization = next(
                (spec.specialization.value for spec in specialist.specializations if spec.is_primary_specialization),
                None
            )
            
            # Build documents
            documents = []
            if specialist.approval_data:
                for doc in specialist.approval_data.documents:
                    documents.append({
                        "document_id": str(doc.id),
                        "document_type": doc.document_type.value,
                        "document_name": doc.document_name,
                        "file_path": doc.file_path,
                        "file_size": doc.file_size,
                        "file_size_mb": doc.file_size_mb,
                        "mime_type": doc.mime_type,
                        "verification_status": doc.verification_status.value,
                        "verified_by": str(doc.verified_by) if doc.verified_by else None,
                        "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
                        "verification_notes": doc.verification_notes,
                        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                        "is_expired": doc.is_expired,
                        "is_verified": doc.is_verified
                    })
            
            # Build auth info
            auth_info = None
            if specialist.auth_info:
                auth_info = {
                    "email_verification_status": specialist.auth_info.email_verification_status.value if specialist.auth_info.email_verification_status else None,
                    "email_verified_at": specialist.auth_info.email_verified_at.isoformat() if specialist.auth_info.email_verified_at else None,
                    "last_login_at": specialist.auth_info.last_login_at.isoformat() if specialist.auth_info.last_login_at else None,
                    "failed_login_attempts": specialist.auth_info.failed_login_attempts if specialist.auth_info else 0,
                    "is_locked": specialist.auth_info.is_locked if specialist.auth_info else False,
                    "two_factor_enabled": specialist.auth_info.two_factor_enabled if specialist.auth_info else False
                }
            
            # Build approval data
            approval_data = None
            if specialist.approval_data:
                approval_data = {
                    "license_number": specialist.approval_data.license_number,
                    "license_issuing_authority": specialist.approval_data.license_issuing_authority,
                    "license_issue_date": specialist.approval_data.license_issue_date.isoformat() if specialist.approval_data.license_issue_date else None,
                    "license_expiry_date": specialist.approval_data.license_expiry_date.isoformat() if specialist.approval_data.license_expiry_date else None,
                    "is_license_valid": specialist.approval_data.is_license_valid,
                    "highest_degree": specialist.approval_data.highest_degree,
                    "university_name": specialist.approval_data.university_name,
                    "graduation_year": specialist.approval_data.graduation_year,
                    "cnic": specialist.approval_data.cnic,
                    "passport_number": specialist.approval_data.passport_number,
                    "professional_memberships": specialist.approval_data.professional_memberships if specialist.approval_data else [],
                    "certifications": specialist.approval_data.certifications if specialist.approval_data else [],
                    "submission_date": specialist.approval_data.submission_date.isoformat() if specialist.approval_data.submission_date else None,
                    "reviewed_by": str(specialist.approval_data.reviewed_by) if specialist.approval_data.reviewed_by else None,
                    "reviewed_at": specialist.approval_data.reviewed_at.isoformat() if specialist.approval_data.reviewed_at else None,
                    "approval_notes": specialist.approval_data.approval_notes,
                    "rejection_reason": specialist.approval_data.rejection_reason,
                    "days_since_submission": specialist.approval_data.days_since_submission if specialist.approval_data else None,
                    "background_check_status": specialist.approval_data.background_check_status,
                    "background_check_date": specialist.approval_data.background_check_date.isoformat() if specialist.approval_data.background_check_date else None,
                    "background_check_notes": specialist.approval_data.background_check_notes,
                    "ethics_declaration_signed": specialist.approval_data.ethics_declaration_signed if specialist.approval_data else False,
                    "ethics_declaration_text": specialist.approval_data.ethics_declaration_text
                }
            
            # Calculate document stats
            document_stats = {
                "total_documents": len(documents),
                "documents_approved": len([d for d in documents if d["verification_status"] == DocumentStatusEnum.APPROVED.value]),
                "documents_pending": len([d for d in documents if d["verification_status"] == DocumentStatusEnum.PENDING.value]),
                "documents_rejected": len([d for d in documents if d["verification_status"] == DocumentStatusEnum.REJECTED.value]),
                "documents_needs_resubmission": len([d for d in documents if d["verification_status"] == DocumentStatusEnum.NEEDS_RESUBMISSION.value]),
                "expired_documents": len([d for d in documents if d["is_expired"]])
            }
            
            # Calculate profile completeness
            profile_completeness = self._calculate_profile_completion(specialist, specialist.specializations, documents)
            
            return {
                "specialist_id": str(specialist.id),
                "full_name": specialist.full_name,
                "first_name": specialist.first_name,
                "last_name": specialist.last_name,
                "email": specialist.email,
                "phone": specialist.phone,
                "date_of_birth": specialist.date_of_birth.isoformat() if specialist.date_of_birth else None,
                "gender": specialist.gender.value if specialist.gender else None,
                "specialist_type": specialist.specialist_type.value,
                "years_experience": specialist.years_experience,
                "bio": specialist.bio,
                "consultation_fee": float(specialist.consultation_fee) if specialist.consultation_fee else None,
                "languages_spoken": specialist.languages_spoken or [],
                "city": specialist.city,
                "address": specialist.address,
                "clinic_name": specialist.clinic_name,
                "website_url": specialist.website_url,
                "profile_image_url": specialist.profile_image_url,
                "social_media_links": specialist.social_media_links,
                "availability_status": specialist.availability_status.value,
                "approval_status": specialist.approval_status.value,
                "average_rating": float(specialist.average_rating) if specialist.average_rating else 0.0,
                "total_reviews": specialist.total_reviews,
                "total_appointments": specialist.total_appointments,
                "can_practice": specialist.can_practice,
                "auth_info": auth_info,
                "specializations": specializations,
                "primary_specialization": primary_specialization,
                "approval_data": approval_data,
                "documents": documents,
                "document_stats": document_stats,
                "profile_completeness": profile_completeness,
                "created_at": specialist.created_at.isoformat() if specialist.created_at else None,
                "updated_at": specialist.updated_at.isoformat() if specialist.updated_at else None,
                "accepts_terms_and_conditions": specialist.accepts_terms_and_conditions
            }
            
        except Exception as e:
            logger.error(f"Error creating protected specialist profile: {str(e)}")
            return None
    
    def create_specialist_private_profile(self, specialist_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Create private specialist profile accessible to specialist only
        Includes: complete personal details and account information
        """
        try:
            # Load specialist with all relations
            specialist = self._get_specialist_with_relations(
                specialist_id, 
                ['auth_info', 'approval_data', 'specializations']
            )
            
            if not specialist:
                logger.warning(f"Specialist not found: {specialist_id}")
                return None
            
            # Build specializations
            specializations = []
            for spec in specialist.specializations:
                specializations.append({
                    "specialization": spec.specialization.value,
                    "years_experience": spec.years_of_experience_in_specialization,
                    "certification_date": spec.certification_date.isoformat() if spec.certification_date else None,
                    "is_primary": spec.is_primary_specialization
                })
            
            primary_specialization = next(
                (spec.specialization.value for spec in specialist.specializations if spec.is_primary_specialization),
                None
            )
            
            # Build documents
            documents = []
            if specialist.approval_data:
                for doc in specialist.approval_data.documents:
                    documents.append({
                        "document_id": str(doc.id),
                        "document_type": doc.document_type.value,
                        "document_name": doc.document_name,
                        "file_path": doc.file_path,
                        "file_size": doc.file_size,
                        "file_size_mb": doc.file_size_mb,
                        "mime_type": doc.mime_type,
                        "verification_status": doc.verification_status.value,
                        "verified_by": str(doc.verified_by) if doc.verified_by else None,
                        "verified_at": doc.verified_at.isoformat() if doc.verified_at else None,
                        "verification_notes": doc.verification_notes,
                        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
                        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                        "is_expired": doc.is_expired,
                        "is_verified": doc.is_verified
                    })
            
            # Build auth info
            auth_info = None
            if specialist.auth_info:
                auth_info = {
                    "is_active": specialist.auth_info.is_active,
                    "is_email_verified": specialist.auth_info.is_email_verified,
                    "is_locked": specialist.auth_info.is_locked,
                    "last_login": specialist.auth_info.last_login_at.isoformat() if specialist.auth_info.last_login_at else None,
                    "failed_login_attempts": specialist.auth_info.failed_login_attempts if specialist.auth_info else 0,
                    "two_factor_enabled": specialist.auth_info.two_factor_enabled if specialist.auth_info else False
                }
            
            # Build approval data
            approval_data = None
            if specialist.approval_data:
                approval_data = {
                    "license_number": specialist.approval_data.license_number,
                    "license_issuing_authority": specialist.approval_data.license_issuing_authority,
                    "license_issue_date": specialist.approval_data.license_issue_date.isoformat() if specialist.approval_data.license_issue_date else None,
                    "license_expiry_date": specialist.approval_data.license_expiry_date.isoformat() if specialist.approval_data.license_expiry_date else None,
                    "is_license_valid": specialist.approval_data.is_license_valid,
                    "highest_degree": specialist.approval_data.highest_degree,
                    "university_name": specialist.approval_data.university_name,
                    "graduation_year": specialist.approval_data.graduation_year,
                    "cnic": specialist.approval_data.cnic,
                    "passport_number": specialist.approval_data.passport_number,
                    "professional_memberships": specialist.approval_data.professional_memberships if specialist.approval_data else [],
                    "certifications": specialist.approval_data.certifications if specialist.approval_data else [],
                    "submission_date": specialist.approval_data.submission_date.isoformat() if specialist.approval_data.submission_date else None,
                    "reviewed_by": str(specialist.approval_data.reviewed_by) if specialist.approval_data.reviewed_by else None,
                    "reviewed_at": specialist.approval_data.reviewed_at.isoformat() if specialist.approval_data.reviewed_at else None,
                    "approval_notes": specialist.approval_data.approval_notes,
                    "rejection_reason": specialist.approval_data.rejection_reason,
                    "background_check_status": specialist.approval_data.background_check_status,
                    "background_check_date": specialist.approval_data.background_check_date.isoformat() if specialist.approval_data.background_check_date else None,
                    "background_check_notes": specialist.approval_data.background_check_notes,
                    "ethics_declaration_signed": specialist.approval_data.ethics_declaration_signed if specialist.approval_data else False,
                    "ethics_declaration_text": specialist.approval_data.ethics_declaration_text
                }
            
            # Calculate profile completion
            profile_completion = self._calculate_profile_completion(specialist, specialist.specializations, documents)
            
            return {
                "specialist_id": str(specialist.id),
                "first_name": specialist.first_name,
                "last_name": specialist.last_name,
                "full_name": specialist.full_name,
                "date_of_birth": specialist.date_of_birth.isoformat() if specialist.date_of_birth else None,
                "gender": specialist.gender.value if specialist.gender else None,
                "email": specialist.email,
                "phone": specialist.phone,
                "city": specialist.city,
                "address": specialist.address,
                "specialist_type": specialist.specialist_type.value,
                "years_experience": specialist.years_experience,
                "bio": specialist.bio,
                "consultation_fee": float(specialist.consultation_fee) if specialist.consultation_fee else None,
                "languages_spoken": specialist.languages_spoken or [],
                "clinic_name": specialist.clinic_name,
                "profile_image_url": specialist.profile_image_url,
                "website_url": specialist.website_url,
                "social_media_links": specialist.social_media_links,
                "availability_status": specialist.availability_status.value,
                "approval_status": specialist.approval_status.value,
                "average_rating": float(specialist.average_rating) if specialist.average_rating else 0.0,
                "total_reviews": specialist.total_reviews,
                "total_appointments": specialist.total_appointments,
                "specializations": specializations,
                "primary_specialization": primary_specialization,
                "auth_info": auth_info,
                "approval_data": approval_data,
                "documents": documents,
                "can_practice": specialist.can_practice,
                "created_at": specialist.created_at.isoformat() if specialist.created_at else None,
                "updated_at": specialist.updated_at.isoformat() if specialist.updated_at else None,
                "accepts_terms_and_conditions": specialist.accepts_terms_and_conditions,
                "profile_completion_percentage": profile_completion
            }
            
        except Exception as e:
            logger.error(f"Error creating private specialist profile: {str(e)}")
            return None
    
    def _calculate_profile_completion(self, specialist: Specialists, specializations: List[SpecialistSpecializations], documents: List[Dict]) -> float:
        """Calculate overall profile completion percentage"""
        total_sections = 6  # Basic info, bio, specializations, documents, contact, approval
        completed_sections = 1  # Basic info is always complete if specialist exists
        
        # Check bio completion
        if specialist.bio:
            completed_sections += 1
        
        # Check consultation fee
        if specialist.consultation_fee:
            completed_sections += 0.5
        
        # Check specializations
        if specializations:
            completed_sections += 1
        
        # Check documents
        if documents:
            completed_sections += 1
        
        # Check contact info
        if specialist.email and specialist.phone:
            completed_sections += 1
        
        # Check approval data
        if specialist.approval_data:
            completed_sections += 0.5
        
        return min((completed_sections / total_sections) * 100, 100.0)
    
    def get_specialists_for_admin_review(
        self, 
        status: Optional[str] = None, 
        city: Optional[str] = None, 
        specialist_type: Optional[str] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get list of specialists for admin review with filtering"""
        try:
            query = self.db.query(Specialists).filter(Specialists.is_deleted == False)
            
            if status:
                query = query.filter(Specialists.approval_status == status)
            if city:
                query = query.filter(Specialists.city.ilike(f"%{city}%"))
            if specialist_type:
                query = query.filter(Specialists.specialist_type == specialist_type)
            
            total_count = query.count()
            specialists = query.offset(offset).limit(limit).all()
            
            specialists_list = []
            for specialist in specialists:
                approval_data = self.db.query(SpecialistsApprovalData).filter(
                    SpecialistsApprovalData.specialist_id == specialist.id
                ).first()
                
                document_count = 0
                if approval_data:
                    document_count = self.db.query(SpecialistDocuments).filter(
                        SpecialistDocuments.approval_data_id == approval_data.id
                    ).count()
                
                specialist_data = {
                    "specialist_id": str(specialist.id),
                    "full_name": specialist.full_name,
                    "email": specialist.email,
                    "phone": specialist.phone,
                    "specialist_type": specialist.specialist_type.value,
                    "city": specialist.city,
                    "approval_status": specialist.approval_status.value,
                    "submission_date": approval_data.submission_date.isoformat() if approval_data and approval_data.submission_date else None,
                    "days_since_submission": approval_data.days_since_submission if approval_data else None,
                    "total_documents": document_count,
                    "ethics_declaration_signed": approval_data.ethics_declaration_signed if approval_data else False,
                    "profile_complete": bool(specialist.bio and specialist.consultation_fee and specialist.address),
                    "created_at": specialist.created_at.isoformat() if specialist.created_at else None
                }
                specialists_list.append(specialist_data)
            
            return {
                "specialists": specialists_list,
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
            
        except Exception as e:
            logger.error(f"Error getting specialists for admin review: {str(e)}")
            return {
                "specialists": [],
                "total_count": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False
            }


# Utility functions for creating profile responses

def create_specialist_public_profile_response(
    db: Session, 
    specialist_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    """Create a public profile response"""
    service = SpecialistProfileService(db)
    profile = service.create_specialist_public_profile(specialist_id)
    
    if not profile:
        return None
    
    return {
        "success": True,
        "message": "Public profile retrieved successfully",
        "data": profile,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def create_specialist_protected_profile_response(
    db: Session, 
    specialist_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    """Create a protected profile response"""
    service = SpecialistProfileService(db)
    profile = service.create_specialist_protected_profile(specialist_id)
    
    if not profile:
        return None
    
    return {
        "success": True,
        "message": "Protected profile retrieved successfully",
        "data": profile,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def create_specialist_private_profile_response(
    db: Session, 
    specialist_id: uuid.UUID
) -> Optional[Dict[str, Any]]:
    """Create a private profile response"""
    service = SpecialistProfileService(db)
    profile = service.create_specialist_private_profile(specialist_id)
    
    if not profile:
        return None
    
    return {
        "success": True,
        "message": "Private profile retrieved successfully", 
        "data": profile,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Export all functions
__all__ = [
    'SpecialistProfileService',
    'create_specialist_public_profile_response',
    'create_specialist_protected_profile_response',
    'create_specialist_private_profile_response'
]

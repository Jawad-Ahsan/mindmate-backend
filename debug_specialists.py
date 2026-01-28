from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.getcwd())

from core.config import settings
from models.sql_models.specialist_models import Specialists, SpecialistsAuthInfo, SpecialistsApprovalData

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict
import mimetypes

# Mocking Pydantic models from admin.py
class SpecialistResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None
    address: str | None
    city: str | None
    clinic_name: str | None
    bio: str | None
    consultation_fee: Decimal | None
    languages_spoken: List[str] | None
    website_url: str | None
    social_media_links: Dict[str, str] | None
    specialist_type: str | None
    years_experience: int | None
    approval_status: str
    created_at: datetime
    last_login: datetime | None
    specializations: List[Dict[str, Any]] | None = None
    documents: List[Dict[str, Any]] | None = None
    availability_slots: List[str] | None = None
    profile_completion_percentage: float | None = None
    submission_date: datetime | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v else None
        }
    )

from models.sql_models.specialist_models import (
    Specialists, SpecialistsAuthInfo, SpecialistsApprovalData, 
    SpecialistSpecializations, SpecialistDocuments, SpecialistAvailability,
    TimeSlotEnum, ApprovalStatusEnum
)

def calculate_profile_completion_for_admin(specialist, specializations, availability_slots, documents):
    return 50.0 # simplified for debug

def safe_enum_to_string(enum_value) -> str:
    if enum_value is None:
        return "Unknown"
    if hasattr(enum_value, 'value'):
        return str(enum_value.value)
    return str(enum_value)

def check_specialist_data():
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        specialists = db.query(Specialists).filter(Specialists.is_deleted == False).all()
        print(f"Total Specialists found: {len(specialists)}")
        
        result = []
        for specialist in specialists:
            print(f"\nProcessing Specialist: {specialist.email}")
            try:
                auth_info = db.query(SpecialistsAuthInfo).filter(
                    SpecialistsAuthInfo.specialist_id == specialist.id
                ).first()
                
                specializations = db.query(SpecialistSpecializations).filter(
                    SpecialistSpecializations.specialist_id == specialist.id
                ).all()
                
                approval_data = db.query(SpecialistsApprovalData).filter(
                    SpecialistsApprovalData.specialist_id == specialist.id
                ).first()
                
                documents = []
                if approval_data:
                    docs = db.query(SpecialistDocuments).filter(
                        SpecialistDocuments.approval_data_id == approval_data.id
                    ).all()
                    documents = [
                        {
                            "id": str(doc.id),
                            "document_name": doc.document_name,
                            "document_type": getattr(doc.document_type, 'value', None) if doc.document_type else None,
                            "verification_status": getattr(doc.verification_status, 'value', None) if doc.verification_status else None,
                            "upload_date": doc.upload_date,
                            "expiry_date": doc.expiry_date,
                            "file_size": doc.file_size,
                            "mime_type": doc.mime_type
                        }
                        for doc in docs
                    ]
                
                availability_slots = db.query(SpecialistAvailability).filter(
                    SpecialistAvailability.specialist_id == specialist.id
                ).all()
                availability_list = [getattr(slot.time_slot, 'value', str(slot.time_slot)) for slot in availability_slots] if availability_slots else []
                
                profile_completion = calculate_profile_completion_for_admin(specialist, specializations, availability_slots, documents)
                
                submission_date = None
                if specialist.approval_status == ApprovalStatusEnum.UNDER_REVIEW and approval_data:
                    submission_date = approval_data.updated_at
                
                data = {
                    "id": str(specialist.id),
                    "email": specialist.email,
                    "full_name": f"{specialist.first_name} {specialist.last_name}",
                    "phone": specialist.phone,
                    "address": specialist.address,
                    "city": specialist.city,
                    "clinic_name": specialist.clinic_name,
                    "bio": specialist.bio,
                    "consultation_fee": specialist.consultation_fee,
                    "languages_spoken": specialist.languages_spoken,
                    "website_url": specialist.website_url,
                    "social_media_links": specialist.social_media_links,
                    "specialist_type": getattr(specialist.specialist_type, 'value', None) if specialist.specialist_type else None,
                    "years_experience": specialist.years_experience,
                    "approval_status": getattr(specialist.approval_status, 'value', "pending") if specialist.approval_status else "pending",
                    "created_at": specialist.created_at,
                    "last_login": auth_info.last_login_at if auth_info else None,
                    "specializations": [
                        {
                            "specialization": getattr(spec.specialization, 'value', None) if spec.specialization else None,
                            "years_of_experience_in_specialization": spec.years_of_experience_in_specialization,
                            "is_primary_specialization": spec.is_primary_specialization,
                            "certification_date": spec.certification_date
                        }
                        for spec in specializations
                    ] if specializations else None,
                    "documents": documents,
                    "availability_slots": availability_list,
                    "profile_completion_percentage": profile_completion,
                    "submission_date": submission_date
                }
                
                print("Data constructed. Validating with Pydantic...")
                resp = SpecialistResponse(**data)
                print("Pydantic Validation Passed!")
                result.append(resp)
                
            except Exception as inner_e:
                print(f"FAILED to process specialist {specialist.email}: {inner_e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_specialist_data()

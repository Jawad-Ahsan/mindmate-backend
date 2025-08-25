from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database.database import get_db
from routers.authentication.authenticate import (
	get_current_user_from_token,
)
from models.sql_models.patient_models import Patient
from models.sql_models.questionnaire_models import MandatoryQuestionnaireSubmission
from models.sql_models.specialist_models import Specialists, SpecialistsApprovalData, SpecialistSpecializations, SpecialistAvailability

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me")
async def get_me(current_user_data: dict = Depends(get_current_user_from_token)):
	user = current_user_data["user"]
	user_type = current_user_data["user_type"]
	auth_info = current_user_data.get("auth_info")

	base = {
		"user_id": str(user.id),
		"email": user.email,
		"first_name": user.first_name,
		"last_name": user.last_name,
		"full_name": f"{user.first_name} {user.last_name}",
		"user_type": user_type,
	}

	if user_type == "patient":
		base.update({
			"verification_status": "verified" if getattr(auth_info, "is_verified", False) else "pending",
			"last_login": getattr(auth_info, "last_login", None),
		})
	elif user_type == "specialist":
		from models.sql_models.specialist_models import ApprovalStatusEnum
		verification = getattr(auth_info, "email_verification_status", None)
		approval = getattr(user, "approval_status", None)
		base.update({
			"verification_status": str(getattr(verification, "value", verification)) if verification else "unknown",
			"approval_status": str(getattr(approval, "value", approval)) if approval else "unknown",
			"last_login": getattr(auth_info, "last_login", None),
		})
	else:
		base.update({
			"verification_status": "verified",
			"last_login": getattr(user, "last_login", None),
		})

	return base


@router.get("/patient/profile")
async def get_patient_profile(
	current_user_data: dict = Depends(get_current_user_from_token),
	db: Session = Depends(get_db)
):
	"""Get complete patient profile data including questionnaire responses"""
	user = current_user_data["user"]
	user_type = current_user_data["user_type"]
	
	if user_type != "patient":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can access this endpoint")
	
	try:
		# Get patient data
		patient = db.query(Patient).filter(Patient.id == user.id).first()
		if not patient:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
		
		# Get questionnaire data
		questionnaire = db.query(MandatoryQuestionnaireSubmission).filter(
			MandatoryQuestionnaireSubmission.patient_id == user.id
		).first()
		
		# Build profile response
		profile_data = {
			"patient": {
				"id": str(patient.id),
				"first_name": patient.first_name,
				"last_name": patient.last_name,
				"full_name": patient.full_name,
				"email": patient.email,
				"phone": patient.phone,
				"date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
				"age": patient.age,
				"gender": patient.gender.value if patient.gender else None,
				"city": patient.city,
				"district": patient.district,
				"province": patient.province,
				"country": patient.country,
				"postal_code": patient.postal_code,
				"primary_language": patient.primary_language.value if patient.primary_language else None,
				"record_status": patient.record_status.value if patient.record_status else None,
				"intake_completed_date": patient.intake_completed_date.isoformat() if patient.intake_completed_date else None,
				"last_contact_date": patient.last_contact_date.isoformat() if patient.last_contact_date else None,
				"next_appointment_date": patient.next_appointment_date.isoformat() if patient.next_appointment_date else None,
				"accepts_terms_and_conditions": patient.accepts_terms_and_conditions
			},
			"questionnaire": questionnaire.to_dict() if questionnaire else None
		}
		
		return profile_data
		
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching patient profile: {str(e)}")


@router.put("/patient/profile")
async def update_patient_profile(
	profile_data: dict,
	current_user_data: dict = Depends(get_current_user_from_token),
	db: Session = Depends(get_db)
):
	"""Update patient profile data"""
	user = current_user_data["user"]
	user_type = current_user_data["user_type"]
	
	if user_type != "patient":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can access this endpoint")
	
	try:
		# Get patient
		patient = db.query(Patient).filter(Patient.id == user.id).first()
		if not patient:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
		
		# Update patient fields if provided
		if "patient" in profile_data:
			patient_data = profile_data["patient"]
			for field, value in patient_data.items():
				if hasattr(patient, field) and value is not None:
					setattr(patient, field, value)
		
		# Update questionnaire if provided
		if "questionnaire" in profile_data and profile_data["questionnaire"]:
			questionnaire = db.query(MandatoryQuestionnaireSubmission).filter(
				MandatoryQuestionnaireSubmission.patient_id == user.id
			).first()
			
			if questionnaire:
				# Update existing questionnaire
				q_data = profile_data["questionnaire"]
				for field, value in q_data.items():
					if hasattr(questionnaire, field) and value is not None:
						setattr(questionnaire, field, value)
			else:
				# Create new questionnaire if doesn't exist
				q_data = profile_data["questionnaire"]
				questionnaire = MandatoryQuestionnaireSubmission(
					patient_id=user.id,
					full_name=q_data.get("full_name", patient.full_name),
					age=q_data.get("age", str(patient.age)),
					gender=q_data.get("gender", patient.gender.value if patient.gender else None),
					chief_complaint=q_data.get("chief_complaint", ""),
					past_psychiatric_diagnosis=q_data.get("past_psychiatric_diagnosis"),
					past_psychiatric_treatment=q_data.get("past_psychiatric_treatment"),
					hospitalizations=q_data.get("hospitalizations"),
					ect_history=q_data.get("ect_history"),
					current_medications=q_data.get("current_medications"),
					medication_allergies=q_data.get("medication_allergies"),
					otc_supplements=q_data.get("otc_supplements"),
					medication_adherence=q_data.get("medication_adherence"),
					medical_history_summary=q_data.get("medical_history_summary"),
					chronic_illnesses=q_data.get("chronic_illnesses"),
					neurological_problems=q_data.get("neurological_problems"),
					head_injury=q_data.get("head_injury"),
					seizure_history=q_data.get("seizure_history"),
					pregnancy_status=q_data.get("pregnancy_status"),
					alcohol_use=q_data.get("alcohol_use"),
					drug_use=q_data.get("drug_use"),
					prescription_drug_abuse=q_data.get("prescription_drug_abuse"),
					last_use_date=q_data.get("last_use_date"),
					substance_treatment=q_data.get("substance_treatment"),
					tobacco_use=q_data.get("tobacco_use"),
					family_mental_health_history=q_data.get("family_mental_health_history"),
					family_mental_health_stigma=q_data.get("family_mental_health_stigma"),
					cultural_background=q_data.get("cultural_background"),
					cultural_beliefs=q_data.get("cultural_beliefs"),
					spiritual_supports=q_data.get("spiritual_supports"),
					lifestyle_smoking=q_data.get("lifestyle_smoking"),
					lifestyle_alcohol=q_data.get("lifestyle_alcohol"),
					lifestyle_activity=q_data.get("lifestyle_activity"),
					is_complete=True
				)
				db.add(questionnaire)
		
		db.commit()
		
		return {"success": True, "message": "Profile updated successfully"}
		
	except Exception as e:
		db.rollback()
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating patient profile: {str(e)}")


@router.get("/specialist/profile")
async def get_specialist_profile(
	current_user_data: dict = Depends(get_current_user_from_token),
	db: Session = Depends(get_db)
):
	"""Get complete specialist profile data"""
	user = current_user_data["user"]
	user_type = current_user_data["user_type"]
	
	if user_type != "specialist":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only specialists can access this endpoint")
	
	try:
		# Get specialist data
		specialist = db.query(Specialists).filter(Specialists.id == user.id).first()
		if not specialist:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialist not found")
		
		# Get approval data
		approval_data = db.query(SpecialistsApprovalData).filter(
			SpecialistsApprovalData.specialist_id == user.id
		).first()
		
		# Get specializations
		specializations = db.query(SpecialistSpecializations).filter(
			SpecialistSpecializations.specialist_id == user.id
		).all()
		
		# Get availability slots
		availability_slots = db.query(SpecialistAvailability).filter(
			SpecialistAvailability.specialist_id == user.id,
			SpecialistAvailability.is_active == True
		).all()
		
		# Build profile response
		profile_data = {
			"specialist": {
				"id": str(specialist.id),
				"first_name": specialist.first_name,
				"last_name": specialist.last_name,
				"full_name": specialist.full_name,
				"email": specialist.email,
				"phone": specialist.phone,
				"date_of_birth": specialist.date_of_birth.isoformat() if specialist.date_of_birth else None,
				"gender": specialist.gender.value if specialist.gender else None,
				"city": specialist.city,
				"address": specialist.address,
				"clinic_name": specialist.clinic_name,
				"specialist_type": specialist.specialist_type.value if specialist.specialist_type else None,
				"years_experience": specialist.years_experience,
				"consultation_fee": float(specialist.consultation_fee) if specialist.consultation_fee else None,
				"bio": specialist.bio,
				"languages_spoken": specialist.languages_spoken,
				"availability_status": specialist.availability_status.value if specialist.availability_status else None,
				"approval_status": specialist.approval_status.value if specialist.approval_status else None,
				"average_rating": float(specialist.average_rating) if specialist.average_rating else None,
				"total_reviews": specialist.total_reviews,
				"total_appointments": specialist.total_appointments,
				"profile_image_url": specialist.profile_image_url,
				"website_url": specialist.website_url,
				"social_media_links": specialist.social_media_links,
				"accepts_terms_and_conditions": specialist.accepts_terms_and_conditions
			},
			"approval_data": {
				"license_number": approval_data.license_number if approval_data else None,
				"license_issuing_authority": approval_data.license_issuing_authority if approval_data else None,
				"license_issue_date": approval_data.license_issue_date.isoformat() if approval_data and approval_data.license_issue_date else None,
				"license_expiry_date": approval_data.license_expiry_date.isoformat() if approval_data and approval_data.license_expiry_date else None,
				"highest_degree": approval_data.highest_degree if approval_data else None,
				"university_name": approval_data.university_name if approval_data else None,
				"graduation_year": approval_data.graduation_year if approval_data else None,
				"professional_memberships": approval_data.professional_memberships if approval_data else None,
				"certifications": approval_data.certifications if approval_data else None,
				"cnic": approval_data.cnic if approval_data else None,
				"passport_number": approval_data.passport_number if approval_data else None,
				"submission_date": approval_data.submission_date.isoformat() if approval_data and approval_data.submission_date else None,
				"background_check_status": approval_data.background_check_status if approval_data else None
			} if approval_data else None,
			"specializations": [
				{
					"specialization": spec.specialization.value,
					"years_of_experience": spec.years_of_experience_in_specialization,
					"certification_date": spec.certification_date.isoformat() if spec.certification_date else None,
					"is_primary": spec.is_primary_specialization
				} for spec in specializations
			] if specializations else [],
			"availability_slots": [
				{
					"time_slot": slot.time_slot.value,
					"display_time": slot.slot_display,
					"is_active": slot.is_active
				} for slot in availability_slots
			] if availability_slots else []
		}
		
		return profile_data
		
	except Exception as e:
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error fetching specialist profile: {str(e)}")


@router.put("/specialist/profile")
async def update_specialist_profile(
	profile_data: dict,
	current_user_data: dict = Depends(get_current_user_from_token),
	db: Session = Depends(get_db)
):
	"""Update specialist profile data"""
	user = current_user_data["user"]
	user_type = current_user_data["user_type"]
	
	if user_type != "specialist":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only specialists can access this endpoint")
	
	try:
		# Get specialist
		specialist = db.query(Specialists).filter(Specialists.id == user.id).first()
		if not specialist:
			raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specialist not found")
		
		# Update specialist fields if provided
		if "specialist" in profile_data:
			specialist_data = profile_data["specialist"]
			# Define safe fields that can be updated
			safe_fields = {
				'first_name', 'last_name', 'phone', 'date_of_birth', 'gender',
				'specialist_type', 'years_experience', 'city', 'address', 'clinic_name',
				'consultation_fee', 'bio', 'languages_spoken', 'availability_status',
				'profile_image_url', 'website_url', 'social_media_links'
			}
			
			for field, value in specialist_data.items():
				if field in safe_fields and hasattr(specialist, field) and value is not None:
					try:
						# Handle enum fields specially
						if field in ['gender', 'specialist_type', 'availability_status']:
							# Validate enum values
							if field == 'gender':
								from models.sql_models.specialist_models import GenderEnum
								if value in [e.value for e in GenderEnum]:
									setattr(specialist, field, value)
								else:
									print(f"Invalid gender value: {value}")
									continue
							elif field == 'specialist_type':
								from models.sql_models.specialist_models import SpecialistTypeEnum
								if value in [e.value for e in SpecialistTypeEnum]:
									setattr(specialist, field, value)
								else:
									print(f"Invalid specialist_type value: {value}")
									continue
							elif field == 'availability_status':
								from models.sql_models.specialist_models import AvailabilityStatusEnum
								if value in [e.value for e in AvailabilityStatusEnum]:
									setattr(specialist, field, value)
								else:
									print(f"Invalid availability_status value: {value}")
									continue
						else:
							# Handle regular fields
							setattr(specialist, field, value)
					except Exception as field_error:
						print(f"Error setting field {field}: {field_error}")
						# Continue with other fields instead of failing completely
		
		# Update approval data if provided
		if "approval_data" in profile_data and profile_data["approval_data"]:
			approval_data = db.query(SpecialistsApprovalData).filter(
				SpecialistsApprovalData.specialist_id == user.id
			).first()
			
			# Define safe fields for approval data
			approval_safe_fields = {
				'license_number', 'license_issuing_authority', 'license_issue_date',
				'license_expiry_date', 'highest_degree', 'university_name',
				'graduation_year', 'professional_memberships', 'certifications',
				'cnic', 'passport_number', 'background_check_status'
			}
			
			if approval_data:
				# Update existing approval data
				ap_data = profile_data["approval_data"]
				for field, value in ap_data.items():
					if field in approval_safe_fields and hasattr(approval_data, field) and value is not None:
						try:
							setattr(approval_data, field, value)
						except Exception as field_error:
							print(f"Error setting approval field {field}: {field_error}")
							# Continue with other fields
			else:
				# Create new approval data if doesn't exist
				ap_data = profile_data["approval_data"]
				approval_data = SpecialistsApprovalData(
					specialist_id=user.id,
					license_number=ap_data.get("license_number"),
					license_issuing_authority=ap_data.get("license_issuing_authority"),
					license_issue_date=ap_data.get("license_issue_date"),
					license_expiry_date=ap_data.get("license_expiry_date"),
					highest_degree=ap_data.get("highest_degree"),
					university_name=ap_data.get("university_name"),
					graduation_year=ap_data.get("graduation_year"),
					professional_memberships=ap_data.get("professional_memberships"),
					certifications=ap_data.get("certifications"),
					cnic=ap_data.get("cnic"),
					passport_number=ap_data.get("passport_number"),
					background_check_status=ap_data.get("background_check_status", "pending")
				)
				db.add(approval_data)
		
		# Update specializations if provided
		if "specializations" in profile_data and profile_data["specializations"]:
			# Remove existing specializations
			db.query(SpecialistSpecializations).filter(
				SpecialistSpecializations.specialist_id == user.id
			).delete()
			
			# Add new specializations
			for spec_data in profile_data["specializations"]:
				# Validate specialization enum value
				from models.sql_models.specialist_models import SpecializationEnum
				specialization_value = spec_data.get("specialization")
				if specialization_value and specialization_value in [e.value for e in SpecializationEnum]:
					spec = SpecialistSpecializations(
						specialist_id=user.id,
						specialization=specialization_value,
						years_of_experience_in_specialization=spec_data.get("years_of_experience", 0),
						certification_date=spec_data.get("certification_date"),
						is_primary_specialization=spec_data.get("is_primary", False)
					)
					db.add(spec)
				else:
					print(f"Invalid specialization value: {specialization_value}")
		
		# Update availability slots if provided
		if "availability_slots" in profile_data and profile_data["availability_slots"]:
			# Remove existing availability slots
			db.query(SpecialistAvailability).filter(
				SpecialistAvailability.specialist_id == user.id
			).delete()
			
			# Add new availability slots
			for slot_data in profile_data["availability_slots"]:
				# Validate time slot enum value
				from models.sql_models.specialist_models import TimeSlotEnum
				time_slot_value = slot_data.get("time_slot")
				if time_slot_value and time_slot_value in [e.value for e in TimeSlotEnum]:
					slot = SpecialistAvailability(
						specialist_id=user.id,
						time_slot=time_slot_value,
						is_active=slot_data.get("is_active", True)
					)
					db.add(slot)
				else:
					print(f"Invalid time slot value: {time_slot_value}")
		
		db.commit()
		
		return {"success": True, "message": "Profile updated successfully"}
		
	except Exception as e:
		db.rollback()
		print(f"Error updating specialist profile: {str(e)}")
		print(f"Profile data received: {profile_data}")
		import traceback
		traceback.print_exc()
		raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error updating specialist profile: {str(e)}")
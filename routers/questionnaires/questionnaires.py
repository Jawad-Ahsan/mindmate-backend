from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session

from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from models.sql_models.questionnaire_models import MandatoryQuestionnaireSubmission

router = APIRouter(prefix="", tags=["Questionnaires"])


class MandatoryQuestionnaireRequest(BaseModel):
	# Basic Information (already collected during registration)
	full_name: str = Field(..., description="Full name")
	age: int = Field(..., description="Age")
	gender: str = Field(..., description="Gender")
	
	# Chief Complaint
	chief_complaint: str = Field(..., description="Chief complaint")
	
	# Mental Health Treatment Data
	past_psychiatric_diagnosis: Optional[str] = Field(None, description="Past psychiatric diagnosis")
	past_psychiatric_treatment: Optional[str] = Field(None, description="Past psychiatric treatment")
	hospitalizations: Optional[str] = Field(None, description="Hospitalizations")
	ect_history: Optional[str] = Field(None, description="ECT history")
	
	# Medical and Substance History
	current_medications: Optional[str] = Field(None, description="Current medications")
	medication_allergies: Optional[str] = Field(None, description="Medication allergies")
	otc_supplements: Optional[str] = Field(None, description="OTC supplements")
	medication_adherence: Optional[str] = Field(None, description="Medication adherence")
	medical_history_summary: Optional[str] = Field(None, description="Medical history summary")
	chronic_illnesses: Optional[str] = Field(None, description="Chronic illnesses")
	neurological_problems: Optional[str] = Field(None, description="Neurological problems")
	head_injury: Optional[str] = Field(None, description="Head injury")
	seizure_history: Optional[str] = Field(None, description="Seizure history")
	pregnancy_status: Optional[str] = Field(None, description="Pregnancy status")
	
	# Substance Use
	alcohol_use: Optional[str] = Field(None, description="Alcohol use")
	drug_use: Optional[str] = Field(None, description="Drug use")
	prescription_drug_abuse: Optional[str] = Field(None, description="Prescription drug abuse")
	last_use_date: Optional[str] = Field(None, description="Last use date")
	substance_treatment: Optional[str] = Field(None, description="Substance treatment")
	tobacco_use: Optional[str] = Field(None, description="Tobacco use")
	
	# Family Mental Health History
	family_mental_health_history: Optional[str] = Field(None, description="Family mental health history")
	family_mental_health_stigma: Optional[str] = Field(None, description="Family mental health stigma")
	
	# Cultural and Spiritual Context
	cultural_background: Optional[str] = Field(None, description="Cultural background")
	cultural_beliefs: Optional[str] = Field(None, description="Cultural beliefs")
	spiritual_supports: Optional[str] = Field(None, description="Spiritual supports")
	
	# Lifestyle Factors
	lifestyle_smoking: Optional[str] = Field(None, description="Lifestyle smoking")
	lifestyle_alcohol: Optional[str] = Field(None, description="Lifestyle alcohol")
	lifestyle_activity: Optional[str] = Field(None, description="Lifestyle activity")


class MandatoryQuestionnaireResponse(BaseModel):
	success: bool = True
	message: str = "Mandatory questionnaire completed successfully"
	redirect_to: str = "/dashboard"


@router.post("/mandatory-questionnaire", response_model=MandatoryQuestionnaireResponse)
async def submit_mandatory_questionnaire(
	request: MandatoryQuestionnaireRequest,
	current_user_data: dict = Depends(get_current_user_from_token),
	db: Session = Depends(get_db),
):
	user = current_user_data["user"]
	user_type = current_user_data["user_type"]
	if user_type != "patient":
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can submit questionnaires")

	submission = MandatoryQuestionnaireSubmission(
		patient_id=user.id,
		full_name=request.full_name.strip(),
		age=str(request.age),
		gender=request.gender,
		chief_complaint=request.chief_complaint.strip(),
		past_psychiatric_diagnosis=request.past_psychiatric_diagnosis,
		past_psychiatric_treatment=request.past_psychiatric_treatment,
		hospitalizations=request.hospitalizations,
		ect_history=request.ect_history,
		current_medications=request.current_medications,
		medication_allergies=request.medication_allergies,
		otc_supplements=request.otc_supplements,
		medication_adherence=request.medication_adherence,
		medical_history_summary=request.medical_history_summary,
		chronic_illnesses=request.chronic_illnesses,
		neurological_problems=request.neurological_problems,
		head_injury=request.head_injury,
		seizure_history=request.seizure_history,
		pregnancy_status=request.pregnancy_status,
		alcohol_use=request.alcohol_use,
		drug_use=request.drug_use,
		prescription_drug_abuse=request.prescription_drug_abuse,
		last_use_date=request.last_use_date,
		substance_treatment=request.substance_treatment,
		tobacco_use=request.tobacco_use,
		family_mental_health_history=request.family_mental_health_history,
		family_mental_health_stigma=request.family_mental_health_stigma,
		cultural_background=request.cultural_background,
		cultural_beliefs=request.cultural_beliefs,
		spiritual_supports=request.spiritual_supports,
		lifestyle_smoking=request.lifestyle_smoking,
		lifestyle_alcohol=request.lifestyle_alcohol,
		lifestyle_activity=request.lifestyle_activity,
		is_complete=True
	)
	
	db.add(submission)
	db.commit()

	return MandatoryQuestionnaireResponse()



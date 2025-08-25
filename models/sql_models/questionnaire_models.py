from sqlalchemy import Column, String, DateTime, JSON, Boolean, Index, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from .base_model import Base, BaseModel as SQLBaseModel


class MandatoryQuestionnaireSubmission(Base, SQLBaseModel):
	__tablename__ = "mandatory_questionnaires"

	patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False, index=True)
	
	# Basic Information (already collected during registration)
	full_name = Column(String(200), nullable=False)
	age = Column(String(10), nullable=False)
	gender = Column(String(50), nullable=False)
	
	# Chief Complaint
	chief_complaint = Column(Text, nullable=False)
	
	# Mental Health Treatment Data
	past_psychiatric_diagnosis = Column(Text, nullable=True)
	past_psychiatric_treatment = Column(Text, nullable=True)
	hospitalizations = Column(Text, nullable=True)
	ect_history = Column(Text, nullable=True)
	
	# Medical and Substance History
	current_medications = Column(Text, nullable=True)
	medication_allergies = Column(Text, nullable=True)
	otc_supplements = Column(Text, nullable=True)
	medication_adherence = Column(String(50), nullable=True)
	medical_history_summary = Column(Text, nullable=True)
	chronic_illnesses = Column(Text, nullable=True)
	neurological_problems = Column(Text, nullable=True)
	head_injury = Column(Text, nullable=True)
	seizure_history = Column(Text, nullable=True)
	pregnancy_status = Column(String(50), nullable=True)
	
	# Substance Use
	alcohol_use = Column(String(50), nullable=True)
	drug_use = Column(String(50), nullable=True)
	prescription_drug_abuse = Column(String(50), nullable=True)
	last_use_date = Column(String(100), nullable=True)
	substance_treatment = Column(Text, nullable=True)
	tobacco_use = Column(String(50), nullable=True)
	
	# Family Mental Health History
	family_mental_health_history = Column(Text, nullable=True)
	family_mental_health_stigma = Column(String(50), nullable=True)
	
	# Cultural and Spiritual Context
	cultural_background = Column(Text, nullable=True)
	cultural_beliefs = Column(Text, nullable=True)
	spiritual_supports = Column(Text, nullable=True)
	
	# Lifestyle Factors
	lifestyle_smoking = Column(String(50), nullable=True)
	lifestyle_alcohol = Column(String(50), nullable=True)
	lifestyle_activity = Column(String(50), nullable=True)
	
	# Metadata
	meta = Column(JSON, nullable=True)
	submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
	processed = Column(Boolean, default=False, nullable=False)
	is_complete = Column(Boolean, default=False, nullable=False)

	patient = relationship("Patient", backref="mandatory_questionnaires")

	__table_args__ = (
		Index('idx_mandatory_q_patient', 'patient_id'),
		Index('idx_mandatory_q_submitted_at', 'submitted_at'),
		Index('idx_mandatory_q_complete', 'is_complete'),
	)

	def to_dict(self):
		"""Convert questionnaire to dictionary"""
		return {
			"id": str(self.id),
			"patient_id": str(self.patient_id),
			"full_name": self.full_name,
			"age": self.age,
			"gender": self.gender,
			"chief_complaint": self.chief_complaint,
			"past_psychiatric_diagnosis": self.past_psychiatric_diagnosis,
			"past_psychiatric_treatment": self.past_psychiatric_treatment,
			"hospitalizations": self.hospitalizations,
			"ect_history": self.ect_history,
			"current_medications": self.current_medications,
			"medication_allergies": self.medication_allergies,
			"otc_supplements": self.otc_supplements,
			"medication_adherence": self.medication_adherence,
			"medical_history_summary": self.medical_history_summary,
			"chronic_illnesses": self.chronic_illnesses,
			"neurological_problems": self.neurological_problems,
			"head_injury": self.head_injury,
			"seizure_history": self.seizure_history,
			"pregnancy_status": self.pregnancy_status,
			"alcohol_use": self.alcohol_use,
			"drug_use": self.drug_use,
			"prescription_drug_abuse": self.prescription_drug_abuse,
			"last_use_date": self.last_use_date,
			"substance_treatment": self.substance_treatment,
			"tobacco_use": self.tobacco_use,
			"family_mental_health_history": self.family_mental_health_history,
			"family_mental_health_stigma": self.family_mental_health_stigma,
			"cultural_background": self.cultural_background,
			"cultural_beliefs": self.cultural_beliefs,
			"spiritual_supports": self.spiritual_supports,
			"lifestyle_smoking": self.lifestyle_smoking,
			"lifestyle_alcohol": self.lifestyle_alcohol,
			"lifestyle_activity": self.lifestyle_activity,
			"submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
			"processed": self.processed,
			"is_complete": self.is_complete
		}



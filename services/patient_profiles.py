"""
Patient Profile Service Layer
============================
Service methods for creating different patient profile access levels:
- Public: Accessible to assigned specialists (clinical info, risk assessment, appointments)
- Protected: Accessible to admins only (account management, non-sensitive info)
- Private: Accessible to patient only (complete detailed profile)
"""

from sqlalchemy.orm import Session, selectinload
from sqlalchemy import desc, and_
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import uuid

from models.sql_models.patient_models import (
    Patient, PatientAuthInfo, PatientPreferences, PatientHistory,
    PatientPresentingConcerns, PatientRiskAssessment
)
from models.sql_models.appointments_model import Appointment

from models.pydantic_models.patient_profile_schemas import (
    # Component schemas
    BasePatientInfo, ContactInfo, LocationInfo,
    AppointmentSummary, RiskAssessmentSummary, PresentingConcernSummary, PreferencesSummary,
    DetailedPersonalInfo, AuthenticationInfo, DetailedPreferences,
    MedicalHistory, DetailedPresentingConcerns, DetailedRiskAssessment, DetailedAppointment,
    
    # Main profile schemas
    PatientPublicProfile, PatientProtectedProfile, PatientPrivateProfile,
    
    # Response schemas
    PatientProfileResponse, PatientReportInfo
)


class PatientProfileService:
    """Service class for managing patient profiles with different access levels"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def _get_patient_with_relations(self, patient_id: uuid.UUID, load_relations: List[str] = None) -> Optional[Patient]:
        """Get patient with specified relations loaded"""
        query = self.db.query(Patient).filter(
            Patient.id == patient_id,
            Patient.is_deleted == False
        )
        
        if load_relations:
            for relation in load_relations:
                query = query.options(selectinload(getattr(Patient, relation)))
        
        return query.first()
    
    def _build_base_patient_info(self, patient: Patient) -> BasePatientInfo:
        """Build base patient information component"""
        return BasePatientInfo(
            id=patient.id,
            full_name=patient.full_name,
            age=patient.age,
            record_status=patient.record_status
        )
    
    def _build_contact_info(self, patient: Patient) -> ContactInfo:
        """Build contact information component"""
        return ContactInfo(
            email=patient.email,
            phone=patient.phone
        )
    
    def _build_location_info(self, patient: Patient) -> LocationInfo:
        """Build location information component"""
        return LocationInfo(
            city=patient.city,
            district=patient.district,
            province=patient.province,
            country=patient.country
        )
    
    def _build_appointment_summaries(self, appointments: List[Appointment]) -> List[AppointmentSummary]:
        """Build appointment summaries from appointment objects"""
        summaries = []
        for appointment in appointments:
            # Get specialist name (you might need to adjust this based on your specialist model)
            specialist_name = None
            if hasattr(appointment, 'specialist') and appointment.specialist:
                specialist_name = appointment.specialist.full_name
            
            summary = AppointmentSummary(
                id=appointment.id,
                scheduled_start=appointment.scheduled_start,
                scheduled_end=appointment.scheduled_end,
                appointment_type=appointment.appointment_type,
                status=appointment.status,
                payment_status=appointment.payment_status,
                fee=appointment.fee,
                specialist_name=specialist_name
            )
            summaries.append(summary)
        return summaries
    
    def _build_risk_assessment_summary(self, risk_assessment: PatientRiskAssessment) -> Optional[RiskAssessmentSummary]:
        """Build risk assessment summary from risk assessment object"""
        if not risk_assessment:
            return None
        
        return RiskAssessmentSummary(
            risk_level=risk_assessment.risk_level,
            risk_value=risk_assessment.risk_value,
            assessment_timestamp=risk_assessment.assessment_timestamp,
            requires_immediate_attention=risk_assessment.requires_immediate_attention,
            safety_plan_created=risk_assessment.safety_plan_created,
            follow_up_required=risk_assessment.follow_up_required,
            follow_up_timeframe=risk_assessment.follow_up_timeframe
        )
    
    def _build_presenting_concern_summary(self, presenting_concerns: PatientPresentingConcerns) -> Optional[PresentingConcernSummary]:
        """Build presenting concern summary from presenting concerns object"""
        if not presenting_concerns:
            return None
        
        return PresentingConcernSummary(
            presenting_concern=presenting_concerns.presenting_concern,
            hpi_severity=presenting_concerns.hpi_severity,
            priority_level=presenting_concerns.priority_level,
            completion_percentage=presenting_concerns.completion_percentage,
            completion_timestamp=presenting_concerns.completion_timestamp
        )
    
    def _build_preferences_summary(self, preferences: PatientPreferences) -> Optional[PreferencesSummary]:
        """Build preferences summary from preferences object"""
        if not preferences:
            return None
        
        return PreferencesSummary(
            consultation_mode=preferences.consultation_mode,
            urgency_level=preferences.urgency_level,
            max_budget=preferences.max_budget,
            preferred_city=preferences.preferred_city
        )
    
    def _get_current_risk_assessment(self, patient_id: uuid.UUID) -> Optional[PatientRiskAssessment]:
        """Get the most current risk assessment for a patient"""
        return self.db.query(PatientRiskAssessment).filter(
            PatientRiskAssessment.patient_id == patient_id,
            PatientRiskAssessment.is_current == True
        ).order_by(desc(PatientRiskAssessment.assessment_timestamp)).first()
    
    def _get_patient_appointments(self, patient_id: uuid.UUID, limit: int = None) -> List[Appointment]:
        """Get patient appointments ordered by date"""
        query = self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).order_by(desc(Appointment.scheduled_start))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def _get_next_appointment(self, patient_id: uuid.UUID) -> Optional[Appointment]:
        """Get the next upcoming appointment for a patient"""
        return self.db.query(Appointment).filter(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.scheduled_start > datetime.now(),
                Appointment.status.in_(['scheduled', 'confirmed'])
            )
        ).order_by(Appointment.scheduled_start).first()
    
    def create_patient_public_profile(self, patient_id: uuid.UUID) -> Optional[PatientPublicProfile]:
        """
        Create public patient profile accessible to assigned specialists
        Includes: clinical info, risk assessment, appointments, contact info
        """
        # Load patient with required relations
        patient = self._get_patient_with_relations(
            patient_id, 
            ['appointments', 'presenting_concerns', 'risk_assessments']
        )
        
        if not patient:
            return None
        
        # Build base components
        patient_info = self._build_base_patient_info(patient)
        contact_info = self._build_contact_info(patient)
        
        # Get current risk assessment
        current_risk = self._get_current_risk_assessment(patient_id)
        risk_assessment_summary = self._build_risk_assessment_summary(current_risk)
        
        # Get presenting concerns (most recent active one)
        presenting_concern = None
        if patient.presenting_concerns:
            # Get the most recent active presenting concern
            active_concerns = [pc for pc in patient.presenting_concerns if pc.is_active]
            if active_concerns:
                presenting_concern = max(active_concerns, key=lambda x: x.completion_timestamp or datetime.min)
        
        presenting_concern_summary = self._build_presenting_concern_summary(presenting_concern)
        
        # Get appointments
        appointments = self._get_patient_appointments(patient_id, limit=10)  # Last 10 appointments
        appointment_summaries = self._build_appointment_summaries(appointments)
        
        # Get next appointment
        next_appointment = self._get_next_appointment(patient_id)
        next_appointment_date = next_appointment.scheduled_start if next_appointment else None
        
        return PatientPublicProfile(
            patient_info=patient_info,
            contact_info=contact_info,
            risk_assessment=risk_assessment_summary,
            presenting_concerns=presenting_concern_summary,
            next_appointment_date=next_appointment_date,
            appointment_history=appointment_summaries,
            assigned_therapist_id=patient.assigned_therapist_id,
            intake_completed_date=patient.intake_completed_date,
            last_contact_date=patient.last_contact_date,
            patient_report_available=False  # Will be updated by SMA
        )
    
    def create_patient_protected_profile(self, patient_id: uuid.UUID) -> Optional[PatientProtectedProfile]:
        """
        Create protected patient profile accessible to admins only
        Includes: account management info, non-sensitive data for status and forum management
        """
        # Load patient with required relations
        patient = self._get_patient_with_relations(
            patient_id, 
            ['auth_info', 'preferences']
        )
        
        if not patient:
            return None
        
        # Build base components
        patient_info = self._build_base_patient_info(patient)
        contact_info = self._build_contact_info(patient)
        location_info = self._build_location_info(patient)
        
        # Build auth info (non-sensitive parts)
        auth_info = None
        if patient.auth_info:
            auth_info = AuthenticationInfo(
                is_active=patient.auth_info.is_active,
                is_verified=patient.auth_info.is_verified,
                is_locked=patient.auth_info.is_locked,
                last_login=patient.auth_info.last_login,
                login_attempts=patient.auth_info.login_attempts,
                two_factor_enabled=patient.auth_info.two_factor_enabled,
                theme_preference=patient.auth_info.theme_preference,
                avatar_url=patient.auth_info.avatar_url
            )
        
        # Build preferences summary
        preferences_summary = self._build_preferences_summary(patient.preferences)
        
        # Forum activity summary (placeholder - implement based on your forum models)
        forum_activity_summary = {
            "total_posts": 0,
            "total_questions": 0,
            "last_activity": None,
            "reputation_score": 0
        }
        
        return PatientProtectedProfile(
            patient_info=patient_info,
            contact_info=contact_info,
            location_info=location_info,
            auth_info=auth_info,
            preferences=preferences_summary,
            intake_completed_date=patient.intake_completed_date,
            last_contact_date=patient.last_contact_date,
            assigned_therapist_id=patient.assigned_therapist_id,
            forum_activity_summary=forum_activity_summary,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            accepts_terms_and_conditions=patient.accepts_terms_and_conditions
        )
    
    def create_patient_private_profile(self, patient_id: uuid.UUID) -> Optional[PatientPrivateProfile]:
        """
        Create private patient profile accessible to patient only
        Includes: complete detailed profile with all information
        """
        # Load patient with all relations
        patient = self._get_patient_with_relations(
            patient_id, 
            ['auth_info', 'preferences', 'history', 'presenting_concerns', 'risk_assessments', 'appointments']
        )
        
        if not patient:
            return None
        
        # Build detailed personal info
        personal_info = DetailedPersonalInfo(
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            primary_language=patient.primary_language,
            full_address=patient.full_address
        )
        
        contact_info = self._build_contact_info(patient)
        location_info = self._build_location_info(patient)
        
        # Build detailed auth info
        auth_info = None
        if patient.auth_info:
            auth_info = AuthenticationInfo(
                is_active=patient.auth_info.is_active,
                is_verified=patient.auth_info.is_verified,
                is_locked=patient.auth_info.is_locked,
                last_login=patient.auth_info.last_login,
                login_attempts=patient.auth_info.login_attempts,
                two_factor_enabled=patient.auth_info.two_factor_enabled,
                theme_preference=patient.auth_info.theme_preference,
                avatar_url=patient.auth_info.avatar_url
            )
        
        # Build detailed preferences
        detailed_preferences = None
        if patient.preferences:
            detailed_preferences = DetailedPreferences(
                location_preferences=patient.preferences.location_preferences,
                cultural_preferences=patient.preferences.cultural_preferences,
                therapy_preferences=patient.preferences.therapy_preferences,
                financial_preferences=patient.preferences.financial_preferences,
                specialist_preferences=patient.preferences.specialist_preferences,
                availability_preferences=patient.preferences.availability_preferences,
                priority_weights=patient.preferences.priority_weights,
                notes=patient.preferences.notes
            )
        
        # Build medical history
        medical_history = None
        if patient.history:
            medical_history = MedicalHistory(
                past_psych_dx=patient.history.past_psych_dx,
                past_psych_treatment=patient.history.past_psych_treatment,
                hospitalizations=patient.history.hospitalizations,
                ect_history=patient.history.ect_history,
                current_meds=patient.history.current_meds,
                med_allergies=patient.history.med_allergies,
                otc_supplements=patient.history.otc_supplements,
                medication_adherence=patient.history.medication_adherence,
                medical_history_summary=patient.history.medical_history_summary,
                chronic_illnesses=patient.history.chronic_illnesses,
                neurological_problems=patient.history.neurological_problems,
                head_injury=patient.history.head_injury,
                seizure_history=patient.history.seizure_history,
                pregnancy_status=patient.history.pregnancy_status,
                alcohol_use=patient.history.alcohol_use,
                drug_use=patient.history.drug_use,
                prescription_drug_abuse=patient.history.prescription_drug_abuse,
                last_use_date=patient.history.last_use_date,
                substance_treatment=patient.history.substance_treatment,
                tobacco_use=patient.history.tobacco_use,
                cultural_background=patient.history.cultural_background,
                cultural_beliefs=patient.history.cultural_beliefs,
                spiritual_supports=patient.history.spiritual_supports,
                family_mental_health_stigma=patient.history.family_mental_health_stigma,
                completion_timestamp=patient.history.completion_timestamp,
                sections_completed=patient.history.sections_completed,
                completion_percentage=patient.history.completion_percentage
            )
        
        # Build detailed presenting concerns (most recent active one)
        detailed_presenting_concerns = None
        if patient.presenting_concerns:
            active_concerns = [pc for pc in patient.presenting_concerns if pc.is_active]
            if active_concerns:
                concern = max(active_concerns, key=lambda x: x.completion_timestamp or datetime.min)
                detailed_presenting_concerns = DetailedPresentingConcerns(
                    presenting_concern=concern.presenting_concern,
                    presenting_onset=concern.presenting_onset,
                    hpi_onset=concern.hpi_onset,
                    hpi_duration=concern.hpi_duration,
                    hpi_course=concern.hpi_course,
                    hpi_severity=concern.hpi_severity,
                    hpi_frequency=concern.hpi_frequency,
                    hpi_triggers=concern.hpi_triggers,
                    hpi_impact_work=concern.hpi_impact_work,
                    hpi_impact_relationships=concern.hpi_impact_relationships,
                    hpi_prior_episodes=concern.hpi_prior_episodes,
                    function_ADL=concern.function_ADL,
                    social_activities=concern.social_activities,
                    conversation_complete=concern.conversation_complete,
                    total_questions_asked=concern.total_questions_asked,
                    completion_timestamp=concern.completion_timestamp,
                    session_notes=concern.session_notes,
                    priority_level=concern.priority_level,
                    completion_percentage=concern.completion_percentage
                )
        
        # Build detailed risk assessments
        detailed_risk_assessments = []
        current_risk_assessment = None
        
        if patient.risk_assessments:
            for risk in patient.risk_assessments:
                detailed_risk = DetailedRiskAssessment(
                    suicide_ideation=risk.suicide_ideation,
                    suicide_plan=risk.suicide_plan,
                    suicide_intent=risk.suicide_intent,
                    past_attempts=risk.past_attempts,
                    self_harm_history=risk.self_harm_history,
                    homicidal_thoughts=risk.homicidal_thoughts,
                    access_means=risk.access_means,
                    protective_factors=risk.protective_factors,
                    risk_level=risk.risk_level,
                    risk_value=risk.risk_value,
                    risk_reason=risk.risk_reason,
                    assessment_timestamp=risk.assessment_timestamp,
                    assessed_by=risk.assessed_by,
                    assessment_type=risk.assessment_type,
                    is_current=risk.is_current,
                    requires_immediate_attention=risk.requires_immediate_attention,
                    safety_plan_created=risk.safety_plan_created,
                    follow_up_required=risk.follow_up_required,
                    follow_up_timeframe=risk.follow_up_timeframe
                )
                detailed_risk_assessments.append(detailed_risk)
                
                if risk.is_current:
                    current_risk_assessment = detailed_risk
        
        # Build detailed appointments
        detailed_appointments = []
        next_appointment = None
        
        if patient.appointments:
            for appointment in patient.appointments:
                # Get specialist name if available
                specialist_name = None
                if hasattr(appointment, 'specialist') and appointment.specialist:
                    specialist_name = appointment.specialist.full_name
                
                detailed_appt = DetailedAppointment(
                    id=appointment.id,
                    scheduled_start=appointment.scheduled_start,
                    scheduled_end=appointment.scheduled_end,
                    appointment_type=appointment.appointment_type,
                    status=appointment.status,
                    fee=appointment.fee,
                    payment_status=appointment.payment_status,
                    notes=appointment.notes,
                    session_notes=appointment.session_notes,
                    cancellation_reason=appointment.cancellation_reason,
                    specialist_id=appointment.specialist_id,
                    specialist_name=specialist_name,
                    created_at=appointment.created_at,
                    updated_at=appointment.updated_at
                )
                detailed_appointments.append(detailed_appt)
                
                # Check if this is the next appointment
                if (appointment.scheduled_start > datetime.now() and 
                    appointment.status in ['scheduled', 'confirmed'] and
                    (next_appointment is None or appointment.scheduled_start < next_appointment.scheduled_start)):
                    next_appointment = detailed_appt
        
        # Calculate overall profile completion percentage
        profile_completion = self._calculate_profile_completion(patient)
        
        return PatientPrivateProfile(
            personal_info=personal_info,
            contact_info=contact_info,
            location_info=location_info,
            auth_info=auth_info,
            preferences=detailed_preferences,
            medical_history=medical_history,
            presenting_concerns=detailed_presenting_concerns,
            risk_assessments=detailed_risk_assessments,
            current_risk_assessment=current_risk_assessment,
            appointments=detailed_appointments,
            next_appointment=next_appointment,
            assigned_therapist_id=patient.assigned_therapist_id,
            intake_completed_date=patient.intake_completed_date,
            last_contact_date=patient.last_contact_date,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            accepts_terms_and_conditions=patient.accepts_terms_and_conditions,
            profile_completion_percentage=profile_completion
        )
    
    def _calculate_profile_completion(self, patient: Patient) -> float:
        """Calculate overall profile completion percentage"""
        total_sections = 5  # Basic info, preferences, history, concerns, risk assessment
        completed_sections = 1  # Basic info is always complete if patient exists
        
        # Check preferences completion
        if patient.preferences:
            completed_sections += 0.5  # Partial completion for having preferences
        
        # Check history completion
        if patient.history and patient.history.completion_percentage:
            completed_sections += (patient.history.completion_percentage / 100)
        
        # Check presenting concerns completion
        if patient.presenting_concerns:
            active_concerns = [pc for pc in patient.presenting_concerns if pc.is_active]
            if active_concerns:
                concern = max(active_concerns, key=lambda x: x.completion_timestamp or datetime.min)
                completed_sections += (concern.completion_percentage / 100) if concern.completion_percentage else 0.5
        
        # Check risk assessment completion
        if patient.risk_assessments:
            current_risk = [ra for ra in patient.risk_assessments if ra.is_current]
            if current_risk:
                completed_sections += 1  # Risk assessment is either complete or not
        
        return min((completed_sections / total_sections) * 100, 100.0)
    
    def get_patient_report_info(self, patient_id: uuid.UUID) -> PatientReportInfo:
        """
        Get patient report information (will be implemented by SMA)
        This is a placeholder for the SMA integration
        """
        # This would typically check if a report exists for this patient
        # and return the appropriate information
        return PatientReportInfo(
            report_available=False,
            report_generated_date=None,
            report_type=None,
            report_url=None,
            generated_by="Specialists Matching Agent (SMA)"
        )


# Utility functions for creating profile responses

def create_patient_public_profile_response(
    db: Session, 
    patient_id: uuid.UUID
) -> Optional[PatientProfileResponse]:
    """Create a public profile response"""
    service = PatientProfileService(db)
    profile = service.create_patient_public_profile(patient_id)
    
    if not profile:
        return None
    
    return PatientProfileResponse(
        success=True,
        message="Public profile retrieved successfully",
        data=profile,
        timestamp=datetime.utcnow()
    )


def create_patient_protected_profile_response(
    db: Session, 
    patient_id: uuid.UUID
) -> Optional[PatientProfileResponse]:
    """Create a protected profile response"""
    service = PatientProfileService(db)
    profile = service.create_patient_protected_profile(patient_id)
    
    if not profile:
        return None
    
    return PatientProfileResponse(
        success=True,
        message="Protected profile retrieved successfully",
        data=profile,
        timestamp=datetime.utcnow()
    )


def create_patient_private_profile_response(
    db: Session, 
    patient_id: uuid.UUID
) -> Optional[PatientProfileResponse]:
    """Create a private profile response"""
    service = PatientProfileService(db)
    profile = service.create_patient_private_profile(patient_id)
    
    if not profile:
        return None
    
    return PatientProfileResponse(
        success=True,
        message="Private profile retrieved successfully", 
        data=profile,
        timestamp=datetime.utcnow()
    )


# Export all functions
__all__ = [
    'PatientProfileService',
    'create_patient_public_profile_response',
    'create_patient_protected_profile_response', 
    'create_patient_private_profile_response'
]
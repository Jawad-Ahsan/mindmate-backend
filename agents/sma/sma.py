"""
SMA - Specialist Matching Agent
==============================
Main orchestrator for specialist matching and appointment booking functionality.
Integrates specialist search, matching, and appointment management.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging
import uuid

from .specialits_matcher import SpecialistMatcher
from .appointments_manager import AppointmentsManager
from .sma_schemas import (
    SpecialistSearchRequest, BookAppointmentRequest, CancelAppointmentRequest, 
    RescheduleAppointmentRequest, UpdateAppointmentStatusRequest, 
    CancelAppointmentBySpecialistRequest, SpecialistDetailedInfo, 
    AppointmentStatus, ConsultationMode, SpecialistBasicInfo, AppointmentInfo,
    PatientPublicProfile, PatientReportInfo
)
from models.sql_models.specialist_models import Specialists, SpecialistsAuthInfo
from models.sql_models.patient_models import Patient
from models.sql_models.appointments_model import Appointment, AppointmentStatusEnum, AppointmentTypeEnum
from services.specialists.specialist_profiles import SpecialistProfileService
from utils.email_utils import send_notification_email

logger = logging.getLogger(__name__)

class SMA:
    """
    Specialist Matching Agent - Main orchestrator
    
    Provides unified interface for:
    - Specialist search and matching
    - Appointment booking and management
    - Integration with other MindMate agents
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.matcher = SpecialistMatcher(db)
        self.appointments_manager = AppointmentsManager(db)
        self.profile_service = SpecialistProfileService(db)
    
    # ============================================================================
    # PATIENT ENDPOINTS
    # ============================================================================
    
    def search_specialists(self, request: SpecialistSearchRequest) -> Dict[str, Any]:
        """
        Search and rank specialists based on patient preferences
        
        Args:
            request: Search criteria and preferences
            
        Returns:
            Paginated list of specialists with metadata
        """
        try:
            logger.info(f"Searching specialists with criteria: {request.dict()}")
            
            result = self.matcher.search_specialists(request)
            
            logger.info(f"Found {result['total_count']} specialists matching criteria")
            return result
            
        except Exception as e:
            logger.error(f"Error in specialist search: {str(e)}")
            raise
    
    def get_specialist_public_profile(self, specialist_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get specialist public profile with all information
        
        Args:
            specialist_id: Specialist UUID
            
        Returns:
            Detailed specialist information
        """
        try:
            logger.info(f"Getting public profile for specialist {specialist_id}")
            
            # Get specialist profile
            profile = self.profile_service.create_specialist_public_profile(specialist_id)
            
            if not profile:
                raise ValueError("Specialist not found or not approved")
            
            # Get availability slots
            slots = self.appointments_manager.get_specialist_slots(
                specialist_id=specialist_id,
                status="free"
            )
            
            result = {
                "specialist": profile,
                "availability_slots": slots[:20]  # Limit to next 20 slots
            }
            
            logger.info(f"Retrieved public profile for specialist {specialist_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting specialist public profile: {str(e)}")
            raise
    
    def book_appointment(self, patient_id: uuid.UUID, request: BookAppointmentRequest) -> Dict[str, Any]:
        """
        Book appointment with specific specialist
        
        Args:
            patient_id: Patient UUID
            request: Booking request
            
        Returns:
            Booked appointment details
        """
        try:
            logger.info(f"Patient {patient_id} booking appointment with specialist {request.specialist_id}")
            
            # Check if specialist exists and is approved
            specialist = self.db.query(Specialists).filter(
                Specialists.id == request.specialist_id,
                Specialists.is_deleted == False,
                Specialists.approval_status == "approved"
            ).first()
            
            if not specialist:
                raise ValueError("Specialist not found or not approved")
            
            # Check if slot is available
            if not self.appointments_manager.is_slot_available(
                specialist_id=request.specialist_id,
                start_time=request.scheduled_start,
                end_time=request.scheduled_end
            ):
                raise ValueError("Selected time slot is not available")
            
            # Create appointment
            appointment = Appointment(
                specialist_id=request.specialist_id,
                patient_id=patient_id,
                scheduled_start=request.scheduled_start,
                scheduled_end=request.scheduled_end,
                appointment_type=AppointmentTypeEnum.VIRTUAL if request.consultation_mode == ConsultationMode.ONLINE else AppointmentTypeEnum.IN_PERSON,
                status=AppointmentStatusEnum.SCHEDULED,
                fee=specialist.consultation_fee or 0,
                notes=request.notes
            )
            
            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)
            
            # Send notification to specialist
            self._send_appointment_notification_to_specialist(appointment, "new_booking")
            
            result = {
                "appointment": {
                    "id": appointment.id,
                    "patient_id": appointment.patient_id,
                    "specialist_id": appointment.specialist_id,
                    "scheduled_start": appointment.scheduled_start,
                    "scheduled_end": appointment.scheduled_end,
                    "consultation_mode": request.consultation_mode,
                    "fee": float(appointment.fee),
                    "status": appointment.status.value,
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                    "updated_at": appointment.updated_at
                },
                "message": "Appointment booked successfully"
            }
            
            logger.info(f"Appointment booked successfully: {appointment.id}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error booking appointment: {str(e)}")
            raise
    
    def cancel_appointment(self, patient_id: uuid.UUID, request: CancelAppointmentRequest) -> Dict[str, Any]:
        """
        Cancel appointment by patient
        
        Args:
            patient_id: Patient UUID
            request: Cancellation request
            
        Returns:
            Cancellation confirmation
        """
        try:
            logger.info(f"Patient {patient_id} cancelling appointment {request.appointment_id}")
            
            appointment = self.db.query(Appointment).filter(
                Appointment.id == request.appointment_id,
                Appointment.patient_id == patient_id,
                Appointment.status.in_([AppointmentStatusEnum.SCHEDULED, AppointmentStatusEnum.CONFIRMED])
            ).first()
            
            if not appointment:
                raise ValueError("Appointment not found or cannot be cancelled")
            
            # Update appointment status
            appointment.status = AppointmentStatusEnum.CANCELLED
            appointment.cancellation_reason = request.reason
            appointment.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Send notification to specialist
            self._send_appointment_notification_to_specialist(appointment, "cancelled_by_patient")
            
            result = {
                "appointment": {
                    "id": appointment.id,
                    "status": appointment.status.value,
                    "cancelled_at": appointment.updated_at
                },
                "message": "Appointment cancelled successfully"
            }
            
            logger.info(f"Appointment {appointment.id} cancelled by patient")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling appointment: {str(e)}")
            raise
    
    def reschedule_appointment(self, patient_id: uuid.UUID, request: RescheduleAppointmentRequest) -> Dict[str, Any]:
        """
        Reschedule appointment by patient
        
        Args:
            patient_id: Patient UUID
            request: Reschedule request
            
        Returns:
            Rescheduled appointment details
        """
        try:
            logger.info(f"Patient {patient_id} rescheduling appointment {request.appointment_id}")
            
            appointment = self.db.query(Appointment).filter(
                Appointment.id == request.appointment_id,
                Appointment.patient_id == patient_id,
                Appointment.status.in_([AppointmentStatusEnum.SCHEDULED, AppointmentStatusEnum.CONFIRMED])
            ).first()
            
            if not appointment:
                raise ValueError("Appointment not found or cannot be rescheduled")
            
            # Check if new slot is available
            if not self.appointments_manager.is_slot_available(
                specialist_id=appointment.specialist_id,
                start_time=request.new_scheduled_start,
                end_time=request.new_scheduled_end
            ):
                raise ValueError("New time slot is not available")
            
            # Update appointment times
            appointment.scheduled_start = request.new_scheduled_start
            appointment.scheduled_end = request.new_scheduled_end
            appointment.notes = f"{appointment.notes or ''}\n\nRescheduled: {request.reason}"
            appointment.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Send notification to specialist
            self._send_appointment_notification_to_specialist(appointment, "rescheduled_by_patient")
            
            result = {
                "appointment": {
                    "id": appointment.id,
                    "scheduled_start": appointment.scheduled_start,
                    "scheduled_end": appointment.scheduled_end,
                    "status": appointment.status.value,
                    "updated_at": appointment.updated_at
                },
                "message": "Appointment rescheduled successfully"
            }
            
            logger.info(f"Appointment {appointment.id} rescheduled by patient")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error rescheduling appointment: {str(e)}")
            raise
    
    def get_appointment_status(self, patient_id: uuid.UUID, appointment_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get appointment status for patient
        
        Args:
            patient_id: Patient UUID
            appointment_id: Appointment UUID
            
        Returns:
            Appointment status information
        """
        try:
            logger.info(f"Getting appointment status for patient {patient_id}, appointment {appointment_id}")
            
            appointment = self.db.query(Appointment).filter(
                Appointment.id == appointment_id,
                Appointment.patient_id == patient_id
            ).first()
            
            if not appointment:
                raise ValueError("Appointment not found")
            
            result = {
                "appointment": {
                    "id": appointment.id,
                    "status": appointment.status.value,
                    "scheduled_start": appointment.scheduled_start,
                    "scheduled_end": appointment.scheduled_end,
                    "fee": float(appointment.fee),
                    "notes": appointment.notes,
                    "created_at": appointment.created_at,
                    "updated_at": appointment.updated_at
                },
                "message": "Appointment status retrieved successfully"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting appointment status: {str(e)}")
            raise
    
    # ============================================================================
    # SPECIALIST ENDPOINTS
    # ============================================================================
    
    def get_booked_appointments(self, specialist_id: uuid.UUID, page: int = 1, size: int = 20) -> Dict[str, Any]:
        """
        Get booked appointments for specialist
        
        Args:
            specialist_id: Specialist UUID
            page: Page number
            size: Results per page
            
        Returns:
            Paginated list of appointments
        """
        try:
            logger.info(f"Getting booked appointments for specialist {specialist_id}")
            
            # Query appointments
            query = self.db.query(Appointment).filter(
                Appointment.specialist_id == specialist_id,
                Appointment.status.in_([
                    AppointmentStatusEnum.SCHEDULED,
                    AppointmentStatusEnum.CONFIRMED,
                    AppointmentStatusEnum.COMPLETED
                ])
            ).order_by(Appointment.scheduled_start)
            
            # Pagination
            total_count = query.count()
            appointments = query.offset((page - 1) * size).limit(size).all()
            
            # Format appointments
            appointment_list = []
            for apt in appointments:
                # Get patient info
                patient = self.db.query(Patient).filter(Patient.id == apt.patient_id).first()
                
                appointment_list.append({
                    "id": apt.id,
                    "patient_id": apt.patient_id,
                    "patient_name": f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
                    "scheduled_start": apt.scheduled_start,
                    "scheduled_end": apt.scheduled_end,
                    "consultation_mode": "online" if apt.appointment_type == AppointmentTypeEnum.VIRTUAL else "in_person",
                    "fee": float(apt.fee),
                    "status": apt.status.value,
                    "notes": apt.notes,
                    "created_at": apt.created_at,
                    "updated_at": apt.updated_at
                })
            
            result = {
                "appointments": appointment_list,
                "total_count": total_count,
                "page": page,
                "size": size,
                "has_more": (page * size) < total_count
            }
            
            logger.info(f"Found {total_count} appointments for specialist {specialist_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting booked appointments: {str(e)}")
            raise
    
    def update_appointment_status(self, specialist_id: uuid.UUID, request: UpdateAppointmentStatusRequest) -> Dict[str, Any]:
        """
        Update appointment status by specialist
        
        Args:
            specialist_id: Specialist UUID
            request: Status update request
            
        Returns:
            Update confirmation
        """
        try:
            logger.info(f"Specialist {specialist_id} updating appointment {request.appointment_id} status to {request.status}")
            
            appointment = self.db.query(Appointment).filter(
                Appointment.id == request.appointment_id,
                Appointment.specialist_id == specialist_id
            ).first()
            
            if not appointment:
                raise ValueError("Appointment not found")
            
            # Update status
            appointment.status = AppointmentStatusEnum(request.status)
            appointment.notes = f"{appointment.notes or ''}\n\nSpecialist notes: {request.notes}"
            appointment.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Send notification to patient
            self._send_appointment_notification_to_patient(appointment, f"status_updated_to_{request.status}")
            
            result = {
                "appointment": {
                    "id": appointment.id,
                    "status": appointment.status.value,
                    "updated_at": appointment.updated_at
                },
                "message": f"Appointment status updated to {request.status}"
            }
            
            logger.info(f"Appointment {appointment.id} status updated to {request.status}")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating appointment status: {str(e)}")
            raise
    
    def cancel_appointment_by_specialist(self, specialist_id: uuid.UUID, request: CancelAppointmentBySpecialistRequest) -> Dict[str, Any]:
        """
        Cancel appointment by specialist
        
        Args:
            specialist_id: Specialist UUID
            request: Cancellation request
            
        Returns:
            Cancellation confirmation
        """
        try:
            logger.info(f"Specialist {specialist_id} cancelling appointment {request.appointment_id}")
            
            appointment = self.db.query(Appointment).filter(
                Appointment.id == request.appointment_id,
                Appointment.specialist_id == specialist_id,
                Appointment.status.in_([AppointmentStatusEnum.SCHEDULED, AppointmentStatusEnum.CONFIRMED])
            ).first()
            
            if not appointment:
                raise ValueError("Appointment not found or cannot be cancelled")
            
            # Update appointment status
            appointment.status = AppointmentStatusEnum.CANCELLED
            appointment.cancellation_reason = request.reason
            appointment.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            # Send notification to patient
            self._send_appointment_notification_to_patient(appointment, "cancelled_by_specialist")
            
            result = {
                "appointment": {
                    "id": appointment.id,
                    "status": appointment.status.value,
                    "cancelled_at": appointment.updated_at
                },
                "message": "Appointment cancelled successfully"
            }
            
            logger.info(f"Appointment {appointment.id} cancelled by specialist")
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cancelling appointment by specialist: {str(e)}")
            raise
    
    def get_patient_public_profile(self, specialist_id: uuid.UUID, patient_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get patient public profile for specialist
        
        Args:
            specialist_id: Specialist UUID
            patient_id: Patient UUID
            
        Returns:
            Patient public profile
        """
        try:
            logger.info(f"Getting patient public profile for specialist {specialist_id}, patient {patient_id}")
            
            # Verify specialist has appointment with this patient
            appointment = self.db.query(Appointment).filter(
                Appointment.specialist_id == specialist_id,
                Appointment.patient_id == patient_id
            ).first()
            
            if not appointment:
                raise ValueError("No appointment found with this patient")
            
            # Get patient info
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            
            if not patient:
                raise ValueError("Patient not found")
            
            # Get consultation history
            consultation_history = self.db.query(Appointment).filter(
                Appointment.patient_id == patient_id,
                Appointment.status == AppointmentStatusEnum.COMPLETED
            ).order_by(Appointment.scheduled_start.desc()).limit(10).all()
            
            history_list = []
            for apt in consultation_history:
                history_list.append({
                    "appointment_id": apt.id,
                    "specialist_name": "Dr. Specialist",  # You can join with specialist table
                    "date": apt.scheduled_start,
                    "status": apt.status.value
                })
            
            result = {
                "patient": {
                    "id": patient.id,
                    "first_name": patient.first_name,
                    "last_name": patient.last_name,
                    "age": patient.age if hasattr(patient, 'age') else None,
                    "gender": patient.gender if hasattr(patient, 'gender') else None,
                    "city": patient.city,
                    "consultation_history": history_list
                },
                "message": "Patient profile retrieved successfully"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting patient public profile: {str(e)}")
            raise
    
    def get_patient_referral_report(self, specialist_id: uuid.UUID, patient_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get patient referral report from PIMA
        
        Args:
            specialist_id: Specialist UUID
            patient_id: Patient UUID
            
        Returns:
            Patient report information
        """
        try:
            logger.info(f"Getting patient referral report for specialist {specialist_id}, patient {patient_id}")
            
            # Verify specialist has appointment with this patient
            appointment = self.db.query(Appointment).filter(
                Appointment.specialist_id == specialist_id,
                Appointment.patient_id == patient_id
            ).first()
            
            if not appointment:
                raise ValueError("No appointment found with this patient")
            
            # TODO: Integrate with PIMA to get actual report
            # For now, return mock data
            result = {
                "report": {
                    "patient_id": str(patient_id),
                    "report_available": True,
                    "report_generated_at": datetime.now(timezone.utc).isoformat(),
                    "report_type": "initial_assessment",
                    "report_summary": "Patient assessment completed by PIMA agent",
                    "risk_level": "moderate",
                    "recommendations": [
                        "Consider CBT therapy for anxiety management",
                        "Regular follow-up appointments recommended",
                        "Monitor for depressive symptoms"
                    ],
                    "generated_by": "PIMA_Agent"
                },
                "message": "Patient referral report retrieved successfully"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting patient referral report: {str(e)}")
            raise
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    def _send_appointment_notification_to_specialist(self, appointment: Appointment, notification_type: str):
        """Send notification to specialist about appointment changes"""
        try:
            # Get specialist email
            specialist = self.db.query(Specialists).filter(Specialists.id == appointment.specialist_id).first()
            if not specialist:
                return
            
            # Get patient info
            patient = self.db.query(Patient).filter(Patient.id == appointment.patient_id).first()
            patient_name = f"{patient.first_name} {patient.last_name}" if patient else "Patient"
            
            subject = f"Appointment Update - {notification_type.replace('_', ' ').title()}"
            message = f"""
            <h3>Appointment Update</h3>
            <p><strong>Patient:</strong> {patient_name}</p>
            <p><strong>Date:</strong> {appointment.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Status:</strong> {appointment.status.value}</p>
            """
            
            send_notification_email(specialist.email, subject, message)
            
        except Exception as e:
            logger.error(f"Error sending notification to specialist: {str(e)}")
    
    def _send_appointment_notification_to_patient(self, appointment: Appointment, notification_type: str):
        """Send notification to patient about appointment changes"""
        try:
            # Get patient email
            patient = self.db.query(Patient).filter(Patient.id == appointment.patient_id).first()
            if not patient:
                return
            
            # Get specialist info
            specialist = self.db.query(Specialists).filter(Specialists.id == appointment.specialist_id).first()
            specialist_name = f"Dr. {specialist.first_name} {specialist.last_name}" if specialist else "Specialist"
            
            subject = f"Appointment Update - {notification_type.replace('_', ' ').title()}"
            message = f"""
            <h3>Appointment Update</h3>
            <p><strong>Specialist:</strong> {specialist_name}</p>
            <p><strong>Date:</strong> {appointment.scheduled_start.strftime('%B %d, %Y at %I:%M %p')}</p>
            <p><strong>Status:</strong> {appointment.status.value}</p>
            """
            
            send_notification_email(patient.email, subject, message)
            
        except Exception as e:
            logger.error(f"Error sending notification to patient: {str(e)}")

"""
Appointments Manager - Slot and Appointment Management for SMA
============================================================
Handles slot availability, appointment booking, and appointment lifecycle management
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta, timezone
import logging
import uuid
from dataclasses import dataclass

from models.sql_models.specialist_models import Specialists
from models.sql_models.appointments_model import Appointment, AppointmentStatusEnum, AppointmentTypeEnum
from models.sql_models.patient_models import Patient
from .sma_schemas import (
    AppointmentInfo, AppointmentStatus, ConsultationMode
)

logger = logging.getLogger(__name__)

class AppointmentsManager:
    """Manages appointment booking and appointment lifecycle"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_specialist_slots(
        self, 
        specialist_id: uuid.UUID, 
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available slots for a specialist
        
        For now, this generates mock slots since we don't have a slots table yet.
        In a real implementation, this would query the specialist_slots table.
        """
        try:
            # Validate specialist exists and is active
            specialist = self.db.query(Specialists).filter(
                Specialists.id == specialist_id,
                Specialists.is_deleted == False
            ).first()
            
            if not specialist:
                raise ValueError("Specialist not found or inactive")
            
            # Set default date range if not provided
            if not from_date:
                from_date = datetime.now(timezone.utc) + timedelta(hours=1)
            if not to_date:
                to_date = from_date + timedelta(days=7)
            
            # Generate mock slots (replace with actual slot query)
            slots = self._generate_mock_slots(specialist_id, from_date, to_date)
            
            # Filter by status if specified
            if status:
                slots = [slot for slot in slots if slot['status'] == status]
            
            return slots
            
        except Exception as e:
            logger.error(f"Error getting specialist slots: {str(e)}")
            raise
    
    def is_slot_available(
        self, 
        specialist_id: uuid.UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> bool:
        """
        Check if a time slot is available for booking
        
        Args:
            specialist_id: Specialist UUID
            start_time: Start time of the slot
            end_time: End time of the slot
            
        Returns:
            True if slot is available, False otherwise
        """
        try:
            # Check if specialist exists and is active
            specialist = self.db.query(Specialists).filter(
                Specialists.id == specialist_id,
                Specialists.is_deleted == False,
                Specialists.approval_status == "approved"
            ).first()
            
            if not specialist:
                return False
            
            # Check for existing appointments in the time range
            existing_appointment = self.db.query(Appointment).filter(
                and_(
                    Appointment.specialist_id == specialist_id,
                    Appointment.status.in_([
                        AppointmentStatusEnum.SCHEDULED,
                        AppointmentStatusEnum.CONFIRMED
                    ]),
                    or_(
                        # Check for overlapping appointments
                        and_(
                            Appointment.scheduled_start < end_time,
                            Appointment.scheduled_end > start_time
                        )
                    )
                )
            ).first()
            
            # If no overlapping appointment found, slot is available
            return existing_appointment is None
            
        except Exception as e:
            logger.error(f"Error checking slot availability: {str(e)}")
            return False
    
    def get_specialist_statistics(
        self, 
        specialist_id: uuid.UUID, 
        from_date: Optional[datetime] = None, 
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get specialist statistics and metrics
        
        Args:
            specialist_id: Specialist UUID
            from_date: Start date for statistics
            to_date: End date for statistics
            
        Returns:
            Specialist statistics
        """
        try:
            # Build query filters
            filters = [Appointment.specialist_id == specialist_id]
            
            if from_date:
                filters.append(Appointment.scheduled_start >= from_date)
            if to_date:
                filters.append(Appointment.scheduled_start <= to_date)
            
            # Get appointment counts by status
            total_appointments = self.db.query(Appointment).filter(*filters).count()
            
            completed_appointments = self.db.query(Appointment).filter(
                *filters,
                Appointment.status == AppointmentStatusEnum.COMPLETED
            ).count()
            
            cancelled_appointments = self.db.query(Appointment).filter(
                *filters,
                Appointment.status == AppointmentStatusEnum.CANCELLED
            ).count()
            
            # Calculate completion rate
            completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
            
            # Get total revenue
            revenue_query = self.db.query(func.sum(Appointment.fee)).filter(
                *filters,
                Appointment.status == AppointmentStatusEnum.COMPLETED
            )
            total_revenue = revenue_query.scalar() or 0
            
            # Calculate average session duration (mock data for now)
            average_session_duration = 60  # minutes
            
            # Mock rating (in real implementation, this would come from reviews table)
            average_rating = 4.5
            
            # Mock patient satisfaction score
            patient_satisfaction_score = 85.0
            
            return {
                "specialist_id": str(specialist_id),
                "total_appointments": total_appointments,
                "completed_appointments": completed_appointments,
                "cancelled_appointments": cancelled_appointments,
                "completion_rate": round(completion_rate, 2),
                "average_rating": average_rating,
                "total_revenue": float(total_revenue),
                "average_session_duration": average_session_duration,
                "patient_satisfaction_score": patient_satisfaction_score,
                "period_start": from_date.isoformat() if from_date else None,
                "period_end": to_date.isoformat() if to_date else None
            }
            
        except Exception as e:
            logger.error(f"Error getting specialist statistics: {str(e)}")
            raise
    
    def cleanup_expired_holds(self) -> int:
        """
        Clean up expired slot holds
        
        Returns:
            Number of holds cleaned up
        """
        try:
            # Since we removed the hold system, this method is simplified
            # In a real implementation, this would clean up expired holds from Redis/database
            cleaned_count = 0
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired holds")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired holds: {str(e)}")
            return 0
    
    def _generate_mock_slots(
        self, 
        specialist_id: uuid.UUID, 
        from_date: datetime, 
        to_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Generate mock slots for testing
        
        In a real implementation, this would query the specialist_slots table
        """
        slots = []
        current_date = from_date
        
        while current_date <= to_date:
            # Generate slots for each day (9 AM to 5 PM, 1-hour slots)
            for hour in range(9, 17):
                slot_start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(hours=1)
                
                # Skip past slots
                if slot_start < datetime.now(timezone.utc):
                    continue
                
                # Check if slot is available
                is_available = self.is_slot_available(specialist_id, slot_start, slot_end)
                
                slots.append({
                    "id": uuid.uuid4(),
                    "specialist_id": str(specialist_id),
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "status": "free" if is_available else "booked",
                    "duration_minutes": 60
                })
            
            current_date += timedelta(days=1)
        
        return slots

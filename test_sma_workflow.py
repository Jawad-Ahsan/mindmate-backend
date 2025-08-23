"""
Test SMA Workflow
================
Test the simplified SMA workflow with patient and specialist endpoints
"""

import pytest
from datetime import datetime, timezone, timedelta
import uuid
from unittest.mock import Mock, patch

from agents.sma.sma import SMA
from agents.sma.sma_schemas import (
    SpecialistSearchRequest, BookAppointmentRequest, CancelAppointmentRequest,
    RescheduleAppointmentRequest, UpdateAppointmentStatusRequest,
    CancelAppointmentBySpecialistRequest, ConsultationMode, AppointmentStatus
)

class TestSMAWorkflow:
    """Test SMA workflow functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_db = Mock()
        self.sma = SMA(self.mock_db)
        
        # Mock patient and specialist IDs
        self.patient_id = uuid.uuid4()
        self.specialist_id = uuid.uuid4()
        self.appointment_id = uuid.uuid4()
        
        # Mock datetime
        self.now = datetime.now(timezone.utc)
        self.future_time = self.now + timedelta(days=1)
    
    def test_search_specialists(self):
        """Test specialist search functionality"""
        # Mock the specialist matcher
        with patch.object(self.sma.matcher, 'search_specialists') as mock_search:
            mock_search.return_value = {
                "specialists": [
                    {
                        "id": str(self.specialist_id),
                        "name": "Dr. Test",
                        "type": "Psychiatrist",
                        "rating": 4.5,
                        "specializations": ["Anxiety", "Depression"],
                        "fee": 3000,
                        "languages": ["English", "Urdu"],
                        "city": "Karachi",
                        "consultation_mode": "online",
                        "match_score": 0.85
                    }
                ],
                "total_count": 1,
                "page": 1,
                "size": 20,
                "has_more": False
            }
            
            # Create search request
            request = SpecialistSearchRequest(
                query="anxiety",
                consultation_mode=ConsultationMode.ONLINE,
                page=1,
                size=20
            )
            
            # Test search
            result = self.sma.search_specialists(request)
            
            # Verify result
            assert result["total_count"] == 1
            assert len(result["specialists"]) == 1
            assert result["specialists"][0]["name"] == "Dr. Test"
            mock_search.assert_called_once_with(request)
    
    def test_book_appointment(self):
        """Test appointment booking functionality"""
        # Mock specialist exists
        mock_specialist = Mock()
        mock_specialist.id = self.specialist_id
        mock_specialist.consultation_fee = 3000
        mock_specialist.is_deleted = False
        mock_specialist.approval_status = "approved"
        
        # Mock slot availability
        with patch.object(self.sma.appointments_manager, 'is_slot_available') as mock_available:
            mock_available.return_value = True
            
            # Mock database operations
            with patch.object(self.mock_db, 'query') as mock_query:
                mock_query.return_value.filter.return_value.first.return_value = mock_specialist
                
                with patch.object(self.mock_db, 'add') as mock_add:
                    with patch.object(self.mock_db, 'commit') as mock_commit:
                        with patch.object(self.mock_db, 'refresh') as mock_refresh:
                            # Mock appointment object
                            mock_appointment = Mock()
                            mock_appointment.id = self.appointment_id
                            mock_appointment.patient_id = self.patient_id
                            mock_appointment.specialist_id = self.specialist_id
                            mock_appointment.scheduled_start = self.future_time
                            mock_appointment.scheduled_end = self.future_time + timedelta(hours=1)
                            mock_appointment.fee = 3000
                            mock_appointment.status.value = "scheduled"
                            mock_appointment.notes = "Test appointment"
                            mock_appointment.created_at = self.now
                            mock_appointment.updated_at = self.now
                            
                            mock_refresh.return_value = mock_appointment
                            
                            # Create booking request
                            request = BookAppointmentRequest(
                                specialist_id=self.specialist_id,
                                scheduled_start=self.future_time,
                                scheduled_end=self.future_time + timedelta(hours=1),
                                consultation_mode=ConsultationMode.ONLINE,
                                notes="Test appointment"
                            )
                            
                            # Test booking
                            result = self.sma.book_appointment(self.patient_id, request)
                            
                            # Verify result
                            assert result["appointment"]["id"] == str(self.appointment_id)
                            assert result["appointment"]["status"] == "scheduled"
                            assert result["message"] == "Appointment booked successfully"
                            
                            # Verify database operations
                            mock_add.assert_called_once()
                            mock_commit.assert_called_once()
                            mock_available.assert_called_once_with(
                                self.specialist_id, 
                                self.future_time, 
                                self.future_time + timedelta(hours=1)
                            )
    
    def test_cancel_appointment(self):
        """Test appointment cancellation functionality"""
        # Mock appointment exists
        mock_appointment = Mock()
        mock_appointment.id = self.appointment_id
        mock_appointment.patient_id = self.patient_id
        mock_appointment.status.value = "scheduled"
        mock_appointment.status = Mock()
        mock_appointment.status.value = "scheduled"
        mock_appointment.updated_at = self.now
        
        # Mock database operations
        with patch.object(self.mock_db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_appointment
            
            with patch.object(self.mock_db, 'commit') as mock_commit:
                # Create cancellation request
                request = CancelAppointmentRequest(
                    appointment_id=self.appointment_id,
                    reason="Test cancellation"
                )
                
                # Test cancellation
                result = self.sma.cancel_appointment(self.patient_id, request)
                
                # Verify result
                assert result["appointment"]["id"] == str(self.appointment_id)
                assert result["appointment"]["status"] == "cancelled"
                assert result["message"] == "Appointment cancelled successfully"
                
                # Verify database operations
                mock_commit.assert_called_once()
    
    def test_get_booked_appointments(self):
        """Test getting booked appointments for specialist"""
        # Mock appointments
        mock_appointment = Mock()
        mock_appointment.id = self.appointment_id
        mock_appointment.patient_id = self.patient_id
        mock_appointment.scheduled_start = self.future_time
        mock_appointment.scheduled_end = self.future_time + timedelta(hours=1)
        mock_appointment.fee = 3000
        mock_appointment.status.value = "confirmed"
        mock_appointment.notes = "Test appointment"
        mock_appointment.created_at = self.now
        mock_appointment.updated_at = self.now
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.first_name = "John"
        mock_patient.last_name = "Doe"
        
        # Mock database operations
        with patch.object(self.mock_db, 'query') as mock_query:
            # Mock appointment query
            mock_appointment_query = Mock()
            mock_appointment_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_appointment]
            mock_appointment_query.filter.return_value.count.return_value = 1
            
            # Mock patient query
            mock_patient_query = Mock()
            mock_patient_query.filter.return_value.first.return_value = mock_patient
            
            mock_query.side_effect = [mock_appointment_query, mock_patient_query]
            
            # Test getting appointments
            result = self.sma.get_booked_appointments(self.specialist_id)
            
            # Verify result
            assert result["total_count"] == 1
            assert len(result["appointments"]) == 1
            assert result["appointments"][0]["patient_name"] == "John Doe"
            assert result["appointments"][0]["status"] == "confirmed"
    
    def test_update_appointment_status(self):
        """Test updating appointment status by specialist"""
        # Mock appointment exists
        mock_appointment = Mock()
        mock_appointment.id = self.appointment_id
        mock_appointment.specialist_id = self.specialist_id
        mock_appointment.status = Mock()
        mock_appointment.status.value = "scheduled"
        mock_appointment.notes = "Original notes"
        mock_appointment.updated_at = self.now
        
        # Mock database operations
        with patch.object(self.mock_db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_appointment
            
            with patch.object(self.mock_db, 'commit') as mock_commit:
                # Create status update request
                request = UpdateAppointmentStatusRequest(
                    appointment_id=self.appointment_id,
                    status=AppointmentStatus.CONFIRMED,
                    notes="Specialist notes"
                )
                
                # Test status update
                result = self.sma.update_appointment_status(self.specialist_id, request)
                
                # Verify result
                assert result["appointment"]["id"] == str(self.appointment_id)
                assert result["appointment"]["status"] == "confirmed"
                assert result["message"] == "Appointment status updated to confirmed"
                
                # Verify database operations
                mock_commit.assert_called_once()
    
    def test_get_patient_public_profile(self):
        """Test getting patient public profile"""
        # Mock appointment exists (for authorization)
        mock_appointment = Mock()
        mock_appointment.id = self.appointment_id
        mock_appointment.specialist_id = self.specialist_id
        mock_appointment.patient_id = self.patient_id
        
        # Mock patient
        mock_patient = Mock()
        mock_patient.id = self.patient_id
        mock_patient.first_name = "John"
        mock_patient.last_name = "Doe"
        mock_patient.city = "Karachi"
        
        # Mock database operations
        with patch.object(self.mock_db, 'query') as mock_query:
            # Mock appointment query
            mock_appointment_query = Mock()
            mock_appointment_query.filter.return_value.first.return_value = mock_appointment
            
            # Mock patient query
            mock_patient_query = Mock()
            mock_patient_query.filter.return_value.first.return_value = mock_patient
            
            # Mock consultation history query
            mock_history_query = Mock()
            mock_history_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
            
            mock_query.side_effect = [mock_appointment_query, mock_patient_query, mock_history_query]
            
            # Test getting patient profile
            result = self.sma.get_patient_public_profile(self.specialist_id, self.patient_id)
            
            # Verify result
            assert result["patient"]["first_name"] == "John"
            assert result["patient"]["last_name"] == "Doe"
            assert result["patient"]["city"] == "Karachi"
            assert result["message"] == "Patient profile retrieved successfully"
    
    def test_get_patient_referral_report(self):
        """Test getting patient referral report from PIMA"""
        # Mock appointment exists (for authorization)
        mock_appointment = Mock()
        mock_appointment.id = self.appointment_id
        mock_appointment.specialist_id = self.specialist_id
        mock_appointment.patient_id = self.patient_id
        
        # Mock database operations
        with patch.object(self.mock_db, 'query') as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = mock_appointment
            
            # Test getting patient report
            result = self.sma.get_patient_referral_report(self.specialist_id, self.patient_id)
            
            # Verify result
            assert result["report"]["patient_id"] == str(self.patient_id)
            assert result["report"]["report_available"] == True
            assert result["report"]["generated_by"] == "PIMA_Agent"
            assert result["message"] == "Patient referral report retrieved successfully"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

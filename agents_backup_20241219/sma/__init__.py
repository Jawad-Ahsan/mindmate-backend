"""
SMA - Specialist Matching Agent
==============================
Main package for specialist matching and appointment booking functionality.
"""

# Core SMA components
from .sma import SMA
from .specialits_matcher import SpecialistMatcher
from .appointments_manager import AppointmentsManager

# Schemas
from .sma_schemas import (
    SpecialistSearchRequest,
    BookAppointmentRequest,
    CancelAppointmentRequest,
    RescheduleAppointmentRequest,
    UpdateAppointmentStatusRequest,
    CancelAppointmentBySpecialistRequest,
    SpecialistBasicInfo,
    SpecialistDetailedInfo,
    AppointmentInfo,
    PatientPublicProfile,
    PatientReportInfo,
    SpecialistSearchResponse,
    SpecialistProfileResponse,
    AppointmentResponse,
    AppointmentListResponse,
    PatientProfileResponse,
    PatientReportResponse,
    ConsultationMode,
    SortOption,
    AppointmentStatus,
    SMAError,
    HealthCheckResponse
)

# Enums and constants
from .sma_schemas import (
    ConsultationMode,
    SortOption,
    AppointmentStatus
)

# Version
__version__ = "1.0.0"

# Package exports
__all__ = [
    # Core classes
    "SMA",
    "SpecialistMatcher", 
    "AppointmentsManager",
    
    # Request schemas
    "SpecialistSearchRequest",
    "BookAppointmentRequest",
    "CancelAppointmentRequest",
    "RescheduleAppointmentRequest",
    "UpdateAppointmentStatusRequest",
    "CancelAppointmentBySpecialistRequest",
    
    # Response schemas
    "SpecialistBasicInfo",
    "SpecialistDetailedInfo",
    "AppointmentInfo",
    "PatientPublicProfile",
    "PatientReportInfo",
    "SpecialistSearchResponse",
    "SpecialistProfileResponse",
    "AppointmentResponse",
    "AppointmentListResponse",
    "PatientProfileResponse",
    "PatientReportResponse",
    
    # Enums
    "ConsultationMode",
    "SortOption",
    "AppointmentStatus",
    
    # Error schemas
    "SMAError",
    "HealthCheckResponse"
]

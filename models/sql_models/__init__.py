# models/sql_models/__init__.py

from .appointments_model import Appointment
from .specialist_models import (
    Specialists,
    SpecialistDocuments,
    SpecialistsApprovalData,
    SpecialistsAuthInfo,
    SpecialistSpecializations,
)
from .patient_models import (
    Patient,
    PatientAuthInfo,
    PatientHistory,
    PatientPreferences,
    PatientPresentingConcerns,
    PatientRiskAssessment,
    
)

from .admin_models import(
    Admin,
    AdminCreate,
    AdminResponse,
    AdminRoleEnum,
    AdminUpdate,
    AdminStatusEnum
    
    
)

from .base_model import USERTYPE, Base, BaseModel
from .forum_models import Forum, ForumAnswer, ForumQuestion, ForumReport, ForumUserType
from .questionnaire_models import MandatoryQuestionnaireSubmission
from .journal_models import JournalEntry

__all__ = [
    # Base
    "Base",
    "BaseModel",
    "USERTYPE",

    # Patient
    "Patient",
    "PatientAuthInfo",
    "PatientHistory",
    "PatientPreferences",
    "PatientPresentingConcerns",
    "PatientRiskAssessment",

    # Specialist
    "Specialists",
    "SpecialistDocuments",
    "SpecialistsApprovalData",
    "SpecialistsAuthInfo",
    "SpecialistSpecializations",
    
    
    #Admin
    
    "Admin",
    "AdminCreate",
    "AdminResponse",
    "AdminUpdate",
    "AdminRoleEnum",
    "AdminStatusEnum",
    

    # Appointment
    "Appointment",

    # Forum
    "Forum",
    "ForumAnswer",
    "ForumQuestion",
    "ForumUserType",
    # Questionnaires
    "MandatoryQuestionnaireSubmission",
    
    # Journal and Forum
    "JournalEntry",
    "ForumQuestion",
    "ForumAnswer",
    "ForumReport",
]

# models/__init__.py

from .sql_models import (
    Base,
    BaseModel,
    USERTYPE,
    Patient,
    PatientAuthInfo,
    PatientHistory,
    PatientPreferences,
    PatientPresentingConcerns,
    PatientRiskAssessment,
    
    Specialists,
    SpecialistDocuments,
    SpecialistsApprovalData,
    SpecialistsAuthInfo,
    SpecialistSpecializations,
    
    Admin,
    AdminCreate,
    AdminResponse,
    AdminUpdate,
    AdminRoleEnum,
    AdminStatusEnum,
        
    Appointment,
    Forum,
    ForumAnswer,
    ForumQuestion,
    ForumUserType,
    
    # Journal and Forum Models
    JournalEntry,
    ForumQuestion,
    ForumAnswer,
)

from .sql_models.forum_models import ForumUserType, ForumQuestion, ForumAnswer, ForumReport

__all__ = [
    # Base
    "Base",
    "BaseModel",
    "USERTYPE",

    # Patient Models
    "Patient",
    "PatientAuthInfo",
    "PatientHistory",
    "PatientPreferences",
    "PatientPresentingConcerns",
    "PatientRiskAssessment",

    # Specialist Models
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
    
    # Journal and Forum
    "JournalEntry",
    "ForumQuestion",
    "ForumAnswer",
    "ForumReport",
]

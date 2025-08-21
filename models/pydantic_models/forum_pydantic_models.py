"""
Forum Pydantic Models - Request/Response Schemas
===============================================
Pydantic models for API request/response validation and serialization
Separated from SQLAlchemy models for clean architecture
"""

from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
import uuid

# Import enums from the SQL models
from  models.sql_models.forum_models import QuestionCategory, QuestionStatus, AnswerStatus

# Type literals for Pydantic
QuestionCategoryLiteral = Literal["anxiety", "depression", "stress", "relationships", "addiction", "trauma", "general", "other"]
QuestionStatusLiteral = Literal["open", "answered", "closed"]
AnswerStatusLiteral = Literal["active", "flagged", "removed"]
ForumUserTypeLiteral = Literal["patient", "specialist"]

# ============================================================================
# FORUM PYDANTIC MODELS
# ============================================================================

class ForumCreateRequest(BaseModel):
    """Request model for creating a new forum"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: QuestionCategoryLiteral = Field(default="general")
    is_moderated: bool = Field(default=True)
    allow_anonymous: bool = Field(default=True)
    max_questions_per_day: int = Field(default=5, ge=1, le=50)
    max_answers_per_question: int = Field(default=10, ge=1, le=100)

class ForumUpdateRequest(BaseModel):
    """Request model for updating forum settings"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[QuestionCategoryLiteral] = None
    is_active: Optional[bool] = None
    is_moderated: Optional[bool] = None
    allow_anonymous: Optional[bool] = None
    max_questions_per_day: Optional[int] = Field(None, ge=1, le=50)
    max_answers_per_question: Optional[int] = Field(None, ge=1, le=100)

class ForumResponse(BaseModel):
    """Response model for forum data"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    id: uuid.UUID
    name: str
    description: Optional[str]
    category: QuestionCategoryLiteral
    is_active: bool
    is_moderated: bool
    allow_anonymous: bool
    max_questions_per_day: int
    max_answers_per_question: int
    total_questions: int
    total_answers: int
    active_participants: int
    created_at: datetime
    updated_at: datetime
    
    @computed_field
    @property
    def engagement_rate(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return round((self.total_answers / self.total_questions), 2)

# ============================================================================
# QUESTION PYDANTIC MODELS
# ============================================================================

class QuestionCreateRequest(BaseModel):
    """Request model for creating a new question"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    forum_id: str = Field(..., description="Forum UUID")
    patient_id: str = Field(..., description="Patient UUID")
    title: str = Field(..., min_length=5, max_length=500)
    content: str = Field(..., min_length=10, max_length=5000)
    category: Optional[QuestionCategoryLiteral] = Field(default="general")
    is_anonymous: bool = Field(default=True)
    is_urgent: bool = Field(default=False)

    @field_validator('forum_id', 'patient_id')
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("Invalid UUID format")

class QuestionUpdateRequest(BaseModel):
    """Request model for updating a question"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    category: Optional[QuestionCategoryLiteral] = None
    status: Optional[QuestionStatusLiteral] = None
    is_urgent: Optional[bool] = None

class QuestionModerationRequest(BaseModel):
    """Request model for question moderation actions"""
    model_config = ConfigDict(use_enum_values=True)
    
    action: Literal["flag", "unflag", "close", "reopen"] = Field(...)
    reason: Optional[str] = Field(None, max_length=200)
    moderator_id: Optional[str] = None

    @field_validator('moderator_id')
    @classmethod
    def validate_moderator_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError("Invalid moderator ID format")
        return v

class PatientBasicInfo(BaseModel):
    """Basic patient info for question responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    display_name: str
    city: str
    age: Optional[int]
    risk_level: Optional[str]

class QuestionResponse(BaseModel):
    """Response model for question data"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    id: uuid.UUID
    forum_id: uuid.UUID
    patient_id: uuid.UUID
    title: str
    content: str
    category: QuestionCategoryLiteral
    status: QuestionStatusLiteral
    is_anonymous: bool
    is_urgent: bool
    answer_count: int
    view_count: int
    helpful_count: int
    is_flagged: bool
    flagged_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Optional nested data
    patient_info: Optional[PatientBasicInfo] = None
    answers: List["AnswerResponse"] = []
    
    @computed_field
    @property
    def has_answers(self) -> bool:
        return self.answer_count > 0
    
    @computed_field
    @property
    def is_answered(self) -> bool:
        return self.status == "answered"
    
    @computed_field
    @property
    def needs_attention(self) -> bool:
        return self.is_urgent and self.status == "open"

# ============================================================================
# ANSWER PYDANTIC MODELS
# ============================================================================

class AnswerCreateRequest(BaseModel):
    """Request model for creating an answer"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    question_id: str = Field(..., description="Question UUID")
    specialist_id: str = Field(..., description="Specialist UUID")
    content: str = Field(..., min_length=10, max_length=3000)

    @field_validator('question_id', 'specialist_id')
    @classmethod
    def validate_uuids(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("Invalid UUID format")

class AnswerUpdateRequest(BaseModel):
    """Request model for updating an answer"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True
    )
    
    content: Optional[str] = Field(None, min_length=10, max_length=3000)
    status: Optional[AnswerStatusLiteral] = None

class AnswerModerationRequest(BaseModel):
    """Request model for answer moderation actions"""
    model_config = ConfigDict(use_enum_values=True)
    
    action: Literal["flag", "approve", "remove", "restore", "mark_solution", "unmark_solution"] = Field(...)
    reason: Optional[str] = Field(None, max_length=200)
    moderator_id: Optional[str] = None

    @field_validator('moderator_id')
    @classmethod
    def validate_moderator_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError("Invalid moderator ID format")
        return v

class AnswerFeedbackRequest(BaseModel):
    """Request model for answer feedback (helpful/not helpful)"""
    model_config = ConfigDict(use_enum_values=True)
    
    is_helpful: bool = Field(...)
    patient_id: str = Field(..., description="Patient providing feedback")

    @field_validator('patient_id')
    @classmethod
    def validate_patient_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("Invalid patient ID format")

class SpecialistBasicInfo(BaseModel):
    """Basic specialist info for answer responses"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    first_name: str
    last_name: str
    specialist_type: str
    years_experience: int
    city: str
    average_rating: float
    
    @computed_field
    @property
    def display_name(self) -> str:
        return f"Dr. {self.first_name} {self.last_name}"
    
    @computed_field
    @property
    def credentials(self) -> str:
        return f"{self.specialist_type.replace('_', ' ').title()}, {self.years_experience} years experience"

class AnswerResponse(BaseModel):
    """Response model for answer data"""
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )
    
    id: uuid.UUID
    question_id: uuid.UUID
    specialist_id: uuid.UUID
    content: str
    status: AnswerStatusLiteral
    is_helpful: Optional[bool] = None
    helpful_count: int
    is_solution: bool
    is_flagged: bool
    flagged_reason: Optional[str]
    specialist_name: Optional[str]
    specialist_type: Optional[str]
    specialist_experience: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    # Optional nested specialist info
    specialist: Optional[SpecialistBasicInfo] = None
    
    @computed_field
    @property
    def is_active(self) -> bool:
        return self.status == "active"
    
    @computed_field
    @property
    def is_verified_solution(self) -> bool:
        return self.is_solution and self.is_active

# ============================================================================
# LIST AND PAGINATION MODELS
# ============================================================================

class QuestionListResponse(BaseModel):
    """Response model for paginated question lists"""
    questions: List[QuestionResponse]
    total: int
    page: int
    page_size: int
    
    @computed_field
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

class AnswerListResponse(BaseModel):
    """Response model for paginated answer lists"""
    answers: List[AnswerResponse]
    total: int
    page: int
    page_size: int
    
    @computed_field
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

class ForumListResponse(BaseModel):
    """Response model for paginated forum lists"""
    forums: List[ForumResponse]
    total: int
    page: int
    page_size: int
    
    @computed_field
    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

# ============================================================================
# STATISTICS AND ANALYTICS MODELS
# ============================================================================

class ForumStatsResponse(BaseModel):
    """Response model for forum statistics"""
    total_questions: int
    answered_questions: int
    unanswered_questions: int
    total_answers: int
    active_specialists: int
    active_patients: int
    total_helpful_votes: int
    total_solutions: int
    
    @computed_field
    @property
    def answer_rate(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return round((self.answered_questions / self.total_questions) * 100, 2)
    
    @computed_field
    @property
    def avg_answers_per_question(self) -> float:
        if self.total_questions == 0:
            return 0.0
        return round(self.total_answers / self.total_questions, 2)

class SpecialistForumStatsResponse(BaseModel):
    """Response model for specialist forum statistics"""
    specialist_id: uuid.UUID
    total_answers: int
    helpful_answers: int
    solution_answers: int
    flagged_answers: int
    forum_rating: float
    questions_answered: int
    avg_helpfulness_score: float
    last_active: Optional[datetime]
    
    @computed_field
    @property
    def helpfulness_ratio(self) -> float:
        if self.total_answers == 0:
            return 0.0
        return round((self.helpful_answers / self.total_answers) * 100, 2)
    
    @computed_field
    @property
    def solution_ratio(self) -> float:
        if self.total_answers == 0:
            return 0.0
        return round((self.solution_answers / self.total_answers) * 100, 2)

class PatientForumStatsResponse(BaseModel):
    """Response model for patient forum statistics"""
    patient_id: uuid.UUID
    total_questions: int
    answered_questions: int
    helpful_votes_given: int
    solutions_marked: int
    categories_used: List[str]
    avg_answers_per_question: float
    last_question_date: Optional[datetime]
    
    @computed_field
    @property
    def engagement_score(self) -> float:
        # Simple engagement score based on activity
        base_score = min(self.total_questions * 10, 100)  # Max 100 for questions
        feedback_bonus = min(self.helpful_votes_given * 5, 50)  # Max 50 for feedback
        solution_bonus = min(self.solutions_marked * 10, 50)  # Max 50 for marking solutions
        return min(base_score + feedback_bonus + solution_bonus, 200)

# ============================================================================
# SEARCH AND FILTER MODELS
# ============================================================================

class QuestionSearchRequest(BaseModel):
    """Request model for searching questions"""
    model_config = ConfigDict(use_enum_values=True)
    
    query: Optional[str] = Field(None, max_length=200)
    category: Optional[QuestionCategoryLiteral] = None
    status: Optional[QuestionStatusLiteral] = None
    is_urgent: Optional[bool] = None
    is_flagged: Optional[bool] = None
    forum_id: Optional[str] = None
    patient_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Literal["created_at", "updated_at", "view_count", "answer_count", "helpful_count"] = Field(default="created_at")
    sort_order: Literal["asc", "desc"] = Field(default="desc")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator('forum_id', 'patient_id')
    @classmethod
    def validate_optional_uuids(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError("Invalid UUID format")
        return v

class AnswerSearchRequest(BaseModel):
    """Request model for searching answers"""
    model_config = ConfigDict(use_enum_values=True)
    
    query: Optional[str] = Field(None, max_length=200)
    status: Optional[AnswerStatusLiteral] = None
    is_solution: Optional[bool] = None
    is_flagged: Optional[bool] = None
    question_id: Optional[str] = None
    specialist_id: Optional[str] = None
    min_helpful_count: Optional[int] = Field(None, ge=0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: Literal["created_at", "updated_at", "helpful_count"] = Field(default="created_at")
    sort_order: Literal["asc", "desc"] = Field(default="desc")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator('question_id', 'specialist_id')
    @classmethod
    def validate_optional_uuids(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                uuid.UUID(v)
                return v
            except ValueError:
                raise ValueError("Invalid UUID format")
        return v

# ============================================================================
# MODERATION AND ADMIN MODELS
# ============================================================================

class ModerationQueueResponse(BaseModel):
    """Response model for moderation queue"""
    flagged_questions: List[QuestionResponse]
    flagged_answers: List[AnswerResponse]
    pending_approval_count: int
    total_flagged_items: int
    
    @computed_field
    @property
    def requires_immediate_attention(self) -> int:
        urgent_questions = sum(1 for q in self.flagged_questions if q.is_urgent)
        return urgent_questions

class BulkModerationRequest(BaseModel):
    """Request model for bulk moderation actions"""
    model_config = ConfigDict(use_enum_values=True)
    
    item_type: Literal["question", "answer"] = Field(...)
    item_ids: List[str] = Field(..., min_length=1)
    action: Literal["approve", "flag", "remove", "restore"] = Field(...)
    reason: Optional[str] = Field(None, max_length=200)
    moderator_id: str = Field(...)

    @field_validator('item_ids')
    @classmethod
    def validate_item_ids(cls, v: List[str]) -> List[str]:
        for item_id in v:
            try:
                uuid.UUID(item_id)
            except ValueError:
                raise ValueError(f"Invalid UUID format: {item_id}")
        return v

    @field_validator('moderator_id')
    @classmethod
    def validate_moderator_id(cls, v: str) -> str:
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("Invalid moderator ID format")

class BulkModerationResponse(BaseModel):
    """Response model for bulk moderation results"""
    success: bool
    processed_count: int
    failed_count: int
    errors: List[str]
    message: str

# ============================================================================
# NOTIFICATION MODELS
# ============================================================================

class ForumNotificationResponse(BaseModel):
    """Response model for forum-related notifications"""
    id: uuid.UUID
    user_id: uuid.UUID
    user_type: ForumUserTypeLiteral
    notification_type: Literal["new_answer", "question_flagged", "answer_flagged", "solution_marked", "helpful_vote"]
    title: str
    message: str
    related_question_id: Optional[uuid.UUID]
    related_answer_id: Optional[uuid.UUID]
    is_read: bool
    created_at: datetime

# Forward reference resolution for nested models
QuestionResponse.model_rebuild()
AnswerResponse.model_rebuild()

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Type Literals
    "QuestionCategoryLiteral",
    "QuestionStatusLiteral", 
    "AnswerStatusLiteral",
    "ForumUserTypeLiteral",
    
    # Forum Models
    "ForumCreateRequest",
    "ForumUpdateRequest",
    "ForumResponse",
    
    # Question Models
    "QuestionCreateRequest",
    "QuestionUpdateRequest",
    "QuestionModerationRequest",
    "QuestionResponse",
    "PatientBasicInfo",
    
    # Answer Models
    "AnswerCreateRequest",
    "AnswerUpdateRequest",
    "AnswerModerationRequest",
    "AnswerFeedbackRequest",
    "AnswerResponse",
    "SpecialistBasicInfo",
    
    # List and Pagination Models
    "QuestionListResponse",
    "AnswerListResponse",
    "ForumListResponse",
    
    # Statistics Models
    "ForumStatsResponse",
    "SpecialistForumStatsResponse",
    "PatientForumStatsResponse",
    
    # Search Models
    "QuestionSearchRequest",
    "AnswerSearchRequest",
    
    # Moderation Models
    "ModerationQueueResponse",
    "BulkModerationRequest",
    "BulkModerationResponse",
    
    # Notification Models
    "ForumNotificationResponse",
]
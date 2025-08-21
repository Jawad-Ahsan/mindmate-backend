"""
Forum Models - SQLAlchemy Models Only
=====================================
Clean separation of concerns with only SQL models and core utility functions
Pydantic models are in separate forum_pydantic_models.py file
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Numeric, func, Index
from sqlalchemy.orm import validates, relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SA_Enum
from sqlalchemy.ext.hybrid import hybrid_property
from typing import Optional, List
from datetime import datetime, timezone
import enum
import uuid

# Import base model
from .base_model import Base, BaseModel as SQLBaseModel, USERTYPE

# ============================================================================
# ENUMERATIONS
# ============================================================================

class QuestionCategory(str, enum.Enum):
    """Question categories for better organization"""
    ANXIETY = "anxiety"
    DEPRESSION = "depression"
    STRESS = "stress"
    RELATIONSHIPS = "relationships"
    ADDICTION = "addiction"
    TRAUMA = "trauma"
    GENERAL = "general"
    OTHER = "other"

class QuestionStatus(str, enum.Enum):
    """Question status tracking"""
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"

class AnswerStatus(str, enum.Enum):
    """Answer status for moderation"""
    ACTIVE = "active"
    FLAGGED = "flagged"
    REMOVED = "removed"

class ForumUserType(str, enum.Enum):
    """Forum user types"""
    ADMIN = "admin"
    PATIENT = "patient"
    SPECIALIST = "specialist"

# ============================================================================
# CORE FORUM TABLE
# ============================================================================

class Forum(Base, SQLBaseModel):
    """
    Main Forum table - Central forum configuration and metadata
    """
    __tablename__ = "forums"
    
    __table_args__ = (
        Index('idx_forum_name', 'name'),
        Index('idx_forum_category', 'category'),
        Index('idx_forum_active', 'is_active'),
        {'extend_existing': True}
    )

    # Forum Information
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(SA_Enum(QuestionCategory), default=QuestionCategory.GENERAL, index=True)
    
    # Forum Settings
    is_active = Column(Boolean, default=True, index=True)
    is_moderated = Column(Boolean, default=True)
    allow_anonymous = Column(Boolean, default=True)
    max_questions_per_day = Column(Integer, default=5)
    max_answers_per_question = Column(Integer, default=10)
    
    # Statistics
    total_questions = Column(Integer, default=0)
    total_answers = Column(Integer, default=0)
    active_participants = Column(Integer, default=0)
    
    # Relationships
    questions = relationship("ForumQuestion", back_populates="forum", cascade="all, delete-orphan", lazy="dynamic")
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    @hybrid_property
    def is_available(self) -> bool:
        return self.is_active and not self.is_deleted
    
    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    
    def increment_question_count(self) -> None:
        """Increment total question count"""
        self.total_questions += 1
    
    def increment_answer_count(self) -> None:
        """Increment total answer count"""
        self.total_answers += 1
    
    def update_participant_count(self, count: int) -> None:
        """Update active participant count"""
        self.active_participants = count
    
    def __repr__(self) -> str:
        return f"<Forum({self.name}, {self.category.value})>"

# ============================================================================
# FORUM QUESTIONS TABLE
# ============================================================================

class ForumQuestion(Base, SQLBaseModel):
    """
    Forum Questions - Questions posted by patients
    """
    __tablename__ = "forum_questions"
    
    __table_args__ = (
            Index('idx_forum_question_patient', 'patient_id'),
            Index('idx_forum_question_forum', 'forum_id'),
            Index('idx_forum_question_category', 'category'),
            Index('idx_forum_question_status', 'status'),
            Index('idx_forum_question_created', 'created_at'),
            Index('idx_forum_question_answered', 'status', 'answer_count'),
            {'extend_existing': True}
        )

    # Foreign Keys 
    forum_id = Column(UUID(as_uuid=True), ForeignKey("forums.id"), nullable=True, index=True)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False, index=True)  
    
    # Question Content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(SA_Enum(QuestionCategory), default=QuestionCategory.GENERAL, index=True)
    
    # Status and Privacy
    status = Column(SA_Enum(QuestionStatus), default=QuestionStatus.OPEN, index=True)
    is_anonymous = Column(Boolean, default=True)
    is_urgent = Column(Boolean, default=False)
    
    # Metrics
    answer_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    
    # Moderation
    is_flagged = Column(Boolean, default=False)
    flagged_reason = Column(String(200), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderated_by = Column(UUID(as_uuid=True), nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    forum = relationship("Forum", back_populates="questions")
    answers = relationship("ForumAnswer", back_populates="question", cascade="all, delete-orphan", lazy="dynamic")
    patient = relationship("Patient", back_populates="forum_questions")     
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    def soft_delete(self):
        self.is_deleted = True
    
    @hybrid_property
    def has_answers(self) -> bool:
        return self.answer_count > 0

    @hybrid_property
    def is_answered(self) -> bool:
        return self.status == QuestionStatus.ANSWERED

    @hybrid_property
    def is_open(self) -> bool:
        return self.status == QuestionStatus.OPEN
    
    @hybrid_property
    def needs_attention(self) -> bool:
        return self.is_urgent and self.status == QuestionStatus.OPEN

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    @validates('title')
    def validate_title(self, key, title):
        if not title or len(title.strip()) < 5:
            raise ValueError("Title must be at least 5 characters long")
        if len(title) > 500:
            raise ValueError("Title cannot exceed 500 characters")
        return title.strip()

    @validates('content')
    def validate_content(self, key, content):
        if not content or len(content.strip()) < 10:
            raise ValueError("Content must be at least 10 characters long")
        if len(content) > 5000:
            raise ValueError("Content cannot exceed 5000 characters")
        return content.strip()

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    
    def increment_view_count(self) -> None:
        """Increment the view count for this question"""
        self.view_count += 1

    def mark_as_answered(self) -> None:
        """Mark question as answered when first answer is added"""
        if self.status == QuestionStatus.OPEN:
            self.status = QuestionStatus.ANSWERED

    def update_answer_count(self, session: Session) -> None:
        """Update the answer count based on active answers"""
        self.answer_count = session.query(func.count(ForumAnswer.id)).filter(
            ForumAnswer.question_id == self.id,
            ForumAnswer.status == AnswerStatus.ACTIVE,
            ForumAnswer.is_deleted == False
        ).scalar() or 0

    def can_be_answered(self) -> bool:
        """Check if question can receive new answers"""
        return self.status in [QuestionStatus.OPEN, QuestionStatus.ANSWERED] and not self.is_deleted

    def flag_question(self, reason: str, moderator_id: uuid.UUID = None) -> None:
        """Flag question for review"""
        self.is_flagged = True
        self.flagged_reason = reason
        self.moderated_at = datetime.now(timezone.utc)
        self.moderated_by = moderator_id

    def unflag_question(self) -> None:
        """Remove flag from question"""
        self.is_flagged = False
        self.flagged_reason = None

    def close_question(self) -> None:
        """Close question to prevent new answers"""
        self.status = QuestionStatus.CLOSED

    def __repr__(self) -> str:
        return f"<ForumQuestion({self.title[:50]}..., {self.category.value}, {self.status.value})>"

# ============================================================================
# FORUM ANSWERS TABLE
# ============================================================================

class ForumAnswer(Base, SQLBaseModel):
    """
    Forum Answers - Responses from specialists to questions
    """
    __tablename__ = "forum_answers"
    
    __table_args__ = (
        Index('idx_forum_answer_question', 'question_id'),
        Index('idx_forum_answer_specialist', 'specialist_id'),
        Index('idx_forum_answer_status', 'status'),
        Index('idx_forum_answer_created', 'created_at'),
        Index('idx_forum_answer_helpful', 'helpful_count'),
        {'extend_existing': True}
    )

    # Foreign Keys
    question_id = Column(UUID(as_uuid=True), ForeignKey("forum_questions.id"), nullable=False, index=True)
    specialist_id = Column(UUID(as_uuid=True), ForeignKey("specialists.id"), nullable=False, index=True)  # ✅ ADDED ForeignKey
    
    
    # Answer Content
    content = Column(Text, nullable=False)
    status = Column(SA_Enum(AnswerStatus), default=AnswerStatus.ACTIVE, index=True)
    
    # Feedback and Metrics
    is_helpful = Column(Boolean, default=None)  # Patient feedback
    helpful_count = Column(Integer, default=0)
    is_solution = Column(Boolean, default=False)  # Marked as solution by patient
    
    # Moderation
    is_flagged = Column(Boolean, default=False)
    flagged_reason = Column(String(200), nullable=True)
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Specialist Info Cache (for performance)
    specialist_name = Column(String(200), nullable=True)
    specialist_type = Column(String(50), nullable=True)
    specialist_experience = Column(Integer, nullable=True)
    
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    question = relationship("ForumQuestion", back_populates="answers")
    specialist = relationship("Specialists", back_populates="forum_answers", lazy="select")
    
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    def soft_delete(self):
        self.is_deleted = True
    
    @hybrid_property
    def is_active(self) -> bool:
        return self.status == AnswerStatus.ACTIVE and not self.is_deleted

    @hybrid_property
    def is_flagged_status(self) -> bool:
        return self.status == AnswerStatus.FLAGGED

    @hybrid_property
    def is_verified_solution(self) -> bool:
        return self.is_solution and self.is_active

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    @validates('content')
    def validate_content(self, key, content):
        if not content or len(content.strip()) < 10:
            raise ValueError("Answer content must be at least 10 characters long")
        if len(content) > 3000:
            raise ValueError("Answer content cannot exceed 3000 characters")
        return content.strip()

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    
    def mark_as_helpful(self, is_helpful: bool = True) -> None:
        """Mark answer as helpful or not helpful"""
        old_helpful = self.is_helpful
        self.is_helpful = is_helpful
        
        # Update helpful count
        if old_helpful != is_helpful:
            if is_helpful and not old_helpful:
                self.helpful_count += 1
            elif not is_helpful and old_helpful:
                self.helpful_count = max(0, self.helpful_count - 1)

    def mark_as_solution(self) -> None:
        """Mark this answer as the solution"""
        self.is_solution = True

    def unmark_as_solution(self) -> None:
        """Remove solution status"""
        self.is_solution = False

    def flag_for_review(self, reason: str, moderator_id: uuid.UUID = None) -> None:
        """Flag answer for moderation review"""
        self.status = AnswerStatus.FLAGGED
        self.is_flagged = True
        self.flagged_reason = reason
        self.moderated_at = datetime.now(timezone.utc)
        self.moderated_by = moderator_id

    def approve_answer(self) -> None:
        """Approve flagged answer"""
        self.status = AnswerStatus.ACTIVE
        self.is_flagged = False
        self.flagged_reason = None

    def remove_answer(self, reason: str = None) -> None:
        """Remove answer (admin action)"""
        self.status = AnswerStatus.REMOVED
        if reason:
            self.flagged_reason = reason

    def restore_answer(self) -> None:
        """Restore removed answer"""
        self.status = AnswerStatus.ACTIVE
        self.is_flagged = False

    def update_specialist_cache(self, specialist_name: str, specialist_type: str, experience: int) -> None:
        """Update cached specialist information for performance"""
        self.specialist_name = specialist_name
        self.specialist_type = specialist_type
        self.specialist_experience = experience

    def __repr__(self) -> str:
        return f"<ForumAnswer(question_id={self.question_id}, specialist_id={self.specialist_id}, {self.status.value})>"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_patient_for_forum(db_session: Session, patient_id: uuid.UUID) -> bool:
    """Validate that patient exists and is verified for forum operations"""
    try:
        from models.sql_models.patient_models import Patient, RecordStatusEnum
        
        patient = db_session.query(Patient).filter(
            Patient.id == patient_id,
            Patient.is_verified == True,
            Patient.is_active == True,
            Patient.record_status == RecordStatusEnum.ACTIVE,
            Patient.is_deleted == False
        ).first()
        
        return patient is not None
        
    except ImportError:
        # If patient model is not available, log warning but don't fail
        print("⚠️  Warning: Could not import Patient model for validation")
        return True

def validate_specialist_for_forum(db_session: Session, specialist_id: uuid.UUID) -> bool:
    """Validate that specialist exists and is approved for forum operations"""
    try:
        from models.sql_models.specialist_models import Specialists, ApprovalStatusEnum
        from models.sql_models.specialist_models import SpecialistsAuthInfo, EmailVerificationStatusEnum
        
        specialist = db_session.query(Specialists).join(
            SpecialistsAuthInfo
        ).filter(
            Specialists.id == specialist_id,
            Specialists.approval_status == ApprovalStatusEnum.APPROVED,
            SpecialistsAuthInfo.email_verification_status == EmailVerificationStatusEnum.VERIFIED,
            Specialists.is_active == True,
            Specialists.is_deleted == False
        ).first()
        
        return specialist is not None
        
    except ImportError:
        # If specialist model is not available, log warning but don't fail
        print("⚠️  Warning: Could not import Specialist model for validation")
        return True

def get_patient_questions(
    db_session: Session, 
    patient_id: uuid.UUID, 
    status: Optional[QuestionStatus] = None,
    category: Optional[QuestionCategory] = None,
    limit: int = 20, 
    offset: int = 0
) -> List[ForumQuestion]:
    """Get questions by a specific patient with optional filters"""
    query = db_session.query(ForumQuestion).filter(
        ForumQuestion.patient_id == patient_id,
        ForumQuestion.is_deleted == False
    )
    
    if status:
        query = query.filter(ForumQuestion.status == status)
    
    if category:
        query = query.filter(ForumQuestion.category == category)
    
    return query.order_by(ForumQuestion.created_at.desc()).offset(offset).limit(limit).all()

def get_specialist_answers(
    db_session: Session, 
    specialist_id: uuid.UUID, 
    status: Optional[AnswerStatus] = None,
    limit: int = 20, 
    offset: int = 0
) -> List[ForumAnswer]:
    """Get answers by a specific specialist with optional status filter"""
    query = db_session.query(ForumAnswer).filter(
        ForumAnswer.specialist_id == specialist_id,
        ForumAnswer.is_deleted == False
    )
    
    if status:
        query = query.filter(ForumAnswer.status == status)
    else:
        # Default to active answers only
        query = query.filter(ForumAnswer.status == AnswerStatus.ACTIVE)
    
    return query.order_by(ForumAnswer.created_at.desc()).offset(offset).limit(limit).all()

def create_specialist_forum_profile(
    db_session: Session,
    specialist_id: uuid.UUID
) -> dict:
    """Create or update specialist forum profile with cached information"""
    try:
        from models.sql_models.specialist_models import Specialists
        
        specialist = db_session.query(Specialists).filter(
            Specialists.id == specialist_id,
            Specialists.is_deleted == False
        ).first()
        
        if not specialist:
            return {
                "success": False,
                "error": "Specialist not found",
                "profile": None
            }
        
        # Get specialist's forum statistics
        total_answers = db_session.query(func.count(ForumAnswer.id)).filter(
            ForumAnswer.specialist_id == specialist_id,
            ForumAnswer.status == AnswerStatus.ACTIVE,
            ForumAnswer.is_deleted == False
        ).scalar() or 0
        
        helpful_answers = db_session.query(func.count(ForumAnswer.id)).filter(
            ForumAnswer.specialist_id == specialist_id,
            ForumAnswer.is_helpful == True,
            ForumAnswer.status == AnswerStatus.ACTIVE,
            ForumAnswer.is_deleted == False
        ).scalar() or 0
        
        solution_answers = db_session.query(func.count(ForumAnswer.id)).filter(
            ForumAnswer.specialist_id == specialist_id,
            ForumAnswer.is_solution == True,
            ForumAnswer.status == AnswerStatus.ACTIVE,
            ForumAnswer.is_deleted == False
        ).scalar() or 0
        
        # Calculate forum rating
        forum_rating = 0.0
        if total_answers > 0:
            helpfulness_ratio = helpful_answers / total_answers
            solution_ratio = solution_answers / total_answers
            forum_rating = round((helpfulness_ratio * 0.7 + solution_ratio * 0.3) * 5, 2)
        
        profile_data = {
            "specialist_id": specialist_id,
            "display_name": f"Dr. {specialist.first_name} {specialist.last_name}",
            "specialist_type": specialist.specialist_type.value,
            "years_experience": specialist.years_experience,
            "city": specialist.city,
            "overall_rating": float(specialist.average_rating),
            "total_answers": total_answers,
            "helpful_answers": helpful_answers,
            "solution_answers": solution_answers,
            "forum_rating": forum_rating,
            "is_active_in_forum": total_answers > 0,
            "last_active": None  # Can be calculated from recent answers
        }
        
        return {
            "success": True,
            "error": None,
            "profile": profile_data
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "profile": None
        }

# ============================================================================
# RELATIONSHIP SETUP FUNCTION
# ============================================================================

def setup_forum_relationships():
    """
    Setup relationships after all models are imported.
    This function should be called after importing all related models.
    """
    try:
        # Setup any additional relationships if needed
        print("✅ Forum relationships configured successfully")
    except Exception as e:
        print(f"⚠️  Warning: Could not setup forum relationships: {e}")

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "QuestionCategory",
    "QuestionStatus", 
    "AnswerStatus",
    
    # SQLAlchemy Models
    "Forum",
    "ForumQuestion",
    "ForumAnswer",
    
    # Utility Functions
    "validate_patient_for_forum",
    "validate_specialist_for_forum",
    "get_patient_questions",
    "get_specialist_answers",
    "create_specialist_forum_profile",
    "setup_forum_relationships",
]

# ============================================================================
# FORUM REPORTS TABLE
# ============================================================================

class ForumReport(Base, SQLBaseModel):
    """
    Forum Reports - Reports submitted by users for questions or answers
    """
    __tablename__ = "forum_reports"
    
    __table_args__ = (
        Index('idx_forum_report_reporter', 'reporter_id'),
        Index('idx_forum_report_post', 'post_id', 'post_type'),
        Index('idx_forum_report_status', 'status'),
        Index('idx_forum_report_created', 'created_at'),
        {'extend_existing': True}
    )

    # Foreign Keys
    reporter_id = Column(UUID(as_uuid=True), ForeignKey("patients.id", ondelete='CASCADE'), nullable=True, index=True)
    specialist_reporter_id = Column(UUID(as_uuid=True), ForeignKey("specialists.id", ondelete='CASCADE'), nullable=True, index=True)
    
    # Report Details
    post_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # ID of reported question or answer
    post_type = Column(String(20), nullable=False, index=True)  # "question" or "answer"
    reason = Column(Text, nullable=True)  # Optional reason for reporting
    
    # Status
    status = Column(String(20), default="pending", index=True)  # "pending", "resolved", "removed"
    
    # Moderation
    moderated_by = Column(UUID(as_uuid=True), nullable=True)  # Admin who processed the report
    moderated_at = Column(DateTime(timezone=True), nullable=True)
    moderation_notes = Column(Text, nullable=True)
    
    # Relationships
    reporter_patient = relationship("Patient", foreign_keys=[reporter_id])
    reporter_specialist = relationship("Specialists", foreign_keys=[specialist_reporter_id])
    
    # ============================================================================
    # PROPERTIES
    # ============================================================================
    
    @property
    def reporter_name(self) -> str:
        """Get reporter name based on type"""
        if self.reporter_patient:
            return f"{self.reporter_patient.first_name} {self.reporter_patient.last_name}"
        elif self.reporter_specialist:
            return f"{self.reporter_specialist.first_name} {self.reporter_specialist.last_name}"
        return "Unknown"
    
    @property
    def reporter_type(self) -> str:
        """Get reporter type"""
        if self.reporter_patient:
            return "patient"
        elif self.reporter_specialist:
            return "specialist"
        return "unknown"
    
    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    
    def mark_resolved(self, admin_id: str, notes: str = None) -> None:
        """Mark report as resolved"""
        self.status = "resolved"
        self.moderated_by = admin_id
        self.moderated_at = datetime.now(timezone.utc)
        self.moderation_notes = notes
    
    def mark_removed(self, admin_id: str, notes: str = None) -> None:
        """Mark report as removed (post was deleted)"""
        self.status = "removed"
        self.moderated_by = admin_id
        self.moderated_at = datetime.now(timezone.utc)
        self.moderation_notes = notes
    
    def __repr__(self) -> str:
        return f"<ForumReport({self.post_type}, {self.status}, {self.reporter_name})>"
"""
Forum Router - API endpoints for forum questions and answers
==========================================================
Handles CRUD operations for forum questions that patients can ask and specialists can answer
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from database.database import get_db
from routers.authentication.authenticate import get_current_user_from_token
from models.sql_models.forum_models import ForumQuestion, ForumAnswer, ForumReport, QuestionCategory, QuestionStatus, AnswerStatus
from models.sql_models.patient_models import Patient
from models.sql_models.specialist_models import Specialists

router = APIRouter(prefix="/forum", tags=["Forum"])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_time_ago(created_at: datetime) -> str:
    """Calculate relative time ago from datetime"""
    now = datetime.now(timezone.utc)
    diff = now - created_at
    
    if diff.days > 0:
        if diff.days == 1:
            return "1 day ago"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            if weeks == 1:
                return "1 week ago"
            return f"{weeks} weeks ago"
        else:
            months = diff.days // 30
            if months == 1:
                return "1 month ago"
            return f"{months} months ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        if hours == 1:
            return "1 hour ago"
        return f"{hours} hours ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        if minutes == 1:
            return "1 minute ago"
        return f"{minutes} minutes ago"
    else:
        return "Just now"

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

from pydantic import BaseModel, Field

class ForumQuestionCreate(BaseModel):
    """Create a new forum question"""
    title: str = Field(..., min_length=1, max_length=500, description="Question title")
    content: str = Field(..., min_length=1, description="Question content")
    category: QuestionCategory = Field(QuestionCategory.GENERAL, description="Question category")
    is_anonymous: bool = Field(True, description="Whether to post anonymously")
    is_urgent: bool = Field(False, description="Whether this is an urgent question")

class ForumQuestionUpdate(BaseModel):
    """Update an existing forum question"""
    title: Optional[str] = Field(None, min_length=1, max_length=500, description="Question title")
    content: Optional[str] = Field(None, min_length=1, description="Question content")
    category: Optional[QuestionCategory] = Field(None, description="Question category")
    is_anonymous: Optional[bool] = Field(None, description="Whether to post anonymously")
    is_urgent: Optional[bool] = Field(None, description="Whether this is an urgent question")

class ForumQuestionResponse(BaseModel):
    """Forum question response model"""
    id: str
    title: str
    content: str
    category: str
    author_id: str
    author_name: str
    is_anonymous: bool
    is_urgent: bool
    status: str
    asked_at: datetime
    formatted_date: str
    time_ago: str
    answers_count: int
    views_count: int
    is_active: bool

    class Config:
        from_attributes = True

class ForumAnswerCreate(BaseModel):
    """Create a new answer to a question"""
    content: str = Field(..., min_length=1, description="Answer content")

class ForumAnswerUpdate(BaseModel):
    """Update an existing answer"""
    content: str = Field(..., min_length=1, description="Answer content")

class ForumAnswerResponse(BaseModel):
    """Forum answer response model"""
    id: str
    question_id: str
    content: str
    specialist_id: str
    specialist_name: str
    answered_at: datetime
    time_ago: str
    status: str
    is_active: bool

    class Config:
        from_attributes = True

class ForumReportCreate(BaseModel):
    """Create a new forum report"""
    post_id: str = Field(..., description="ID of the reported question or answer")
    post_type: str = Field(..., description="Type of post: 'question' or 'answer'")
    reason: Optional[str] = Field(None, description="Optional reason for reporting")

class ForumReportResponse(BaseModel):
    """Forum report response model"""
    id: str
    post_id: str
    post_type: str
    reason: Optional[str]
    status: str
    reporter_name: str
    reporter_type: str
    created_at: datetime
    moderated_by: Optional[str]
    moderated_at: Optional[datetime]
    moderation_notes: Optional[str]

    class Config:
        from_attributes = True

# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/questions", response_model=ForumQuestionResponse)
async def create_forum_question(
    question_data: ForumQuestionCreate,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new forum question"""
    try:
        user = current_user_data["user"]
        user_type = current_user_data["user_type"]
        
        # Check if user is a patient
        if user_type != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only patients can create forum questions"
            )
        
        # Create new question
        new_question = ForumQuestion(
            title=question_data.title,
            content=question_data.content,
            category=question_data.category,
            is_anonymous=question_data.is_anonymous,
            is_urgent=question_data.is_urgent,
            patient_id=user.id
        )
        
        db.add(new_question)
        db.commit()
        db.refresh(new_question)
        
        # Get author name (handle anonymous case)
        if question_data.is_anonymous:
            author_name = "Anonymous"
        else:
            author_name = f"{user.first_name} {user.last_name}" if user else "Unknown"
        
        # Prepare response
        response_data = ForumQuestionResponse(
            id=str(new_question.id),
            title=new_question.title,
            content=new_question.content,
            category=new_question.category.value,
            author_id=str(new_question.patient_id),
            author_name=author_name,
            is_anonymous=new_question.is_anonymous,
            is_urgent=new_question.is_urgent,
            status=new_question.status.value,
            asked_at=new_question.created_at,
            formatted_date=new_question.created_at.strftime("%B %d, %Y at %I:%M %p"),
            time_ago=get_time_ago(new_question.created_at),
            answers_count=new_question.answer_count,
            views_count=new_question.view_count,
            is_active=not new_question.is_deleted
        )
        
        return response_data
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create forum question: {str(e)}"
        )

@router.get("/questions", response_model=List[ForumQuestionResponse])
async def get_forum_questions(
    category: Optional[QuestionCategory] = None,
    status: Optional[QuestionStatus] = None,
    patient_id: Optional[str] = None,
    bookmarked: Optional[bool] = None,
    needs_moderation: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get forum questions with optional filtering"""
    try:
        query = db.query(ForumQuestion).filter(ForumQuestion.is_deleted == False)
        
        if category:
            query = query.filter(ForumQuestion.category == category)
        
        if status:
            query = query.filter(ForumQuestion.status == status)
        
        # Filter by patient (for "My Questions")
        if patient_id:
            try:
                patient_uuid = uuid.UUID(patient_id)
                query = query.filter(ForumQuestion.patient_id == patient_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid patient ID format"
                )
        
        # Filter bookmarked questions
        if bookmarked:
            from models.sql_models.forum_models import ForumBookmark
            bookmarked_question_ids = db.query(ForumBookmark.question_id).filter(
                ForumBookmark.patient_id == patient_id if patient_id else True
            ).subquery()
            query = query.filter(ForumQuestion.id.in_(bookmarked_question_ids))
        
        # Filter questions that need moderation
        if needs_moderation:
            query = query.filter(ForumQuestion.is_flagged == True)
        
        questions = query.order_by(ForumQuestion.created_at.desc()).offset(offset).limit(limit).all()
        
        response_data = []
        for question in questions:
            # Get author name (handle anonymous case)
            if question.is_anonymous:
                author_name = "Anonymous"
            else:
                patient = db.query(Patient).filter(Patient.id == question.patient_id).first()
                author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
            
            response_data.append(ForumQuestionResponse(
                id=str(question.id),
                title=question.title,
                content=question.content,
                category=question.category.value,
                author_id=str(question.patient_id),
                author_name=author_name,
                is_anonymous=question.is_anonymous,
                is_urgent=question.is_urgent,
                status=question.status.value,
                asked_at=question.created_at,
                formatted_date=question.created_at.strftime("%B %d, %Y at %I:%M %p"),
                time_ago=get_time_ago(question.created_at),
                answers_count=question.answer_count,
                views_count=question.view_count,
                is_active=not question.is_deleted
            ))
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch forum questions: {str(e)}"
        )

@router.get("/questions/{question_id}", response_model=ForumQuestionResponse)
async def get_forum_question(
    question_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific forum question by ID"""
    try:
        question = db.query(ForumQuestion).filter(
            ForumQuestion.id == question_id,
            ForumQuestion.is_deleted == False
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Increment view count
        question.view_count += 1
        db.commit()
        
        # Get author name (handle anonymous case)
        if question.is_anonymous:
            author_name = "Anonymous"
        else:
            patient = db.query(Patient).filter(Patient.id == question.patient_id).first()
            author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
        
        return ForumQuestionResponse(
            id=str(question.id),
            title=question.title,
            content=question.content,
            category=question.category.value,
            author_id=str(question.patient_id),
            author_name=author_name,
            is_anonymous=question.is_anonymous,
            is_urgent=question.is_urgent,
            status=question.status.value,
            asked_at=question.created_at,
            formatted_date=question.created_at.strftime("%B %d, %Y at %I:%M %p"),
            time_ago=get_time_ago(question.created_at),
            answers_count=question.answer_count,
            views_count=question.view_count,
            is_active=not question.is_deleted
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch question: {str(e)}"
        )

@router.put("/questions/{question_id}", response_model=ForumQuestionResponse)
async def update_forum_question(
    question_id: str,
    question_data: ForumQuestionUpdate,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update an existing forum question"""
    try:
        user = current_user_data["user"]
        
        question = db.query(ForumQuestion).filter(
            ForumQuestion.id == question_id,
            ForumQuestion.patient_id == user.id,
            ForumQuestion.is_deleted == False
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found or you don't have permission to edit it"
            )
        
        # Update fields
        if question_data.title is not None:
            question.title = question_data.title
        if question_data.content is not None:
            question.content = question_data.content
        if question_data.category is not None:
            question.category = question_data.category
        if question_data.is_anonymous is not None:
            question.is_anonymous = question_data.is_anonymous
        if question_data.is_urgent is not None:
            question.is_urgent = question_data.is_urgent
        
        db.commit()
        db.refresh(question)
        
        # Get author name (handle anonymous case)
        if question.is_anonymous:
            author_name = "Anonymous"
        else:
            patient = db.query(Patient).filter(Patient.id == question.patient_id).first()
            author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
        
        return ForumQuestionResponse(
            id=str(question.id),
            title=question.title,
            content=question.content,
            category=question.category.value,
            author_id=str(question.patient_id),
            author_name=author_name,
            is_anonymous=question.is_anonymous,
            is_urgent=question.is_urgent,
            status=question.status.value,
            asked_at=question.created_at,
            formatted_date=question.created_at.strftime("%B %d, %Y at %I:%M %p"),
            time_ago=get_time_ago(question.created_at),
            answers_count=question.answer_count,
            views_count=question.view_count,
            is_active=not question.is_deleted
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update question: {str(e)}"
        )

@router.delete("/questions/{question_id}")
async def delete_forum_question(
    question_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a forum question"""
    try:
        user = current_user_data["user"]
        
        question = db.query(ForumQuestion).filter(
            ForumQuestion.id == question_id,
            ForumQuestion.patient_id == user.id,
            ForumQuestion.is_deleted == False
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found or you don't have permission to delete it"
            )
        
        # Soft delete
        question.is_deleted = True
        db.commit()
        
        return {"message": "Question deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete question: {str(e)}"
        )

@router.post("/questions/{question_id}/answers", response_model=ForumAnswerResponse)
async def create_forum_answer(
    question_id: str,
    answer_data: ForumAnswerCreate,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new answer to a forum question (specialists only)"""
    try:
        user = current_user_data["user"]
        
        # Check if user is a specialist
        specialist = db.query(Specialists).filter(
            Specialists.id == user.id,
            Specialists.is_deleted == False
        ).first()
        
        if not specialist:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only specialists can answer questions"
            )
        
        # Check if question exists and is active
        question = db.query(ForumQuestion).filter(
            ForumQuestion.id == question_id,
            ForumQuestion.is_deleted == False
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Create new answer
        new_answer = ForumAnswer(
            question_id=question_id,
            specialist_id=user.id,
            content=answer_data.content
        )
        
        db.add(new_answer)
        
        # Update question status and answers count
        question.status = QuestionStatus.ANSWERED
        question.answer_count += 1
        
        db.commit()
        db.refresh(new_answer)
        
        # Get specialist name
        specialist_name = f"{specialist.first_name} {specialist.last_name}" if specialist else "Unknown"
        
        return ForumAnswerResponse(
            id=str(new_answer.id),
            question_id=str(new_answer.question_id),
            content=new_answer.content,
            specialist_id=str(new_answer.specialist_id),
            specialist_name=specialist_name,
            answered_at=new_answer.created_at,
            time_ago=get_time_ago(new_answer.created_at),
            status=new_answer.status.value,
            is_active=new_answer.is_deleted == False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create answer: {str(e)}"
        )

@router.get("/questions/{question_id}/answers", response_model=List[ForumAnswerResponse])
async def get_forum_answers(
    question_id: str,
    db: Session = Depends(get_db)
):
    """Get all answers for a specific question"""
    try:
        answers = db.query(ForumAnswer).filter(
            ForumAnswer.question_id == question_id,
            ForumAnswer.is_deleted == False
        ).order_by(ForumAnswer.created_at.asc()).all()
        
        response_data = []
        for answer in answers:
            specialist = db.query(Specialists).filter(Specialists.id == answer.specialist_id).first()
            specialist_name = f"{specialist.first_name} {specialist.last_name}" if specialist else "Unknown"
            
            response_data.append(ForumAnswerResponse(
                id=str(answer.id),
                question_id=str(answer.question_id),
                content=answer.content,
                specialist_id=str(answer.specialist_id),
                specialist_name=specialist_name,
                answered_at=answer.created_at,
                time_ago=get_time_ago(answer.created_at),
                status=answer.status.value,
                is_active=answer.is_deleted == False
            ))
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch answers: {str(e)}"
        )

@router.put("/answers/{answer_id}", response_model=ForumAnswerResponse)
async def update_forum_answer(
    answer_id: str,
    answer_data: ForumAnswerUpdate,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update an existing forum answer"""
    try:
        user = current_user_data["user"]
        
        answer = db.query(ForumAnswer).filter(
            ForumAnswer.id == answer_id,
            ForumAnswer.specialist_id == user.id,
            ForumAnswer.is_deleted == False
        ).first()
        
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found or you don't have permission to edit it"
            )
        
        # Update content
        answer.content = answer_data.content
        
        db.commit()
        db.refresh(answer)
        
        # Get specialist name
        specialist = db.query(Specialists).filter(Specialists.id == answer.specialist_id).first()
        specialist_name = f"{specialist.first_name} {specialist.last_name}" if specialist else "Unknown"
        
        return ForumAnswerResponse(
            id=str(answer.id),
            question_id=str(answer.question_id),
            content=answer.content,
            specialist_id=str(answer.specialist_id),
            specialist_name=specialist_name,
            answered_at=answer.created_at,
            time_ago=get_time_ago(answer.created_at),
            status=answer.status.value,
            is_active=answer.is_deleted == False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update answer: {str(e)}"
        )

@router.delete("/answers/{answer_id}")
async def delete_forum_answer(
    answer_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Delete a forum answer"""
    try:
        user = current_user_data["user"]
        
        answer = db.query(ForumAnswer).filter(
            ForumAnswer.id == answer_id,
            ForumAnswer.specialist_id == user.id,
            ForumAnswer.is_deleted == False
        ).first()
        
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found or you don't have permission to delete it"
            )
        
        # Soft delete
        answer.is_deleted = True
        
        # Update question answers count
        question = db.query(ForumQuestion).filter(ForumQuestion.id == answer.question_id).first()
        if question and question.answer_count > 0:
            question.answer_count -= 1
            # Update status if no more answers
            if question.answer_count == 0:
                question.status = QuestionStatus.OPEN
        
        db.commit()
        
        return {"message": "Answer deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete answer: {str(e)}"
        )

# ============================================================================
# BOOKMARK ENDPOINTS
# ============================================================================

@router.post("/questions/{question_id}/bookmark")
async def bookmark_question(
    question_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Bookmark a question for the current patient"""
    try:
        user = current_user_data["user"]
        user_type = current_user_data["user_type"]
        
        # Only patients can bookmark questions
        if user_type != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only patients can bookmark questions"
            )
        
        # Check if question exists
        question = db.query(ForumQuestion).filter(
            ForumQuestion.id == question_id,
            ForumQuestion.is_deleted == False
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Check if already bookmarked
        from models.sql_models.forum_models import ForumBookmark
        existing_bookmark = db.query(ForumBookmark).filter(
            ForumBookmark.patient_id == user.id,
            ForumBookmark.question_id == question_id
        ).first()
        
        if existing_bookmark:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question is already bookmarked"
            )
        
        # Create bookmark
        new_bookmark = ForumBookmark(
            patient_id=user.id,
            question_id=question_id
        )
        
        db.add(new_bookmark)
        db.commit()
        
        return {"message": "Question bookmarked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bookmark question: {str(e)}"
        )

@router.delete("/questions/{question_id}/bookmark")
async def unbookmark_question(
    question_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Remove bookmark from a question"""
    try:
        user = current_user_data["user"]
        user_type = current_user_data["user_type"]
        
        # Only patients can unbookmark questions
        if user_type != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only patients can unbookmark questions"
            )
        
        # Find and delete bookmark
        from models.sql_models.forum_models import ForumBookmark
        bookmark = db.query(ForumBookmark).filter(
            ForumBookmark.patient_id == user.id,
            ForumBookmark.question_id == question_id
        ).first()
        
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        
        db.delete(bookmark)
        db.commit()
        
        return {"message": "Bookmark removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove bookmark: {str(e)}"
        )

@router.get("/questions/{question_id}/bookmark")
async def check_bookmark_status(
    question_id: str,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Check if a question is bookmarked by the current user"""
    try:
        user = current_user_data["user"]
        user_type = current_user_data["user_type"]
        
        # Only patients can check bookmark status
        if user_type != "patient":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only patients can check bookmark status"
            )
        
        # Check if bookmarked
        from models.sql_models.forum_models import ForumBookmark
        bookmark = db.query(ForumBookmark).filter(
            ForumBookmark.patient_id == user.id,
            ForumBookmark.question_id == question_id
        ).first()
        
        return {"is_bookmarked": bookmark is not None}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check bookmark status: {str(e)}"
        )

# ============================================================================
# MODERATION ENDPOINTS
# ============================================================================

@router.get("/moderation/queue")
async def get_moderation_queue(
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get questions that need moderation (admin/moderator only)"""
    try:
        user = current_user_data["user"]
        user_type = current_user_data["user_type"]
        
        # Only admins and moderators can access moderation queue
        if user_type not in ["admin", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin or moderator privileges required."
            )
        
        # Get flagged questions
        flagged_questions = db.query(ForumQuestion).filter(
            ForumQuestion.is_flagged == True,
            ForumQuestion.is_deleted == False
        ).order_by(ForumQuestion.moderated_at.desc()).all()
        
        response_data = []
        for question in flagged_questions:
            # Get author name (handle anonymous case)
            if question.is_anonymous:
                author_name = "Anonymous"
            else:
                patient = db.query(Patient).filter(Patient.id == question.patient_id).first()
                author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
            
            response_data.append(ForumQuestionResponse(
                id=str(question.id),
                title=question.title,
                content=question.content,
                category=question.category.value,
                author_id=str(question.patient_id),
                author_name=author_name,
                is_anonymous=question.is_anonymous,
                is_urgent=question.is_urgent,
                status=question.status.value,
                asked_at=question.created_at,
                formatted_date=question.created_at.strftime("%B %d, %Y at %I:%M %p"),
                time_ago=get_time_ago(question.created_at),
                answers_count=question.answer_count,
                views_count=question.view_count,
                is_active=not question.is_deleted
            ))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch moderation queue: {str(e)}"
        )

@router.post("/questions/{question_id}/moderate")
async def moderate_question(
    question_id: str,
    action: str,  # "approve", "remove", "flag"
    reason: Optional[str] = None,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Moderate a question (admin/moderator only)"""
    try:
        user = current_user_data["user"]
        user_type = current_user_data["user_type"]
        
        # Only admins and moderators can moderate
        if user_type not in ["admin", "moderator"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Admin or moderator privileges required."
            )
        
        # Get question
        question = db.query(ForumQuestion).filter(
            ForumQuestion.id == question_id,
            ForumQuestion.is_deleted == False
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Apply moderation action
        if action == "approve":
            question.unflag_question()
        elif action == "remove":
            question.soft_delete()
        elif action == "flag":
            question.flag_question(reason or "Flagged by moderator", user.id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid action. Must be 'approve', 'remove', or 'flag'"
            )
        
        db.commit()
        
        return {"message": f"Question {action}ed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to moderate question: {str(e)}"
        )

# ============================================================================
# REPORTS ENDPOINT
# ============================================================================

@router.post("/reports", response_model=ForumReportResponse)
async def create_forum_report(
    report_data: ForumReportCreate,
    current_user_data: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Create a new forum report"""
    try:
        user = current_user_data["user"]
        user_type = current_user_data["user_type"]
        
        # Validate post type
        if report_data.post_type not in ["question", "answer"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Post type must be 'question' or 'answer'"
            )
        
        # Check if post exists
        if report_data.post_type == "question":
            post = db.query(ForumQuestion).filter(
                ForumQuestion.id == report_data.post_id,
                ForumQuestion.is_deleted == False
            ).first()
        else:  # answer
            post = db.query(ForumAnswer).filter(
                ForumAnswer.id == report_data.post_id,
                ForumAnswer.is_deleted == False
            ).first()
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{report_data.post_type.capitalize()} not found"
            )
        
        # Check if user already reported this post
        existing_report = db.query(ForumReport).filter(
            ForumReport.post_id == report_data.post_id,
            ForumReport.post_type == report_data.post_type,
            ForumReport.status == "pending"
        ).first()
        
        if existing_report:
            # Check if it's the same user reporting
            if user_type == "patient" and existing_report.reporter_id == user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already reported this post"
                )
            elif user_type == "specialist" and existing_report.specialist_reporter_id == user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You have already reported this post"
                )
        
        # Create new report
        new_report = ForumReport(
            post_id=report_data.post_id,
            post_type=report_data.post_type,
            reason=report_data.reason
        )
        
        # Set reporter based on user type
        if user_type == "patient":
            new_report.reporter_id = user.id
        elif user_type == "specialist":
            new_report.specialist_reporter_id = user.id
        
        db.add(new_report)
        db.commit()
        db.refresh(new_report)
        
        # Prepare response
        return ForumReportResponse(
            id=str(new_report.id),
            post_id=str(new_report.post_id),
            post_type=new_report.post_type,
            reason=new_report.reason,
            status=new_report.status,
            reporter_name=new_report.reporter_name,
            reporter_type=new_report.reporter_type,
            created_at=new_report.created_at,
            moderated_by=None,
            moderated_at=None,
            moderation_notes=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report: {str(e)}"
        )


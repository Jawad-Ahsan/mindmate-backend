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
from models.sql_models.forum_models import ForumQuestion, ForumAnswer, QuestionCategory, QuestionStatus, AnswerStatus
from models.sql_models.patient_models import Patient
from models.sql_models.specialist_models import Specialists

router = APIRouter(prefix="/forum", tags=["Forum"])

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

from pydantic import BaseModel, Field

class ForumQuestionCreate(BaseModel):
    """Create a new forum question"""
    title: str = Field(..., min_length=1, max_length=200, description="Question title")
    content: str = Field(..., min_length=1, description="Question content")
    category: QuestionCategory = Field(QuestionCategory.GENERAL, description="Question category")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    is_anonymous: bool = Field(False, description="Whether to post anonymously")

class ForumQuestionUpdate(BaseModel):
    """Update an existing forum question"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Question title")
    content: Optional[str] = Field(None, min_length=1, description="Question content")
    category: Optional[QuestionCategory] = Field(None, description="Question category")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")

class ForumQuestionResponse(BaseModel):
    """Forum question response model"""
    id: str
    title: str
    content: str
    category: str
    tags: Optional[str]
    author_id: str
    author_name: str
    is_anonymous: bool
    status: str
    asked_at: datetime
    formatted_date: str
    time_ago: str
    answers_count: int
    views_count: int
    is_active: bool
    is_featured: bool

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
    is_best_answer: bool

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
        
        # Create new question
        new_question = ForumQuestion(
            title=question_data.title,
            content=question_data.content,
            category=question_data.category,
            tags=question_data.tags,
            is_anonymous=question_data.is_anonymous,
            author_id=user["id"]
        )
        
        db.add(new_question)
        db.commit()
        db.refresh(new_question)
        
        # Get author name (handle anonymous case)
        if question_data.is_anonymous:
            author_name = "Anonymous"
        else:
            patient = db.query(Patient).filter(Patient.id == user["id"]).first()
            author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
        
        # Prepare response
        response_data = ForumQuestionResponse(
            id=str(new_question.id),
            title=new_question.title,
            content=new_question.content,
            category=new_question.category.value,
            tags=new_question.tags,
            author_id=str(new_question.author_id),
            author_name=author_name,
            is_anonymous=new_question.is_anonymous,
            status=new_question.status.value,
            asked_at=new_question.asked_at,
            formatted_date=new_question.formatted_date,
            time_ago=new_question.time_ago,
            answers_count=new_question.answers_count,
            views_count=new_question.views_count,
            is_active=new_question.is_active,
            is_featured=new_question.is_featured
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
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get forum questions with optional filtering"""
    try:
        query = db.query(ForumQuestion).filter(ForumQuestion.is_active == True)
        
        if category:
            query = query.filter(ForumQuestion.category == category)
        
        if status:
            query = query.filter(ForumQuestion.status == status)
        
        questions = query.order_by(ForumQuestion.asked_at.desc()).offset(offset).limit(limit).all()
        
        response_data = []
        for question in questions:
            # Get author name (handle anonymous case)
            if question.is_anonymous:
                author_name = "Anonymous"
            else:
                patient = db.query(Patient).filter(Patient.id == question.author_id).first()
                author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
            
            response_data.append(ForumQuestionResponse(
                id=str(question.id),
                title=question.title,
                content=question.content,
                category=question.category.value,
                tags=question.tags,
                author_id=str(question.author_id),
                author_name=author_name,
                is_anonymous=question.is_anonymous,
                status=question.status.value,
                asked_at=question.asked_at,
                formatted_date=question.formatted_date,
                time_ago=question.time_ago,
                answers_count=question.answers_count,
                views_count=question.views_count,
                is_active=question.is_active,
                is_featured=question.is_featured
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
            ForumQuestion.is_active == True
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Increment view count
        question.views_count += 1
        db.commit()
        
        # Get author name (handle anonymous case)
        if question.is_anonymous:
            author_name = "Anonymous"
        else:
            patient = db.query(Patient).filter(Patient.id == question.author_id).first()
            author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
        
        return ForumQuestionResponse(
            id=str(question.id),
            title=question.title,
            content=question.content,
            category=question.category.value,
            tags=question.tags,
            author_id=str(question.author_id),
            author_name=author_name,
            is_anonymous=question.is_anonymous,
            status=question.status.value,
            asked_at=question.asked_at,
            formatted_date=question.formatted_date,
            time_ago=question.time_ago,
            answers_count=question.answers_count,
            views_count=question.views_count,
            is_active=question.is_active,
            is_featured=question.is_featured
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
            ForumQuestion.author_id == user["id"],
            ForumQuestion.is_active == True
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
        if question_data.tags is not None:
            question.tags = question_data.tags
        
        db.commit()
        db.refresh(question)
        
        # Get author name (handle anonymous case)
        if question.is_anonymous:
            author_name = "Anonymous"
        else:
            patient = db.query(Patient).filter(Patient.id == question.author_id).first()
            author_name = f"{patient.first_name} {patient.last_name}" if patient else "Unknown"
        
        return ForumQuestionResponse(
            id=str(question.id),
            title=question.title,
            content=question.content,
            category=question.category.value,
            tags=question.tags,
            author_id=str(question.author_id),
            author_name=author_name,
            is_anonymous=question.is_anonymous,
            status=question.status.value,
            asked_at=question.asked_at,
            formatted_date=question.formatted_date,
            time_ago=question.time_ago,
            answers_count=question.answers_count,
            views_count=question.views_count,
            is_active=question.is_active,
            is_featured=question.is_featured
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
            ForumQuestion.author_id == user["id"],
            ForumQuestion.is_active == True
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found or you don't have permission to delete it"
            )
        
        # Soft delete
        question.is_active = False
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
            Specialists.id == user["id"],
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
            ForumQuestion.is_active == True
        ).first()
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Create new answer
        new_answer = ForumAnswer(
            question_id=question_id,
            specialist_id=user["id"],
            content=answer_data.content
        )
        
        db.add(new_answer)
        
        # Update question status and answers count
        question.status = QuestionStatus.ANSWERED
        question.answers_count += 1
        
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
            answered_at=new_answer.answered_at,
            time_ago=new_answer.time_ago,
            status=new_answer.status.value,
            is_active=new_answer.is_active,
            is_best_answer=new_answer.is_best_answer
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
            ForumAnswer.is_active == True
        ).order_by(ForumAnswer.answered_at.asc()).all()
        
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
                answered_at=answer.answered_at,
                time_ago=answer.time_ago,
                status=answer.status.value,
                is_active=answer.is_active,
                is_best_answer=answer.is_best_answer
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
            ForumAnswer.specialist_id == user["id"],
            ForumAnswer.is_active == True
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
            answered_at=answer.answered_at,
            time_ago=answer.time_ago,
            status=answer.status.value,
            is_active=answer.is_active,
            is_best_answer=answer.is_best_answer
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
            ForumAnswer.specialist_id == user["id"],
            ForumAnswer.is_active == True
        ).first()
        
        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found or you don't have permission to delete it"
            )
        
        # Soft delete
        answer.is_active = False
        
        # Update question answers count
        question = db.query(ForumQuestion).filter(ForumQuestion.id == answer.question_id).first()
        if question and question.answers_count > 0:
            question.answers_count -= 1
            # Update status if no more answers
            if question.answers_count == 0:
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


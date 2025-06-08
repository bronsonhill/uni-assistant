import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..exceptions.business_exceptions import (
    ValidationError,
    QuestionNotFoundError,
    UnauthorizedAccessError,
    DuplicateQuestionError,
    DatabaseError,
    ResourceNotFoundError
)
from data.repositories.question_repository import QuestionRepository

logger = logging.getLogger(__name__)

class QuestionService:
    """Service class for managing questions."""

    def __init__(self, question_repository: QuestionRepository):
        self.question_repository = question_repository

    def _validate_question_input(self, subject: Optional[str], week: Optional[int],
                               question: str, answer: str, email: Optional[str]) -> None:
        """Validate question input data"""
        if subject is not None and not subject.strip():
            raise ValidationError("Subject cannot be empty")
            
        if week is not None and not (1 <= week <= 52):
            raise ValidationError("Week must be between 1 and 52")
            
        if not question.strip():
            raise ValidationError("Question cannot be empty")
            
        if not answer.strip():
            raise ValidationError("Answer cannot be empty")
            
        if email is not None and not "@" in email:
            raise ValidationError("Invalid email format")

    def add_question(self, subject: str, week: int, question: str, answer: str, email: str) -> str:
        """Add a new question"""
        self._validate_question_input(subject, week, question, answer, email)
        
        try:
            question_data = {
                "subject": subject,
                "week": week,
                "question": question,
                "answer": answer,
                "email": email,
                "scores": [],
                "last_practiced": None,
                "created_at": datetime.now()
            }
            return self.question_repository.create(question_data)
        except Exception as e:
            raise DatabaseError(f"Failed to add question: {str(e)}", "CREATE")

    def update_question(self, id: str, question: str, answer: str) -> bool:
        """Update an existing question"""
        self._validate_question_input(None, None, question, answer, None)
        
        try:
            question_data = {
                "question": question,
                "answer": answer,
                "updated_at": datetime.now()
            }
            return self.question_repository.update(id, question_data)
        except Exception as e:
            raise DatabaseError(f"Failed to update question: {str(e)}", "UPDATE")

    def delete_question(self, id: str) -> bool:
        """Delete a question"""
        try:
            return self.question_repository.delete(id)
        except Exception as e:
            raise DatabaseError(f"Failed to delete question: {str(e)}", "DELETE")

    def get_question(self, id: str) -> Optional[Dict]:
        """Get a question by ID"""
        try:
            question = self.question_repository.find_by_id(id)
            if not question:
                raise ResourceNotFoundError(f"Question {id} not found")
            return question
        except Exception as e:
            raise DatabaseError(f"Failed to get question: {str(e)}", "READ")

    def get_questions_by_subject_week(self, subject: str, week: int) -> List[Dict]:
        """Get questions by subject and week"""
        try:
            return self.question_repository.find_by_subject_week(subject, week)
        except Exception as e:
            raise DatabaseError(f"Failed to get questions: {str(e)}", "READ")

    def get_questions_by_user(self, email: str) -> List[Dict]:
        """Get questions by user email"""
        try:
            return self.question_repository.find_by_user(email)
        except Exception as e:
            raise DatabaseError(f"Failed to get questions: {str(e)}", "READ")

    def update_question_score(self, id: str, score: float) -> bool:
        """Update question score"""
        if not 0 <= score <= 1:
            raise ValidationError("Score must be between 0 and 1")
            
        try:
            return self.question_repository.update_score(id, score)
        except Exception as e:
            raise DatabaseError(f"Failed to update score: {str(e)}", "UPDATE")

    def get_all_questions(self, email: str) -> List[Dict[str, Any]]:
        """
        Get all questions for a user.
        
        Args:
            email: User's email
            
        Returns:
            List of all questions for user
            
        Raises:
            ValidationError: If input validation fails
            DatabaseError: If database operation fails
        """
        try:
            logger.info(f"Getting all questions for {email}")
            
            # Validate email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                raise ValidationError("Invalid email format")
            
            # Get questions
            return self.question_repository.find_by_user(email)
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting questions: {str(e)}")
            raise DatabaseError(f"Failed to get questions: {str(e)}") 
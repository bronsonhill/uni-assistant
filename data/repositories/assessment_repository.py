from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from .base_repository import BaseRepository

class AssessmentRepository(BaseRepository):
    """Repository interface for assessment-related operations."""
    
    def __init__(self):
        """Initialize the assessment repository."""
        super().__init__("assessments")
    
    def _validate_assessment(self, assessment: Dict[str, Any]) -> bool:
        """Validate assessment data.
        
        Args:
            assessment (Dict[str, Any]): Assessment data to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If assessment data is invalid
        """
        required_fields = ["subject", "week", "questions", "email", "start_time"]
        if not all(field in assessment for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")
        
        if not isinstance(assessment["questions"], list):
            raise ValueError("Questions must be a list")
        
        if not isinstance(assessment["start_time"], datetime):
            raise ValueError("Start time must be a datetime object")
        
        return True
    
    @abstractmethod
    def find_by_user(self, email: str) -> List[Dict[str, Any]]:
        """Find all assessments for a user.
        
        Args:
            email (str): User email
            
        Returns:
            List[Dict[str, Any]]: List of user's assessments
        """
        pass
    
    @abstractmethod
    def find_by_subject_week(self, subject: str, week: int, email: str) -> List[Dict[str, Any]]:
        """Find assessments by subject and week.
        
        Args:
            subject (str): Subject name
            week (int): Week number
            email (str): User email
            
        Returns:
            List[Dict[str, Any]]: List of matching assessments
        """
        pass
    
    @abstractmethod
    def update_score(self, id: str, score: float, answers: List[Dict[str, Any]]) -> bool:
        """Update assessment score and answers.
        
        Args:
            id (str): Assessment ID
            score (float): Final score (0-1)
            answers (List[Dict[str, Any]]): User's answers
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If score is invalid
        """
        pass
    
    @abstractmethod
    def get_assessment_stats(self, email: str) -> Dict[str, Any]:
        """Get assessment statistics for a user.
        
        Args:
            email (str): User email
            
        Returns:
            Dict[str, Any]: Assessment statistics including:
                - total_assessments: int
                - average_score: float
                - subject_scores: Dict[str, float]
                - weekly_progress: Dict[int, float]
        """
        pass
    
    @abstractmethod
    def get_recent_assessments(self, email: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent assessments for a user.
        
        Args:
            email (str): User email
            limit (int): Maximum number of assessments to return
            
        Returns:
            List[Dict[str, Any]]: List of recent assessments
        """
        pass
    
    @abstractmethod
    def get_incomplete_assessments(self, email: str) -> List[Dict[str, Any]]:
        """Get incomplete assessments for a user.
        
        Args:
            email (str): User email
            
        Returns:
            List[Dict[str, Any]]: List of incomplete assessments
        """
        pass
    
    @abstractmethod
    def get_assessment_analytics(self, email: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed assessment analytics.
        
        Args:
            email (str): User email
            days (int): Number of days to analyze
            
        Returns:
            Dict[str, Any]: Analytics including:
                - completion_rate: float
                - average_time: float
                - question_accuracy: Dict[str, float]
                - improvement_rate: float
        """
        pass 
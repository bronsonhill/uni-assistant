from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from .base_repository import BaseRepository
from mongodb.connection import get_collection

class QuestionRepository(BaseRepository):
    """Repository interface for question-related operations."""
    
    def __init__(self):
        """Initialize the question repository."""
        super().__init__("questions")
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """Validate question data.
        
        Args:
            question (Dict[str, Any]): Question data to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If question data is invalid
        """
        required_fields = ["subject", "week", "question", "answer", "email"]
        if not all(field in question for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")
        
        if not isinstance(question["week"], int) or question["week"] < 1 or question["week"] > 52:
            raise ValueError("Week must be an integer between 1 and 52")
        
        if not isinstance(question["question"], str) or len(question["question"]) > 1000:
            raise ValueError("Question must be a string with maximum length of 1000")
        
        if not isinstance(question["answer"], str) or len(question["answer"]) > 2000:
            raise ValueError("Answer must be a string with maximum length of 2000")
        
        return True
    
    @abstractmethod
    def find_by_subject_week(self, subject: str, week: int, email: str) -> List[Dict[str, Any]]:
        """Find questions by subject and week.
        
        Args:
            subject (str): Subject name
            week (int): Week number
            email (str): User email
            
        Returns:
            List[Dict[str, Any]]: List of matching questions
        """
        pass
    
    @abstractmethod
    def find_by_user(self, email: str) -> List[Dict[str, Any]]:
        """Find all questions for a user.
        
        Args:
            email (str): User email
            
        Returns:
            List[Dict[str, Any]]: List of user's questions
        """
        pass
    
    @abstractmethod
    def update_score(self, id: str, score: float, user_answer: str) -> bool:
        """Update question score and user answer.
        
        Args:
            id (str): Question ID
            score (float): New score (0-1)
            user_answer (str): User's answer
            
        Returns:
            bool: True if successful
            
        Raises:
            ValueError: If score is invalid
        """
        pass
    
    @abstractmethod
    def get_subject_stats(self, subject: str, email: str) -> Dict[str, Any]:
        """Get statistics for a subject.
        
        Args:
            subject (str): Subject name
            email (str): User email
            
        Returns:
            Dict[str, Any]: Subject statistics including:
                - total_questions: int
                - average_score: float
                - weekly_scores: Dict[int, float]
                - weak_areas: List[str]
        """
        pass
    
    @abstractmethod
    def get_weak_areas(self, email: str, subject: Optional[str] = None) -> List[str]:
        """Get weak areas for a user.
        
        Args:
            email (str): User email
            subject (Optional[str]): Optional subject filter
            
        Returns:
            List[str]: List of weak areas
        """
        pass
    
    @abstractmethod
    def get_recent_questions(self, email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently practiced questions.
        
        Args:
            email (str): User email
            limit (int): Maximum number of questions to return
            
        Returns:
            List[Dict[str, Any]]: List of recent questions
        """
        pass

class MongoDBQuestionRepository(QuestionRepository):
    """MongoDB implementation of the question repository."""
    
    def __init__(self, db_client):
        """Initialize the MongoDB question repository."""
        super().__init__()
        self.db = db_client[self.collection_name]
    
    def find_by_id(self, id: str) -> Optional[Dict]:
        """Find a question by ID."""
        self._validate_id(id)
        return self.db.find_one({"_id": ObjectId(id)})
    
    def find_all(self, filters: Dict = None) -> List[Dict]:
        """Find all questions matching optional filters."""
        query = filters or {}
        return list(self.db.find(query))
    
    def create(self, data: Dict) -> str:
        """Create a new question."""
        self._validate_question(data)
        data = self._add_timestamps(data)
        result = self.db.insert_one(data)
        return str(result.inserted_id)
    
    def update(self, id: str, data: Dict) -> bool:
        """Update a question by ID."""
        self._validate_id(id)
        data = self._add_timestamps(data)
        result = self.db.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0
    
    def delete(self, id: str) -> bool:
        """Delete a question by ID."""
        self._validate_id(id)
        result = self.db.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0
    
    def exists(self, id: str) -> bool:
        """Check if a question exists."""
        self._validate_id(id)
        return self.db.count_documents({"_id": ObjectId(id)}) > 0
    
    def find_by_subject_week(self, subject: str, week: int, email: str) -> List[Dict[str, Any]]:
        """Find questions by subject and week."""
        query = {
            "subject": subject,
            "week": week,
            "email": email
        }
        return list(self.db.find(query))
    
    def find_by_user(self, email: str) -> List[Dict[str, Any]]:
        """Find all questions for a user."""
        return list(self.db.find({"email": email}))
    
    def update_score(self, subject: str, week: str, idx: int, score_entry: Dict, email: str = None) -> Dict:
        """Update question score and user answer.
        
        Args:
            subject: Subject name
            week: Week number
            idx: Question index
            score_entry: Score entry dictionary with score, timestamp, and optional user_answer
            email: User email
            
        Returns:
            Dict: Updated data dictionary
            
        Raises:
            ValueError: If inputs are invalid
        """
        try:
            # Validate inputs
            if not isinstance(score_entry, dict) or "score" not in score_entry or "timestamp" not in score_entry:
                raise ValueError("Invalid score entry format")
                
            # Build the query
            query = {
                "subject": subject,
                "week": week
            }
            if email:
                query["email"] = email
                
            # Find the document
            doc = self.db.find_one(query)
            
            if not doc:
                # Create new document if it doesn't exist
                doc = {
                    "subject": subject,
                    "week": week,
                    "email": email,
                    "questions": [],
                    "updated_at": score_entry["timestamp"]
                }
                self.db.insert_one(doc)
            
            # Ensure we have enough slots for the question index
            questions = doc.get("questions", [])
            while len(questions) <= idx:
                questions.append({"scores": [], "last_practiced": None})
            
            # Initialize scores array if needed
            if "scores" not in questions[idx]:
                questions[idx]["scores"] = []
            
            # Add the new score entry
            questions[idx]["scores"].append(score_entry)
            questions[idx]["last_practiced"] = score_entry["timestamp"]
            
            # Update the document
            self.db.update_one(
                query,
                {
                    "$set": {
                        "questions": questions,
                        "updated_at": score_entry["timestamp"]
                    }
                }
            )
            
            # Return the updated data structure
            return {
                subject: {
                    week: questions
                }
            }
            
        except Exception as e:
            raise ValueError(f"Failed to update score: {str(e)}")
    
    def get_subject_stats(self, subject: str, email: str) -> Dict[str, Any]:
        """Get statistics for a subject."""
        pipeline = [
            {"$match": {"subject": subject, "email": email}},
            {"$group": {
                "_id": None,
                "total_questions": {"$sum": 1},
                "average_score": {"$avg": "$scores"},
                "weekly_scores": {"$push": {"week": "$week", "score": "$scores"}}
            }}
        ]
        result = list(self.db.aggregate(pipeline))
        if not result:
            return {
                "total_questions": 0,
                "average_score": 0,
                "weekly_scores": {},
                "weak_areas": []
            }
        
        stats = result[0]
        return {
            "total_questions": stats["total_questions"],
            "average_score": stats["average_score"],
            "weekly_scores": {w["week"]: w["score"] for w in stats["weekly_scores"]},
            "weak_areas": self.get_weak_areas(email, subject)
        }
    
    def get_weak_areas(self, email: str, subject: Optional[str] = None) -> List[str]:
        """Get weak areas for a user."""
        match = {"email": email}
        if subject:
            match["subject"] = subject
        
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": "$subject",
                "average_score": {"$avg": "$scores"}
            }},
            {"$match": {"average_score": {"$lt": 0.6}}}
        ]
        
        results = list(self.db.aggregate(pipeline))
        return [r["_id"] for r in results]
    
    def get_recent_questions(self, email: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently practiced questions."""
        return list(self.db.find(
            {"email": email},
            sort=[("last_practiced", -1)],
            limit=limit
        )) 
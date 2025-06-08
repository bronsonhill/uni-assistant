from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from .base_repository import BaseRepository
from core.exceptions.business_exceptions import DatabaseError

class UserRepository(BaseRepository):
    """Repository interface for user-related operations."""
    
    def __init__(self):
        """Initialize the user repository."""
        super().__init__("users")
    
    def _validate_user(self, user: Dict[str, Any]) -> bool:
        """Validate user data.
        
        Args:
            user (Dict[str, Any]): User data to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If user data is invalid
        """
        required_fields = ["email", "name"]
        if not all(field in user for field in required_fields):
            raise ValueError(f"Missing required fields: {required_fields}")
        
        if not isinstance(user["email"], str) or "@" not in user["email"]:
            raise ValueError("Invalid email format")
        
        if not isinstance(user["name"], str) or len(user["name"]) > 100:
            raise ValueError("Name must be a string with maximum length of 100")
        
        return True
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email.
        
        Args:
            email (str): User email
            
        Returns:
            Optional[Dict[str, Any]]: User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update_last_login(self, email: str) -> bool:
        """Update user's last login timestamp.
        
        Args:
            email (str): User email
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def update_preferences(self, email: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences.
        
        Args:
            email (str): User email
            preferences (Dict[str, Any]): New preferences
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def get_subscription_status(self, email: str) -> Dict[str, Any]:
        """Get user's subscription status.
        
        Args:
            email (str): User email
            
        Returns:
            Dict[str, Any]: Subscription information including:
                - status: str
                - expiry_date: datetime
                - features: List[str]
        """
        pass
    
    @abstractmethod
    def update_subscription(self, email: str, subscription_data: Dict[str, Any]) -> bool:
        """Update user's subscription.
        
        Args:
            email (str): User email
            subscription_data (Dict[str, Any]): New subscription data
            
        Returns:
            bool: True if successful
        """
        pass
    
    @abstractmethod
    def get_user_stats(self, email: str) -> Dict[str, Any]:
        """Get user statistics.
        
        Args:
            email (str): User email
            
        Returns:
            Dict[str, Any]: User statistics including:
                - total_questions: int
                - average_score: float
                - subjects: List[str]
                - last_active: datetime
        """
        pass
    
    @abstractmethod
    def get_active_users(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get list of active users.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            List[Dict[str, Any]]: List of active users
        """
        pass

class MongoDBUserRepository(BaseRepository):
    """MongoDB implementation of user repository"""
    
    def __init__(self, db_client):
        super().__init__("users")
        self.db = db_client.get_database("study_legend")[self.collection_name]

    def find_by_id(self, id: str) -> Optional[Dict]:
        """Find a user by ID"""
        self._validate_id(id)
        return self.db.find_one({"_id": ObjectId(id)})

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email.
        
        Args:
            email (str): User email to search for
            
        Returns:
            Optional[Dict[str, Any]]: User document if found, None otherwise
            
        Raises:
            ValueError: If email is invalid
            DatabaseError: If database operation fails
        """
        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")
            
        if "@" not in email:
            raise ValueError("Invalid email format")
            
        try:
            user = self.db.find_one({"email": email.lower()})
            return user
        except Exception as e:
            raise DatabaseError(f"Failed to find user by email: {str(e)}", "READ")

    def find_all(self, filters: Dict = None) -> List[Dict]:
        """Find all users matching filters"""
        query = filters or {}
        return list(self.db.find(query))

    def create(self, data: Dict) -> str:
        """Create a new user"""
        self._validate_data(data)
        self._validate_user(data)
        result = self.db.insert_one(data)
        return str(result.inserted_id)

    def update(self, id: str, data: Dict) -> bool:
        """Update a user"""
        self._validate_id(id)
        self._validate_data(data)
        result = self.db.update_one(
            {"_id": ObjectId(id)},
            {"$set": data}
        )
        return result.modified_count > 0

    def update_last_login(self, email: str) -> bool:
        """Update user's last login time"""
        result = self.db.update_one(
            {"email": email},
            {"$set": {"last_login": datetime.now()}}
        )
        return result.modified_count > 0

    def delete(self, id: str) -> bool:
        """Delete a user"""
        self._validate_id(id)
        result = self.db.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    def exists(self, id: str) -> bool:
        """Check if a user exists by ID"""
        self._validate_id(id)
        return self.db.count_documents({"_id": ObjectId(id)}) > 0

    def _validate_user(self, user: Dict) -> bool:
        """Validate user data"""
        required_fields = ["email", "name"]
        if not all(field in user for field in required_fields):
            raise ValueError("Missing required fields")
        return True 
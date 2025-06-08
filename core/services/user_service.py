import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import re

from core.models.user import User
from core.exceptions.business_exceptions import (
    ValidationError, UserNotFoundError, SubscriptionError,
    DatabaseError, AuthenticationError, ResourceNotFoundError
)

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing users"""
    
    def __init__(self, user_repository, subscription_repository=None):
        self.user_repository = user_repository
        self.subscription_repository = subscription_repository

    def _validate_email(self, email: str) -> None:
        """Validate email format"""
        if not email or "@" not in email:
            raise ValidationError("Invalid email format")

    def _validate_settings(self, settings: Dict) -> None:
        """Validate user settings"""
        if not isinstance(settings, dict):
            raise ValidationError("Settings must be a dictionary")

    def get_user_profile(self, email: str) -> Dict:
        """Get user profile by email"""
        try:
            user = self.user_repository.find_by_email(email)
            if not user:
                raise ResourceNotFoundError(f"User {email} not found")
            return user
        except Exception as e:
            raise DatabaseError(f"Failed to get user profile: {str(e)}", "READ")

    def update_user_settings(self, email: str, settings: Dict) -> bool:
        """Update user settings"""
        try:
            user = self.user_repository.find_by_email(email)
            if not user:
                raise ResourceNotFoundError(f"User {email} not found")
                
            update_data = {
                "settings": settings,
                "updated_at": datetime.now()
            }
            return self.user_repository.update(user["_id"], update_data)
        except Exception as e:
            raise DatabaseError(f"Failed to update user settings: {str(e)}", "UPDATE")

    def get_subscription_status(self, email: str) -> Dict:
        """Get user's subscription status"""
        try:
            user = self.user_repository.find_by_email(email)
            if not user:
                raise ResourceNotFoundError(f"User {email} not found")
                
            return {
                "status": user.get("subscription_status", "free"),
                "expiry_date": user.get("subscription_expiry"),
                "features": user.get("subscription_features", [])
            }
        except Exception as e:
            raise DatabaseError(f"Failed to get subscription status: {str(e)}", "READ")

    def validate_user_access(self, email: str, feature: str) -> bool:
        """Validate if user has access to a feature"""
        try:
            user = self.user_repository.find_by_email(email)
            if not user:
                raise ResourceNotFoundError(f"User {email} not found")
                
            subscription = self.get_subscription_status(email)
            return feature in subscription["features"]
        except Exception as e:
            raise DatabaseError(f"Failed to validate access: {str(e)}", "READ")

    def update_last_login(self, email: str) -> bool:
        """Update user's last login time"""
        try:
            return self.user_repository.update_last_login(email)
        except Exception as e:
            raise DatabaseError(f"Failed to update last login: {str(e)}", "UPDATE")

    def _get_subscription_features(self, user: User) -> List[str]:
        """Get list of features available to user based on subscription"""
        if not user.is_subscription_active():
            return ['basic']
        
        # Add premium features based on subscription type
        return ['basic', 'premium', 'ai_feedback', 'advanced_analytics']

    def record_login(self, email: str) -> None:
        """
        Record a user login
        
        Args:
            email (str): User's email
            
        Raises:
            ValidationError: If email is invalid
            UserNotFoundError: If user doesn't exist
            DatabaseError: If database operation fails
        """
        try:
            self._validate_email(email)
            user_data = self.user_repository.find_by_email(email)
            if not user_data:
                raise UserNotFoundError(f"User {email} not found")
            
            user = User.from_dict(user_data)
            user.login_count += 1
            user.last_login = datetime.now()
            
            success = self.user_repository.update(email, user.to_dict())
            if not success:
                raise DatabaseError("Failed to record login")
            
            logger.info(f"Recorded login for user {email}")
        except (ValidationError, UserNotFoundError) as e:
            logger.error(f"Error recording login: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Database error recording login: {str(e)}")
            raise DatabaseError(f"Failed to record login: {str(e)}") 
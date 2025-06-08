import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from core.models.user import User
from core.services.user_service import UserService
from core.exceptions.business_exceptions import (
    ValidationError, UserNotFoundError, DatabaseError
)

class TestUserService(unittest.TestCase):
    def setUp(self):
        self.user_repository = Mock()
        self.subscription_repository = Mock()
        self.service = UserService(self.user_repository, self.subscription_repository)
        
        # Sample user data
        self.test_user = User(
            email="test@example.com",
            name="Test User",
            subscription_status=True,
            subscription_end=datetime.now() + timedelta(days=30),
            created_at=datetime.now(),
            last_updated=datetime.now(),
            login_count=0
        )

    def test_validate_email(self):
        # Test valid email
        self.assertTrue(self.service._validate_email("test@example.com"))
        
        # Test invalid emails
        with self.assertRaises(ValidationError):
            self.service._validate_email("")
        with self.assertRaises(ValidationError):
            self.service._validate_email("invalid-email")
        with self.assertRaises(ValidationError):
            self.service._validate_email(None)

    def test_get_user_profile(self):
        # Setup
        self.user_repository.find_by_email.return_value = self.test_user.to_dict()
        
        # Test successful profile retrieval
        profile = self.service.get_user_profile("test@example.com")
        self.assertEqual(profile["email"], "test@example.com")
        self.assertEqual(profile["name"], "Test User")
        
        # Test user not found
        self.user_repository.find_by_email.return_value = None
        with self.assertRaises(UserNotFoundError):
            self.service.get_user_profile("nonexistent@example.com")
        
        # Test database error
        self.user_repository.find_by_email.side_effect = Exception("DB Error")
        with self.assertRaises(DatabaseError):
            self.service.get_user_profile("test@example.com")

    def test_update_user_settings(self):
        # Setup
        self.user_repository.find_by_email.return_value = self.test_user.to_dict()
        self.user_repository.update.return_value = True
        
        # Test successful update
        settings = {"theme": "dark", "notifications": True}
        result = self.service.update_user_settings("test@example.com", settings)
        self.assertTrue(result)
        
        # Test user not found
        self.user_repository.find_by_email.return_value = None
        with self.assertRaises(UserNotFoundError):
            self.service.update_user_settings("nonexistent@example.com", settings)
        
        # Test database error
        self.user_repository.update.return_value = False
        with self.assertRaises(DatabaseError):
            self.service.update_user_settings("test@example.com", settings)

    def test_get_subscription_status(self):
        # Setup
        self.user_repository.find_by_email.return_value = self.test_user.to_dict()
        
        # Test active subscription
        status = self.service.get_subscription_status("test@example.com")
        self.assertEqual(status["status"], "active")
        self.assertIn("premium", status["features"])
        
        # Test inactive subscription
        inactive_user = User(
            email="inactive@example.com",
            subscription_status=False
        )
        self.user_repository.find_by_email.return_value = inactive_user.to_dict()
        status = self.service.get_subscription_status("inactive@example.com")
        self.assertEqual(status["status"], "inactive")
        self.assertEqual(status["features"], ["basic"])

    def test_validate_user_access(self):
        # Setup
        self.user_repository.find_by_email.return_value = self.test_user.to_dict()
        
        # Test premium feature access
        self.assertTrue(self.service.validate_user_access("test@example.com", "premium"))
        
        # Test basic feature access
        self.assertTrue(self.service.validate_user_access("test@example.com", "basic"))
        
        # Test invalid feature
        with self.assertRaises(ValidationError):
            self.service.validate_user_access("test@example.com", "")
        
        # Test user not found
        self.user_repository.find_by_email.return_value = None
        with self.assertRaises(UserNotFoundError):
            self.service.validate_user_access("nonexistent@example.com", "premium")

    def test_record_login(self):
        # Setup
        self.user_repository.find_by_email.return_value = self.test_user.to_dict()
        self.user_repository.update.return_value = True
        
        # Test successful login recording
        self.service.record_login("test@example.com")
        self.user_repository.update.assert_called_once()
        
        # Test user not found
        self.user_repository.find_by_email.return_value = None
        with self.assertRaises(UserNotFoundError):
            self.service.record_login("nonexistent@example.com")
        
        # Test database error
        self.user_repository.update.return_value = False
        with self.assertRaises(DatabaseError):
            self.service.record_login("test@example.com")

if __name__ == '__main__':
    unittest.main() 
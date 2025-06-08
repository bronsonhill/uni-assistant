import unittest
from unittest.mock import Mock, patch
from datetime import datetime

from core.services.question_service import QuestionService
from core.exceptions.business_exceptions import (
    ValidationError,
    QuestionNotFoundError,
    UnauthorizedAccessError,
    DuplicateQuestionError,
    DatabaseError
)

class TestQuestionService(unittest.TestCase):
    def setUp(self):
        self.mock_repository = Mock()
        self.service = QuestionService(self.mock_repository)
        self.test_question = {
            "subject": "Test Subject",
            "week": 1,
            "question": "Test Question",
            "answer": "Test Answer",
            "email": "test@example.com"
        }

    def test_validate_question_input_success(self):
        """Test successful input validation."""
        self.service._validate_question_input(
            self.test_question["subject"],
            self.test_question["week"],
            self.test_question["question"],
            self.test_question["answer"],
            self.test_question["email"]
        )

    def test_validate_question_input_missing_fields(self):
        """Test validation with missing fields."""
        with self.assertRaises(ValidationError):
            self.service._validate_question_input("", 1, "Q", "A", "test@example.com")

    def test_validate_question_input_invalid_week(self):
        """Test validation with invalid week."""
        with self.assertRaises(ValidationError):
            self.service._validate_question_input("Subject", 0, "Q", "A", "test@example.com")

    def test_validate_question_input_invalid_email(self):
        """Test validation with invalid email."""
        with self.assertRaises(ValidationError):
            self.service._validate_question_input("Subject", 1, "Q", "A", "invalid-email")

    def test_add_question_success(self):
        """Test successful question addition."""
        self.mock_repository.find_by_subject_week.return_value = []
        self.mock_repository.create.return_value = "123"

        result = self.service.add_question(
            self.test_question["subject"],
            self.test_question["week"],
            self.test_question["question"],
            self.test_question["answer"],
            self.test_question["email"]
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["question_id"], "123")
        self.mock_repository.create.assert_called_once()

    def test_add_question_duplicate(self):
        """Test adding duplicate question."""
        self.mock_repository.find_by_subject_week.return_value = [self.test_question]

        with self.assertRaises(DuplicateQuestionError):
            self.service.add_question(
                self.test_question["subject"],
                self.test_question["week"],
                self.test_question["question"],
                self.test_question["answer"],
                self.test_question["email"]
            )

    def test_update_question_success(self):
        """Test successful question update."""
        self.mock_repository.find_by_subject_week.return_value = [self.test_question]
        self.mock_repository.update.return_value = True

        result = self.service.update_question(
            self.test_question["subject"],
            self.test_question["week"],
            0,
            "Updated Question",
            "Updated Answer",
            self.test_question["email"]
        )

        self.assertTrue(result)
        self.mock_repository.update.assert_called_once()

    def test_update_question_not_found(self):
        """Test updating non-existent question."""
        self.mock_repository.find_by_subject_week.return_value = []

        with self.assertRaises(QuestionNotFoundError):
            self.service.update_question(
                self.test_question["subject"],
                self.test_question["week"],
                0,
                "Q",
                "A",
                self.test_question["email"]
            )

    def test_update_question_unauthorized(self):
        """Test unauthorized question update."""
        self.mock_repository.find_by_subject_week.return_value = [self.test_question]

        with self.assertRaises(UnauthorizedAccessError):
            self.service.update_question(
                self.test_question["subject"],
                self.test_question["week"],
                0,
                "Q",
                "A",
                "other@example.com"
            )

    def test_delete_question_success(self):
        """Test successful question deletion."""
        self.mock_repository.find_by_subject_week.return_value = [self.test_question]
        self.mock_repository.delete.return_value = True

        result = self.service.delete_question(
            self.test_question["subject"],
            self.test_question["week"],
            0,
            self.test_question["email"]
        )

        self.assertTrue(result)
        self.mock_repository.delete.assert_called_once()

    def test_delete_question_not_found(self):
        """Test deleting non-existent question."""
        self.mock_repository.find_by_subject_week.return_value = []

        with self.assertRaises(QuestionNotFoundError):
            self.service.delete_question(
                self.test_question["subject"],
                self.test_question["week"],
                0,
                self.test_question["email"]
            )

    def test_get_questions_by_subject_week_success(self):
        """Test successful question retrieval by subject and week."""
        self.mock_repository.find_by_subject_week.return_value = [self.test_question]

        result = self.service.get_questions_by_subject_week(
            self.test_question["subject"],
            self.test_question["week"],
            self.test_question["email"]
        )

        self.assertEqual(result, [self.test_question])
        self.mock_repository.find_by_subject_week.assert_called_once()

    def test_get_all_questions_success(self):
        """Test successful retrieval of all questions."""
        self.mock_repository.find_by_user.return_value = [self.test_question]

        result = self.service.get_all_questions(self.test_question["email"])

        self.assertEqual(result, [self.test_question])
        self.mock_repository.find_by_user.assert_called_once()

if __name__ == '__main__':
    unittest.main() 
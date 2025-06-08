"""
Unit tests for the analytics service.
"""
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from core.services.analytics_service import AnalyticsService

class TestAnalyticsService(unittest.TestCase):
    def setUp(self):
        self.question_repository = Mock()
        self.user_repository = Mock()
        self.service = AnalyticsService(self.question_repository, self.user_repository)

    def test_calculate_weighted_score_empty_scores(self):
        """Test weighted score calculation with empty scores."""
        result = self.service.calculate_weighted_score([])
        self.assertIsNone(result)

    def test_calculate_weighted_score_single_score(self):
        """Test weighted score calculation with a single score."""
        current_time = datetime.now(timezone.utc).timestamp()
        scores = [{"score": 4.0, "timestamp": current_time}]
        
        result = self.service.calculate_weighted_score(scores)
        self.assertEqual(result, 4.0)

    def test_calculate_weighted_score_multiple_scores(self):
        """Test weighted score calculation with multiple scores."""
        current_time = datetime.now(timezone.utc).timestamp()
        one_day_ago = current_time - (24 * 60 * 60)
        two_days_ago = current_time - (2 * 24 * 60 * 60)
        
        scores = [
            {"score": 4.0, "timestamp": current_time},
            {"score": 3.0, "timestamp": one_day_ago},
            {"score": 2.0, "timestamp": two_days_ago}
        ]
        
        result = self.service.calculate_weighted_score(scores)
        self.assertIsNotNone(result)
        self.assertGreater(result, 2.0)  # Should be weighted towards recent scores
        self.assertLess(result, 4.0)  # Should be less than the most recent score

    def test_calculate_weighted_score_with_last_practiced(self):
        """Test weighted score calculation with last practiced date."""
        current_time = datetime.now(timezone.utc).timestamp()
        one_day_ago = current_time - (24 * 60 * 60)
        
        scores = [
            {"score": 4.0, "timestamp": current_time},
            {"score": 3.0, "timestamp": one_day_ago}
        ]
        
        # Test with last practiced one day ago
        result = self.service.calculate_weighted_score(scores, last_practiced=one_day_ago)
        self.assertIsNotNone(result)
        self.assertLess(result, 4.0)  # Should be decayed due to last practiced date

    def test_get_user_statistics_empty(self):
        """Test user statistics with no questions."""
        self.question_repository.find_by_user.return_value = []
        
        result = self.service.get_user_statistics("test@example.com")
        
        self.assertEqual(result["total_content"], 0)
        self.assertEqual(result["total_practice_sessions"], 0)
        self.assertEqual(result["average_practice_score"], 0)
        self.assertIsNone(result["last_active"])
        self.assertEqual(result["streak_days"], 0)

    def test_get_user_statistics_with_data(self):
        """Test user statistics with sample questions."""
        current_time = datetime.now(timezone.utc).timestamp()
        questions = [
            {
                "question": "Test question 1",
                "scores": [
                    {"score": 4.0, "timestamp": current_time},
                    {"score": 3.0, "timestamp": current_time - 86400}
                ]
            },
            {
                "question": "Test question 2",
                "scores": [
                    {"score": 5.0, "timestamp": current_time}
                ]
            }
        ]
        
        self.question_repository.find_by_user.return_value = questions
        
        result = self.service.get_user_statistics("test@example.com")
        
        self.assertEqual(result["total_content"], 2)
        self.assertEqual(result["total_practice_sessions"], 3)
        self.assertAlmostEqual(result["average_practice_score"], 4.0)
        self.assertIsNotNone(result["last_active"])
        self.assertEqual(result["streak_days"], 1)

    def test_get_subject_statistics(self):
        """Test subject statistics calculation."""
        current_time = datetime.now(timezone.utc).timestamp()
        questions = [
            {
                "question": "Test question 1",
                "week": 1,
                "scores": [
                    {"score": 4.0, "timestamp": current_time},
                    {"score": 3.0, "timestamp": current_time - 86400}
                ]
            },
            {
                "question": "Test question 2",
                "week": 2,
                "scores": [
                    {"score": 2.0, "timestamp": current_time}
                ]
            }
        ]
        
        self.question_repository.find_by_subject_week.return_value = questions
        
        result = self.service.get_subject_statistics("Test Subject", "test@example.com")
        
        self.assertEqual(result["total_questions"], 2)
        self.assertEqual(result["total_attempts"], 3)
        self.assertAlmostEqual(result["average_score"], 3.0)
        self.assertIn("1", result["weekly_scores"])
        self.assertIn("2", result["weekly_scores"])
        self.assertEqual(len(result["weak_areas"]), 1)  # One question with score < 3.5

    def test_calculate_streak(self):
        """Test streak calculation."""
        today = datetime.now(timezone.utc).date()
        practice_dates = [
            datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
            datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
            datetime.combine(today - timedelta(days=2), datetime.min.time(), tzinfo=timezone.utc)
        ]
        
        streak = self.service._calculate_streak(practice_dates)
        self.assertEqual(streak, 3)

    def test_calculate_streak_with_gap(self):
        """Test streak calculation with a gap in practice."""
        today = datetime.now(timezone.utc).date()
        practice_dates = [
            datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc),
            datetime.combine(today - timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc),
            datetime.combine(today - timedelta(days=3), datetime.min.time(), tzinfo=timezone.utc)  # Gap of one day
        ]
        
        streak = self.service._calculate_streak(practice_dates)
        self.assertEqual(streak, 2)  # Should only count consecutive days

if __name__ == '__main__':
    unittest.main() 
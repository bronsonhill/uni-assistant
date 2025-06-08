"""
Analytics service for Study Legend.

This service handles all analytics-related operations including score calculations,
statistics generation, and performance tracking.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import math
import time
from collections import defaultdict
from core.exceptions.business_exceptions import (
    ValidationError,
    DatabaseError
)

class AnalyticsService:
    def __init__(self, question_repository, user_repository):
        self.question_repository = question_repository
        self.user_repository = user_repository

    def calculate_weighted_score(self, scores: List[float], last_practiced: datetime = None,
                               decay_factor: float = 0.1, forgetting_decay_factor: float = 0.05) -> float:
        """Calculate weighted score based on history and time decay"""
        if not scores:
            return 0.0
            
        # Calculate time decay
        time_decay = 1.0
        if last_practiced:
            days_since = (datetime.now() - last_practiced).days
            time_decay = math.exp(-decay_factor * days_since)
            
        # Calculate forgetting curve decay
        forgetting_decay = 1.0
        if len(scores) > 1:
            forgetting_decay = math.exp(-forgetting_decay_factor * (len(scores) - 1))
            
        # Calculate weighted average
        weights = [math.exp(-forgetting_decay_factor * i) for i in range(len(scores))]
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)
        
        return (weighted_sum / total_weight) * time_decay * forgetting_decay

    def get_user_statistics(self, email: str) -> Dict:
        """Get user statistics"""
        try:
            questions = self.question_repository.find_by_user(email)
            
            # Calculate overall statistics
            total_questions = len(questions)
            total_score = sum(self.calculate_weighted_score(q.get("scores", []), q.get("last_practiced"))
                            for q in questions)
            average_score = total_score / total_questions if total_questions > 0 else 0
            
            # Calculate subject statistics
            subject_stats = {}
            for question in questions:
                subject = question["subject"]
                if subject not in subject_stats:
                    subject_stats[subject] = {
                        "total": 0,
                        "average_score": 0,
                        "questions": []
                    }
                subject_stats[subject]["total"] += 1
                subject_stats[subject]["questions"].append(question)
                
            # Calculate averages for each subject
            for subject in subject_stats:
                questions = subject_stats[subject]["questions"]
                scores = [self.calculate_weighted_score(q.get("scores", []), q.get("last_practiced"))
                         for q in questions]
                subject_stats[subject]["average_score"] = sum(scores) / len(scores) if scores else 0
                del subject_stats[subject]["questions"]  # Remove raw questions from stats
                
            return {
                "total_questions": total_questions,
                "average_score": average_score,
                "subject_stats": subject_stats
            }
            
        except Exception as e:
            raise DatabaseError(f"Failed to get user statistics: {str(e)}", "READ")

    def get_recent_activity(self, email: str) -> List[Dict]:
        """
        Get recent activity for a user.
        
        Args:
            email: User's email
            
        Returns:
            List of recent activity items
        """
        try:
            # Get recent questions and their scores
            questions = self.question_repository.find_by_user(email)
            
            # Sort by last practiced date
            questions.sort(key=lambda x: x.get("last_practiced", datetime.min), reverse=True)
            
            # Format activity items
            activity = []
            for question in questions[:10]:  # Get last 10 activities
                if question.get("last_practiced"):
                    activity.append({
                        "type": "Practice",
                        "timestamp": question["last_practiced"].strftime("%Y-%m-%d %H:%M"),
                        "description": f"Practiced {question['subject']} Week {question['week']}"
                    })
            
            return activity

        except Exception as e:
            print(f"Error getting recent activity: {str(e)}")
            return []

    def get_subject_statistics(self, subject: str, email: str) -> Dict:
        """Get statistics for a specific subject"""
        try:
            questions = self.question_repository.find_by_subject_week(subject, None)
            questions = [q for q in questions if q.get("email") == email]
            
            if not questions:
                return {
                    "total_questions": 0,
                    "average_score": 0,
                    "weekly_scores": {},
                    "weak_areas": []
                }
                
            # Calculate overall statistics
            total_questions = len(questions)
            scores = [self.calculate_weighted_score(q.get("scores", []), q.get("last_practiced"))
                     for q in questions]
            average_score = sum(scores) / len(scores) if scores else 0
            
            # Calculate weekly scores
            weekly_scores = {}
            for question in questions:
                week = question["week"]
                if week not in weekly_scores:
                    weekly_scores[week] = []
                weekly_scores[week].append(
                    self.calculate_weighted_score(question.get("scores", []), question.get("last_practiced"))
                )
                
            # Calculate averages for each week
            for week in weekly_scores:
                weekly_scores[week] = sum(weekly_scores[week]) / len(weekly_scores[week])
                
            # Identify weak areas (weeks with scores below average)
            weak_areas = [
                week for week, score in weekly_scores.items()
                if score < average_score * 0.8  # 20% below average
            ]
            
            return {
                "total_questions": total_questions,
                "average_score": average_score,
                "weekly_scores": weekly_scores,
                "weak_areas": weak_areas
            }
            
        except Exception as e:
            raise DatabaseError(f"Failed to get subject statistics: {str(e)}", "READ")

    def _calculate_streak(self, practice_dates: List[datetime]) -> int:
        """
        Calculate the user's current practice streak.
        
        Args:
            practice_dates: List of practice dates
            
        Returns:
            Number of consecutive days with practice
        """
        if not practice_dates:
            return 0
            
        streak = 0
        today = datetime.now(timezone.utc).date()
        
        # Sort practice history by date
        sorted_dates = sorted(practice_dates, reverse=True)
        
        for date in sorted_dates:
            if date.date() == today - datetime.timedelta(days=streak):
                streak += 1
            else:
                break
                
        return streak

    def update_question_score(self, subject: str, week: str, idx: int, score: int, user_answer: str = None, email: str = None) -> Dict:
        """
        Update the score for a specific question.
        
        Args:
            subject: Subject name
            week: Week number
            idx: Question index
            score: Score value (1-5)
            user_answer: User's answer (optional)
            email: User's email
            
        Returns:
            Updated data dictionary
            
        Raises:
            ValidationError: If inputs are invalid
            DatabaseError: If database operation fails
        """
        try:
            # Validate inputs
            if not isinstance(score, int) or score < 1 or score > 5:
                raise ValidationError(f"Invalid score value: {score}. Score must be between 1 and 5.")
                
            if not subject or not week or not isinstance(idx, int) or idx < 0:
                raise ValidationError("Invalid subject, week, or question index")
                
            # Create the score entry
            timestamp = int(time.time())
            score_entry = {
                "score": score,
                "timestamp": timestamp
            }
            if user_answer:
                score_entry["user_answer"] = user_answer
                
            # Update the question score in the repository
            data = self.question_repository.update_score(
                subject=subject,
                week=week,
                idx=idx,
                score_entry=score_entry,
                email=email
            )
            
            return data
            
        except Exception as e:
            raise DatabaseError(f"Failed to update question score: {str(e)}", "UPDATE") 
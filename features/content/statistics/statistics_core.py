"""
Core functionality for statistics module.

This module handles data processing and statistics calculations.
"""
from typing import Dict, Any, List, Tuple
import datetime
from datetime import timezone
from collections import defaultdict
import numpy as np
from mongodb import queue_cards, assessments

def get_user_statistics(email: str) -> Dict[str, Any]:
    """Get overall user statistics."""
    # Load data from MongoDB
    data = queue_cards.load_data(email)
    
    # Calculate total content
    total_content = sum(
        len(week_questions)
        for subject in data.values()
        for week_questions in subject.values()
        if isinstance(week_questions, list)
    )
    
    # Calculate practice statistics
    total_attempts = 0
    total_score = 0
    practice_dates = []
    
    for subject in data.values():
        for week, questions in subject.items():
            if isinstance(questions, list):
                for question in questions:
                    if "scores" in question:
                        # Each score is a dictionary with 'score' and 'timestamp' fields
                        scores = [score["score"] for score in question["scores"]]
                        total_attempts += len(scores)
                        total_score += sum(scores)
                        
                        # Get practice dates from score timestamps, properly handling timezone
                        practice_dates.extend([
                            datetime.datetime.fromtimestamp(score["timestamp"], tz=timezone.utc)
                            for score in question["scores"]
                        ])
    
    # Calculate average score (out of 5)
    average_score = (total_score / total_attempts) if total_attempts > 0 else 0
    
    # Calculate streak
    streak = calculate_streak(practice_dates)
    
    # Get last active date
    last_active = max(practice_dates) if practice_dates else None
    
    return {
        "total_content": total_content,
        "total_practice_sessions": total_attempts,
        "average_practice_score": average_score,
        "last_active": last_active,
        "streak_days": streak
    }

def get_content_statistics(email: str) -> Dict[str, Any]:
    """Get statistics about user's content."""
    data = queue_cards.load_data(email)
    
    total_questions = 0
    questions_by_subject = defaultdict(int)
    questions_by_week = defaultdict(int)
    recent_additions = []
    
    for subject, weeks in data.items():
        for week, questions in weeks.items():
            if isinstance(questions, list):
                total_questions += len(questions)
                questions_by_subject[subject] += len(questions)
                questions_by_week[f"Week {week}"] += len(questions)
                
                # Get recent additions (last 5 questions)
                for question in questions:
                    if "added_at" in question:
                        recent_additions.append({
                            "subject": subject,
                            "week": week,
                            "question": question["question"][:50] + "...",
                            "added_at": datetime.datetime.fromtimestamp(question["added_at"], tz=timezone.utc)
                        })
    
    # Sort recent additions by date
    recent_additions.sort(key=lambda x: x["added_at"], reverse=True)
    
    return {
        "total_questions": total_questions,
        "questions_by_subject": dict(questions_by_subject),
        "questions_by_week": dict(questions_by_week),
        "recent_additions": recent_additions[:5],  # Only return last 5
        "content_distribution": dict(questions_by_subject)
    }

def get_practice_statistics(email: str) -> Dict[str, Any]:
    """Get statistics about user's practice sessions."""
    data = queue_cards.load_data(email)
    
    total_attempts = 0
    correct_answers = 0
    practice_history = []
    subject_performance = defaultdict(lambda: {"attempts": 0, "correct": 0})
    
    # Collect practice data
    for subject, weeks in data.items():
        for week, questions in weeks.items():
            if isinstance(questions, list):
                for question in questions:
                    if "scores" in question:
                        # Each score is a dictionary with 'score' and 'timestamp' fields
                        scores = [score["score"] for score in question["scores"]]
                        total_attempts += len(scores)
                        correct_answers += sum(1 for score in scores if score >= 3.5)  # 70% of 5
                        
                        # Record practice history with proper timezone handling
                        for score_data in question["scores"]:
                            practice_history.append({
                                "date": datetime.datetime.fromtimestamp(score_data["timestamp"], tz=timezone.utc),
                                "score": score_data["score"],  # Keep score out of 5
                                "subject": subject
                            })
                        
                        # Update subject performance
                        subject_performance[subject]["attempts"] += len(scores)
                        subject_performance[subject]["correct"] += sum(1 for score in scores if score >= 3.5)  # 70% of 5
    
    # Calculate average score (out of 5)
    average_score = (correct_answers / total_attempts) if total_attempts > 0 else 0
    
    # Sort practice history by date
    practice_history.sort(key=lambda x: x["date"])
    
    # Calculate weak and strong areas
    weak_areas = []
    strong_areas = []
    
    for subject, perf in subject_performance.items():
        if perf["attempts"] >= 5:  # Only consider subjects with enough attempts
            success_rate = (perf["correct"] / perf["attempts"]) * 100
            if success_rate < 60:
                weak_areas.append(f"{subject} ({success_rate:.1f}%)")
            elif success_rate > 80:
                strong_areas.append(f"{subject} ({success_rate:.1f}%)")
    
    return {
        "total_questions_attempted": total_attempts,
        "correct_answers": correct_answers,
        "average_score": average_score,
        "practice_history": practice_history,
        "weak_areas": weak_areas,
        "strong_areas": strong_areas,
        "subject_performance": dict(subject_performance)
    }

def calculate_streak(practice_history: List[datetime.datetime]) -> int:
    """Calculate the user's current practice streak."""
    if not practice_history:
        return 0
        
    streak = 0
    today = datetime.datetime.now(timezone.utc).date()
    
    # Sort practice history by date
    sorted_dates = sorted(practice_history, reverse=True)
    
    for date in sorted_dates:
        if date.date() == today - datetime.timedelta(days=streak):
            streak += 1
        else:
            break
            
    return streak

def get_last_30_days_attempts(practice_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Get practice attempts from the last 30 days."""
    thirty_days_ago = datetime.datetime.now(timezone.utc) - datetime.timedelta(days=30)
    return [
        attempt for attempt in practice_history
        if attempt["date"] >= thirty_days_ago
    ]

def get_score_distribution(practice_history: List[Dict[str, Any]]) -> List[float]:
    """Get list of scores for distribution analysis."""
    return [attempt["score"] for attempt in practice_history]

def get_subject_week_scores(email: str) -> Dict[str, Dict[str, float]]:
    """Get average scores for each subject-week combination."""
    data = queue_cards.load_data(email)
    subject_week_scores = defaultdict(lambda: defaultdict(list))
    
    for subject, weeks in data.items():
        for week, questions in weeks.items():
            if isinstance(questions, list):
                for question in questions:
                    if "scores" in question:
                        scores = [score["score"] for score in question["scores"]]
                        subject_week_scores[subject][week].extend(scores)
    
    # Calculate averages for each subject-week combination
    averages = {}
    for subject, weeks in subject_week_scores.items():
        averages[subject] = {}
        for week, scores in weeks.items():
            if scores:
                averages[subject][week] = sum(scores) / len(scores)
            else:
                averages[subject][week] = 0
    
    return dict(averages) 
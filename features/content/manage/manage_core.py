"""
Core functionality for manage module.

This module provides core functions for the Manage Questions feature.
"""
import streamlit as st
import hashlib
import numpy as np
import pandas as pd
import datetime
from typing import Dict, List, Any, Optional

# Import from Home
from Home import save_data, delete_question, update_question, calculate_weighted_score

def init_editing_state():
    """Initialize editing state variables"""
    if "editing" not in st.session_state:
        st.session_state.editing = False
    if "edit_subject" not in st.session_state:
        st.session_state.edit_subject = ""
    if "edit_week" not in st.session_state:
        st.session_state.edit_week = ""
    if "edit_idx" not in st.session_state:
        st.session_state.edit_idx = -1

def get_score_emoji(score):
    """Get an appropriate emoji for a score value"""
    if score is None:
        return "⚪"
    elif score >= 4:
        return "🟢"  # Green for good scores
    elif score >= 2.5:
        return "🟠"  # Orange for medium scores
    else:
        return "🔴"  # Red for low scores

def get_questions_for_subject_week(data: Dict, subject: str, week: str) -> List[Dict]:
    """Get questions for a specific subject and week"""
    if subject in data and week in data[subject]:
        return data[subject][week]
    return []

def get_metrics_for_questions(questions: List[Dict], decay_factor: Optional[float] = None, forgetting_decay_factor: Optional[float] = None) -> Dict:
    """Calculate metrics for a set of questions using provided factors."""
    # Collect all weighted scores for questions
    all_scores = []
    for q in questions:
        scores = q.get("scores", [])
        last_practiced = q.get("last_practiced")
        
        # Pass factors to the calculation. Use None if not provided (function defaults will apply)
        weighted_score = calculate_weighted_score(
            scores, 
            last_practiced=last_practiced,
            decay_factor=decay_factor if decay_factor is not None else 0.1, # Provide default if None
            forgetting_decay_factor=forgetting_decay_factor if forgetting_decay_factor is not None else 0.05 # Provide default if None
        )
        if weighted_score is not None:
            all_scores.append(weighted_score)
    
    # Calculate metrics
    metrics = {
        "question_count": len(questions),
        "score_count": len(all_scores),
        "avg_score": np.mean(all_scores) if all_scores else None,
        "good_count": sum(1 for s in all_scores if s >= 4),
        "medium_count": sum(1 for s in all_scores if 2.5 <= s < 4),
        "low_count": sum(1 for s in all_scores if s < 2.5),
    }
    
    # Calculate mastery percentage
    if metrics["score_count"] > 0:
        metrics["mastery_percent"] = (metrics["good_count"] / metrics["score_count"]) * 100
    else:
        metrics["mastery_percent"] = 0
    
    return metrics

def get_subject_choices(data: Dict) -> List[str]:
    """Get list of unique subjects in the data"""
    return list(data.keys())

def get_week_choices(data: Dict, subject: str) -> List[str]:
    """Get list of week choices for a given subject"""
    if subject in data:
        week_options = list(data[subject].keys())
        # Filter out metadata entries that aren't weeks
        week_options = [w for w in week_options if w != "vector_store_metadata" and w.isdigit()]
        return sorted(week_options, key=int)
    return []

def handle_delete_question(data: Dict, subject: str, week: str, idx: int, user_email: str) -> Dict:
    """Handle deleting a question"""
    # Delete the question
    updated_data = delete_question(data, subject, int(week), idx, email=user_email)
    
    # Save the updated data
    save_data(updated_data, email=user_email)
    
    return updated_data 
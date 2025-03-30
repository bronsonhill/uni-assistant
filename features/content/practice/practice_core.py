"""
Core functionality for practice module.

This module provides the core logic for practice functionality,
including queue generation, scoring, and state management.
"""
import streamlit as st
import sys
import os
import random
import time
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple, Callable
from functools import wraps

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import functions from Home.py
import Home
from ai_feedback import evaluate_answer, chat_about_question
from mongodb.queue_cards import save_ai_feedback, update_single_question_score
from features.content.base_content import check_auth_for_action, show_preview_mode, get_user_email

# Use functions from Home module
load_data = Home.load_data
save_data = Home.save_data
update_question_score = Home.update_question_score
calculate_weighted_score = Home.calculate_weighted_score

# Constants
KNOWLEDGE_LEVEL_OPTIONS = {
    0: "0 - 🆕 New questions only",
    1: "1 - 🟥 New + struggling questions",
    2: "2 - 🟧 Questions needing improvement",
    3: "3 - 🟨 Questions with moderate knowledge",
    4: "4 - 🟩 Questions with good knowledge",
    5: "5 - ⬜ All questions"
}

SCORE_EMOJI_MAP = {
    1: "🔴",
    2: "🟠",
    3: "🟠",
    4: "🟢",
    5: "🟢"
}

def get_score_emoji(score: int) -> str:
    """Return the appropriate emoji for a given score"""
    if score >= 4:
        return "🟢"
    elif score >= 2:
        return "🟠"
    else:
        return "🔴"

# Cache the loading of data with TTL of 10 minutes to balance freshness with performance
@st.cache_data(ttl=600)
def cached_load_data(user_email):
    """Cached version of load_data to reduce repeated disk/database access"""
    return load_data(user_email)

# Cache the vector store ID lookups
@st.cache_data(ttl=1800)  # 30 minutes TTL
def get_cached_vector_store_id(subject: str, week: str, data):
    """Get vector store ID for the current subject and week if it exists"""
    if (subject in data and 
        "vector_store_metadata" in data[subject] and 
        week in data[subject]["vector_store_metadata"]):
        return data[subject]["vector_store_metadata"][week].get("id")
    return None

def is_metadata_key(key: str) -> bool:
    """Check if a key is a metadata key (not a week)"""
    return key == "vector_store_metadata" or not key.isdigit()

def filter_weeks(data: Dict, subject: str) -> List[str]:
    """Get a list of week keys for a subject, filtering out metadata"""
    return [w for w in data[subject].keys() if not is_metadata_key(w)]

def collect_all_weeks(data: Dict) -> List[str]:
    """Collect all week numbers across all subjects"""
    all_weeks = set()
    for subject in data.keys():
        weeks = filter_weeks(data, subject)
        all_weeks.update(weeks)
    return sorted(list(all_weeks), key=int) if all_weeks else []

def build_question_item(subject: str, week: str, q_idx: int, q_data: Dict) -> Dict:
    """Create a standardized question item for the queue"""
    weighted_score = None
    if "scores" in q_data and q_data["scores"]:
        weighted_score = calculate_weighted_score(q_data["scores"])
    
    return {
        "subject": subject,
        "week": week,
        "question_idx": q_idx,
        "question": q_data["question"],
        "answer": q_data["answer"],
        "weighted_score": weighted_score,
        "last_practiced": q_data.get("last_practiced", None)
    }

def should_include_question(q_data: Dict, min_score: int) -> bool:
    """Determine if a question should be included based on score threshold"""
    if "scores" not in q_data or not q_data["scores"]:
        return True  # Include questions with no scores
    
    weighted_score = calculate_weighted_score(q_data["scores"])
    return weighted_score <= min_score

def filter_questions_by_subject_week(data: Dict, subject: str, week: str, min_score: int) -> List[Dict]:
    """Filter questions for a specific subject and week"""
    questions = []
    for i, q in enumerate(data[subject][week]):
        if should_include_question(q, min_score):
            questions.append(build_question_item(subject, week, i, q))
    return questions

# Cache the filtered question queue to avoid rebuilding it frequently
@st.cache_data(ttl=300)  # 5 minutes TTL
def build_cached_queue(data, selected_subject, selected_week, practice_order, min_score):
    """Build a cached queue of questions based on selected filters and score threshold"""
    questions_queue = []
    all_subjects = list(data.keys())
    all_weeks = collect_all_weeks(data)
    
    # Check if we have specific weeks selected
    try:
        selected_weeks_list = st.session_state.get("selected_practice_weeks", [])
        # Ensure it's a valid list
        if not isinstance(selected_weeks_list, list):
            selected_weeks_list = []
    except Exception:
        # If there's any error, just use an empty list
        selected_weeks_list = []
    
    # Build queue based on filters
    if selected_subject == "All" and selected_week == "All":
        # All subjects, all weeks (or selected weeks if specified)
        for subject in all_subjects:
            for week in filter_weeks(data, subject):
                # If we have specific weeks selected, only include those
                if selected_weeks_list and week not in selected_weeks_list:
                    continue
                questions_queue.extend(filter_questions_by_subject_week(data, subject, week, min_score))
    elif selected_subject == "All":
        # All subjects, specific week
        for subject in all_subjects:
            if selected_week in data[subject]:
                questions_queue.extend(filter_questions_by_subject_week(data, subject, selected_week, min_score))
    elif selected_week == "All":
        # Specific subject, all weeks (or selected weeks if specified)
        for week in filter_weeks(data, selected_subject):
            # If we have specific weeks selected, only include those
            if selected_weeks_list and week not in selected_weeks_list:
                continue
            questions_queue.extend(filter_questions_by_subject_week(data, selected_subject, week, min_score))
    else:
        # Specific subject, specific week
        questions_queue.extend(filter_questions_by_subject_week(data, selected_subject, selected_week, min_score))
    
    # Apply order modes
    if practice_order == "Random":
        # Use a deterministic random seed based on the current date
        random_seed = hash(datetime.now().strftime("%Y-%m-%d"))
        random.Random(random_seed).shuffle(questions_queue)
    elif practice_order == "Needs Practice":
        # Sort by weighted score (lowest first) and then by last practiced time (oldest first)
        questions_queue.sort(key=lambda x: (
            5 if x["weighted_score"] is None else x["weighted_score"],  # None scores get highest value
            0 if x["last_practiced"] is None else -x["last_practiced"]   # None last_practiced get highest priority
        ))
    
    return questions_queue, all_subjects, all_weeks

# Cache AI feedback responses to avoid repeated API calls
@st.cache_data(ttl=1800)  # 30 minutes TTL
def cached_evaluate_answer(question, user_answer, expected_answer):
    """Cache the AI evaluation of user answers"""
    # Use a placeholder for the stream handler since it can't be cached
    return evaluate_answer(question, user_answer, expected_answer, stream_handler=None)

def save_score_with_answer(data: Dict, question_item: Dict, score: int, user_answer: str, user_email: str) -> Dict:
    """Save user's score and answer with improved error handling and data validation"""
    print(f"\n=== save_score_with_answer called ===")
    print(f"Question item: {question_item}")
    print(f"Score: {score}")
    print(f"User email: {user_email}")
    
    try:
        # Validate inputs
        if not isinstance(score, int) or score < 1 or score > 5:
            raise ValueError(f"Invalid score value: {score}. Score must be between 1 and 5.")
            
        if not question_item.get("subject") or not question_item.get("week") or "question_idx" not in question_item:
            raise ValueError("Invalid question item: missing required fields")
            
        # Ensure the data structure exists
        subject = question_item["subject"]
        week = str(question_item["week"])  # Ensure week is string
        question_idx = question_item["question_idx"]
        
        print(f"Processing score for subject: {subject}, week: {week}, question_idx: {question_idx}")
        
        if subject not in data:
            print(f"Creating new subject: {subject}")
            data[subject] = {}
        if week not in data[subject]:
            print(f"Creating new week: {week}")
            data[subject][week] = []
            
        # Ensure the question exists
        if question_idx >= len(data[subject][week]):
            raise ValueError(f"Question index {question_idx} out of range for subject {subject}, week {week}")
            
        # Initialize scores list if it doesn't exist
        if "scores" not in data[subject][week][question_idx]:
            print("Initializing scores list")
            data[subject][week][question_idx]["scores"] = []
            
        # Create the score entry with timestamp
        score_entry = {
            "score": score,
            "timestamp": int(time.time()),
            "user_answer": user_answer
        }
        
        print(f"Adding score entry: {score_entry}")
        
        # Add the score entry
        data[subject][week][question_idx]["scores"].append(score_entry)
        
        # Update last_practiced timestamp
        data[subject][week][question_idx]["last_practiced"] = int(time.time())
        
        print("Calling update_question_score...")
        # Update the data in MongoDB
        data = update_question_score(
            data,
            subject,
            week,
            question_idx,
            score,
            user_answer,
            user_email
        )
        print("update_question_score completed")
        
        return data
        
    except Exception as e:
        print(f"Error in save_score_with_answer: {str(e)}")
        import traceback
        print(f"Full error traceback:\n{traceback.format_exc()}")
        raise  # Re-raise the exception to be handled by the caller

def save_ai_feedback_to_data(data: Dict, question_item: Dict, feedback_data: Dict) -> Dict:
    """Save AI feedback to the most recent score entry"""
    subject = question_item["subject"]
    week = question_item["week"]
    idx = question_item["question_idx"]
    
    if (subject in data and 
        week in data[subject] and 
        idx < len(data[subject][week]) and
        "scores" in data[subject][week][idx] and
        data[subject][week][idx]["scores"]):
        
        # Get the most recent score entry
        latest_score = data[subject][week][idx]["scores"][-1]
        
        # Add feedback data
        latest_score["ai_feedback"] = {
            "feedback": feedback_data.get("feedback", ""),
            "hint": feedback_data.get("hint", "")
        }
    
    return data

def init_session_state():
    """Initialize practice-specific session state variables"""
    if "practice_active" not in st.session_state:
        st.session_state.practice_active = False
    if "current_question_idx" not in st.session_state:
        st.session_state.current_question_idx = 0
    if "questions_queue" not in st.session_state:
        st.session_state.questions_queue = []
    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False
    if "practice_subject" not in st.session_state:
        # Get the first available subject if any exist
        data_subjects = sorted(list(st.session_state.data.keys()))
        st.session_state.practice_subject = data_subjects[0] if data_subjects else ""
    if "practice_week" not in st.session_state:
        st.session_state.practice_week = ""
    if "selected_practice_weeks" not in st.session_state:
        st.session_state.selected_practice_weeks = []
    if "practice_order" not in st.session_state:
        st.session_state.practice_order = "Sequential"
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "enable_ai_feedback" not in st.session_state:
        st.session_state.enable_ai_feedback = True
    if "min_score_threshold" not in st.session_state:
        st.session_state.min_score_threshold = 0  # Default to show all questions
    if "self_rate_score" not in st.session_state:
        st.session_state.self_rate_score = 0  # For self-rated scores
    if "rating_submitted" not in st.session_state:
        st.session_state.rating_submitted = False  # Track if a rating has been submitted for the current question
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []  # Store chat messages
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""  # Store the user's answer for the current question
    if "answer_submitted" not in st.session_state:
        st.session_state.answer_submitted = False  # Track if an answer has been submitted
    if "question_ratings" not in st.session_state:
        st.session_state.question_ratings = {}  # Track ratings for questions

def reset_question_state():
    """Reset state for the current question"""
    st.session_state.show_answer = False
    st.session_state.feedback = None
    st.session_state.rating_submitted = False
    st.session_state.self_rate_score = 0
    st.session_state.user_answer = ""
    st.session_state.answer_submitted = False
    st.session_state.chat_messages = []

def reset_practice():
    """Reset all practice session state"""
    st.session_state.practice_active = False
    st.session_state.current_question_idx = 0
    st.session_state.questions_queue = []
    st.session_state.show_answer = False
    st.session_state.feedback = None
    st.session_state.user_answer = ""
    st.session_state.answer_submitted = False
    st.session_state.chat_messages = []
    
    # Save the data with updated scores
    user_email = get_user_email()
    if user_email and "question_ratings" in st.session_state and st.session_state.question_ratings:
        try:
            save_data(st.session_state.data, user_email)
        except Exception as e:
            # Log but continue if save fails
            print(f"Error saving data: {str(e)}")
    
    # Clear the question ratings
    if "question_ratings" not in st.session_state:
        st.session_state.question_ratings = {}
    else:
        st.session_state.question_ratings = {}

def start_practice():
    """Start a new practice session"""
    st.session_state.practice_active = True
    st.session_state.current_question_idx = 0
    reset_question_state()

def build_queue():
    """Build queue using the cached function with current session state"""
    try:
        # Make sure we have all the required session state variables
        if not hasattr(st.session_state, 'data'):
            st.session_state.data = {}
        
        practice_subject = st.session_state.get('practice_subject', 'All')
        practice_week = st.session_state.get('practice_week', 'All')
        practice_order = st.session_state.get('practice_order', 'Sequential')
        min_score_threshold = st.session_state.get('min_score_threshold', 0)
        
        return build_cached_queue(
            st.session_state.data,
            practice_subject,
            practice_week,
            practice_order,
            min_score_threshold
        )
    except Exception as e:
        # Log the error and return empty data
        import traceback
        print(f"Error building queue: {str(e)}")
        print(traceback.format_exc())
        return [], [], []

def go_to_next_question():
    """Move to the next question in the queue"""
    # Reset answer-related state
    st.session_state.show_answer = False
    st.session_state.user_answer = ""
    st.session_state.feedback = None
    st.session_state.chat_messages = []
    
    # Move to next question
    st.session_state.current_question_idx += 1
    
    # Check if we've reached the end
    if st.session_state.current_question_idx >= len(st.session_state.questions_queue):
        # Practice session completed
        reset_practice()
        
        # Show completion message will be handled by UI layer 
import streamlit as st
import json
import os
import sys
from typing import Dict, Optional
from dotenv import load_dotenv
from paywall import check_subscription, show_premium_benefits, display_subscription_status, handle_oauth_login
import users

# Load environment variables from .env file if it exists
load_dotenv()

# Set server to use session persistence by the time the app loads
# This is a fallback for the config.toml settings
if not hasattr(st.session_state, "server_configured"):
    try:
        st._config.set_option("server.enableXsrfProtection", False)
        st._config.set_option("server.enableCORS", False)
        st._config.set_option("server.enableWebsocketCompression", False)
        st._config.set_option("server.maxSessionAge", 86400)  # 24 hours in seconds
        st._config.set_option("server.maxUploadSize", 50)  # 50 MB upload limit
        
        # Explicitly configure XSRF cookie options to fix file upload issues
        st._config.set_option("server.cookieOptions.xsrfCookie", False)
        
        # Set session expiration time (7 days = 604800 seconds)
        st._config.set_option("server.sessionOptions.sessionState.maxSessionLife", 604800)
        
        # Output confirmation of configuration
        print("Server configured with session persistence and XSRF protection disabled")
        
        st.session_state.server_configured = True
    except Exception as e:
        # If we can't set server options programmatically, we'll rely on config.toml
        print(f"Error configuring server options programmatically: {e}")
        print("Falling back to config.toml settings")

# Instead of using cookies, let's focus on the server-side session persistence
# which is provided by the configuration changes we've already made

# We'll remove the cookie manager entirely to fix the errors

# The config.toml and streamlit server configuration should be sufficient
# to maintain session state across refreshes

# Data structure: {subject: {week: [{"question": "...", "answer": "..."}]}}
DATA_FILE = "queue_cards.json"

# Flag to control whether to use MongoDB or JSON files
USE_MONGODB = True

# Core data functions
def load_data(email: str = None) -> Dict:
    """
    Load queue cards data from storage (MongoDB or JSON file)
    
    Args:
        email: Optional user email to filter data by ownership
    
    Returns:
        Dict: The queue cards data
    """
    if USE_MONGODB:
        try:
            import mongodb
            return mongodb.load_data(email)
        except Exception as e:
            st.warning(f"Error loading from MongoDB, falling back to JSON: {str(e)}")
            # Fall back to JSON on error
            pass
    
    # Load from JSON file
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def init_rag_manager(email: str = None):
    """
    Initialize RAG manager and load saved vector stores
    
    Args:
        email: Optional user email to filter vector stores by ownership
    
    Returns:
        Initialized RAGManager instance with loaded vector stores
    """
    from rag_manager import RAGManager
    
    # Create the RAG manager instance
    rag_manager = RAGManager()
    
    # Load saved vector stores from the data
    data = load_data(email)
    rag_manager.load_vector_stores_from_data(data, email)
    
    return rag_manager

def save_data(data: Dict, email: str = None) -> None:
    """
    Save queue cards data to storage (MongoDB or JSON file)
    
    Args:
        data: The queue cards data to save
        email: Optional user email to associate with the saved data
    """
    if USE_MONGODB:
        try:
            import mongodb
            mongodb.save_data(data, email)
            return
        except Exception as e:
            st.warning(f"Error saving to MongoDB, falling back to JSON: {str(e)}")
            # Fall back to JSON on error
            pass
    
    # Save to JSON file
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_question(data: Dict, subject: str, week: int, question: str, answer: Optional[str] = None, email: str = None) -> Dict:
    """
    Add a new question to the data
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
        question: Question text
        answer: Answer text (optional)
        email: User's email (optional) to associate with this question
    
    Returns:
        Updated data dictionary
    """
    if USE_MONGODB:
        try:
            import mongodb
            return mongodb.add_question(data, subject, week, question, answer, email)
        except Exception as e:
            st.warning(f"Error using MongoDB, falling back to JSON: {str(e)}")
            # Fall back to JSON implementation
            pass
    
    # Original implementation for JSON
    if subject not in data:
        data[subject] = {}
    
    week_str = str(week)
    if week_str not in data[subject]:
        data[subject][week_str] = []
    
    # Add the question with score tracking
    data[subject][week_str].append({
        "question": question,
        "answer": answer or "",
        "scores": [],  # Will store score history with timestamps
        "last_practiced": None  # Will track when it was last practiced
    })
    
    return data

def delete_question(data: Dict, subject: str, week: int, question_idx: int, email: str = None) -> Dict:
    """
    Delete a question from the data
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
        question_idx: Index of the question to delete
        email: User's email (optional)
    
    Returns:
        Updated data dictionary
    """
    if USE_MONGODB:
        try:
            import mongodb
            return mongodb.delete_question(data, subject, week, question_idx, email)
        except Exception as e:
            st.warning(f"Error using MongoDB, falling back to JSON: {str(e)}")
            # Fall back to JSON implementation
            pass
    
    # Original implementation for JSON
    week_str = str(week)
    if subject in data and week_str in data[subject] and question_idx < len(data[subject][week_str]):
        data[subject][week_str].pop(question_idx)
    return data

def update_question(data: Dict, subject: str, week: int, question_idx: int, new_question: str, new_answer: str, email: str = None) -> Dict:
    """
    Update an existing question
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
        question_idx: Index of the question to update
        new_question: New question text
        new_answer: New answer text
        email: User's email (optional)
    
    Returns:
        Updated data dictionary
    """
    if USE_MONGODB:
        try:
            import mongodb
            return mongodb.update_question(data, subject, week, question_idx, new_question, new_answer, email)
        except Exception as e:
            st.warning(f"Error using MongoDB, falling back to JSON: {str(e)}")
            # Fall back to JSON implementation
            pass
    
    # Original implementation for JSON
    week_str = str(week)
    if subject in data and week_str in data[subject] and question_idx < len(data[subject][week_str]):
        # Keep existing scores and tracking when updating a question
        existing_scores = data[subject][week_str][question_idx].get("scores", [])
        last_practiced = data[subject][week_str][question_idx].get("last_practiced", None)
        
        data[subject][week_str][question_idx] = {
            "question": new_question,
            "answer": new_answer,
            "scores": existing_scores,
            "last_practiced": last_practiced
        }
    return data

def update_question_score(data: Dict, subject: str, week: str, question_idx: int, score: int, user_answer: str = None, email: str = None) -> Dict:
    """
    Update the score for a specific question
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number (as string)
        question_idx: Index of the question
        score: Score value (0-10)
        user_answer: Optional user's answer to log
        email: User's email (optional)
        
    Returns:
        Updated data dictionary
    """
    if USE_MONGODB:
        try:
            import mongodb
            return mongodb.update_question_score(data, subject, week, question_idx, score, user_answer, email)
        except Exception as e:
            st.warning(f"Error using MongoDB, falling back to JSON: {str(e)}")
            # Fall back to JSON implementation
            pass
    
    # Original implementation for JSON
    import time
    
    if subject in data and week in data[subject] and question_idx < len(data[subject][week]):
        # Get the current timestamp
        current_time = int(time.time())
        
        # Initialize scores list if it doesn't exist
        if "scores" not in data[subject][week][question_idx]:
            data[subject][week][question_idx]["scores"] = []
            
        # Create score entry
        score_entry = {
            "score": score,
            "timestamp": current_time
        }
        
        # Add user answer if provided
        if user_answer is not None:
            score_entry["user_answer"] = user_answer
            
        # Add the new score with timestamp and user answer
        data[subject][week][question_idx]["scores"].append(score_entry)
        
        # Update last practiced timestamp
        data[subject][week][question_idx]["last_practiced"] = current_time
    
    return data

def get_user_email():
    """
    Get the current user's email from available sources.
    
    Returns:
        str: The user's email if available, otherwise None
    """
    # First check session_state.user_email (most reliable)
    if "user_email" in st.session_state:
        return st.session_state.user_email
    
    # Then check session_state.email (set by OAuth)
    if "email" in st.session_state:
        return st.session_state.email
    
    # No email found
    return None

def calculate_weighted_score(scores, decay_factor=0.1):
    """
    Calculate a time-weighted score for a question based on score history
    
    Args:
        scores: List of score objects with score and timestamp
        decay_factor: How much to decay older scores (higher = faster decay)
        
    Returns:
        Weighted score (float) or None if no scores available
    """
    if USE_MONGODB:
        try:
            import mongodb
            return mongodb.calculate_weighted_score(scores, decay_factor)
        except Exception:
            # Fall back to JSON implementation (silently - no need for warning here)
            pass
    
    # Original implementation
    import time
    import math
    
    if not scores:
        return None
    
    current_time = time.time()
    total_weight = 0
    total_weighted_score = 0
    
    for score_obj in scores:
        score = score_obj["score"]
        timestamp = score_obj["timestamp"]
        
        # Calculate time difference in days
        time_diff = (current_time - timestamp) / (60 * 60 * 24)  # Convert seconds to days
        
        # Exponential decay weight based on recency
        weight = math.exp(-decay_factor * time_diff)
        
        total_weighted_score += score * weight
        total_weight += weight
    
    if total_weight == 0:  # Avoid division by zero
        return None
        
    return total_weighted_score / total_weight

def migrate_to_mongodb():
    """
    Migrate data from JSON files to MongoDB.
    This function can be called to trigger a one-time migration.
    """
    try:
        import mongodb
        mongodb.migrate_json_to_mongodb()
        return True
    except Exception as e:
        st.error(f"Failed to migrate data to MongoDB: {str(e)}")
        return False

# Function to render home page content
def render_home_page():
    """
    This function contains all the code for rendering the home page content.
    It should be called after navigation is set up.
    """
    # Main title
    st.title("📚 Study Legend")
    
    # Show welcome message for new users
    if st.session_state.get("show_welcome", False):
        email = st.session_state.get("welcome_email", "")
        if email:
            st.success(f"👋 Welcome to Study Legend, {email}! Your account has been created successfully.")
            # Clear the welcome flag after showing it once
            st.session_state.show_welcome = False
    
    # Show welcome message with user email if authenticated
    if 'email' in st.session_state:
        st.markdown(f"#### Welcome, {st.session_state.email}! 👋")
    
    st.markdown("""
    Welcome to Study Legend! This app helps you study like a legend with the help of AI.
    
    The sidebar has navigation for your main activities:
    - **Add Queue Cards with AI**: Generate questions from your lecture notes or course materials.
    - **Practice**: Test yourself with your questions in sequential or random order. Get AI feedback on your answers.
    - **Subject Tutor**: Chat with an AI assistant that has access to your course materials.
    - **Assessments**: Keep track of your assessments and scores with the help of AI.
    """)
    
    # Display subscription status and benefits
    if st.session_state.get('is_subscribed'):
        st.success("🌟 **Premium Subscription Active** - Enjoy all premium features!")
        
        # Show subscription details if user is logged in
        if 'email' in st.session_state:
            email = st.session_state.email
            # Use cached info since subscription was already verified
            subscription_info = users.get_subscription_info(email, skip_stripe=True)
            
            if subscription_info and subscription_info["active"]:
                expiry_date = subscription_info.get("end_date", "Unknown")
                days_remaining = subscription_info.get("days_remaining", 0)
                
                # Format the date for display
                try:
                    from datetime import datetime
                    expiry_datetime = datetime.fromisoformat(expiry_date)
                    formatted_date = expiry_datetime.strftime("%B %d, %Y")
                except:
                    formatted_date = expiry_date
                
                st.info(f"📅 Your subscription is active until **{formatted_date}** ({days_remaining} days remaining)")
    else:
        st.info("You're using the free version of Study Legend. Consider upgrading to Premium for additional features.")
        show_premium_benefits()
    
    # Stats
    st.subheader("Your Question Stats")
    
    total_questions = 0
    subject_count = len(st.session_state.data)
    all_weeks = set()
    
    for subject in st.session_state.data:
        for week in st.session_state.data[subject]:
            if week != "vector_store_metadata":  # Skip metadata
                all_weeks.add(week)
                total_questions += len(st.session_state.data[subject][week])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", total_questions)
    with col2:
        st.metric("Subjects", subject_count)
    with col3:
        st.metric("Weeks Covered", len(all_weeks))
    
    # Add MongoDB migration option for admins
    if st.session_state.get('email') == "admin@example.com":  # Replace with your admin email
        with st.expander("Admin Options"):
            st.markdown("### Database Migration")
            if st.button("Migrate Data to MongoDB"):
                with st.spinner("Migrating data to MongoDB..."):
                    success = migrate_to_mongodb()
                    if success:
                        st.success("Migration completed successfully!")
                    else:
                        st.error("Migration failed. See error message above.")

# Main app
def main():
    # Set the page config with the same settings across the entire app
    # This is crucial for the navigation to work correctly
    try:
        # Only set page config if it hasn't been set already
        if not st.session_state.get("page_config_set", False):
            st.set_page_config(
                page_title="Study Legend AI", 
                page_icon="📚",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            st.session_state.page_config_set = True
    except Exception as e:
        # If there's an error (likely because page config is already set), just continue
        print(f"Note: Page config may have already been set: {e}")
    
    # Explicitly check for OAuth login
    # This ensures we record the login even if the user just authenticated
    handle_oauth_login()
    
    # Check subscription status first (before navigation)
    # Only force verification on first page load (Home.py)
    # This ensures we check Stripe at least once when the app is started
    force_first_check = "subscription_verified_at" not in st.session_state
    
    # This will set st.session_state.is_subscribed which is used by navigation
    is_subscribed, user_email = check_subscription(required=False, force_verify=force_first_check)
    
    # Display subscription status in sidebar
    display_subscription_status()
    
    # Always store user email in session state for consistent access
    if user_email:
        st.session_state.user_email = user_email
    
    # Use our helper function to get the most reliable email
    email_to_use = get_user_email()
    
    # Initialize session state variables if they don't exist
    if "data" not in st.session_state:
        st.session_state.data = load_data(email_to_use)
    if "editing" not in st.session_state:
        st.session_state.editing = False
    if "edit_subject" not in st.session_state:
        st.session_state.edit_subject = ""
    if "edit_week" not in st.session_state:
        st.session_state.edit_week = ""
    if "edit_idx" not in st.session_state:
        st.session_state.edit_idx = -1
    if "rag_manager" not in st.session_state:
        st.session_state.rag_manager = init_rag_manager(email_to_use)
    if "current_view" not in st.session_state:
        st.session_state.current_view = "home"
    
    # Import and set up navigation - do this after subscription check
    from common_nav import setup_navigation
    
    # Set up navigation and run the selected page
    pg = setup_navigation()
    pg.run()

if __name__ == "__main__":
    main()
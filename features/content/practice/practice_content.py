"""
Practice content module.

This module integrates the Practice functionality components and manages the UI.
"""
import streamlit as st
import sys
import os
from st_paywall import add_auth

# Add parent directory to path so we can import from parent modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import from Home and base content
import Home
from features.content.base_content import check_auth_for_action, show_preview_mode, get_user_email, init_data

# Import from refactored practice modules
from features.content.practice.practice_core import (
    init_session_state,
    reset_question_state,
    reset_practice,
    start_practice,
    build_queue,
    go_to_next_question,
    load_data
)
from features.content.practice.practice_ui import (
    display_setup_screen,
    display_practice_question,
    display_practice_navigation,
    display_knowledge_level_selector
)
from features.content.practice.practice_demo import (
    show_demo_content,
    show_premium_benefits
)

def run():
    """Main practice page content - this gets run by the navigation system"""
    # Check if user is authenticated and subscribed using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    st.title("🎯 Practice with AI")
    st.markdown("""
    Test your knowledge with the questions you've created. You can practice all questions 
    or filter by subject and week. Choose between sequential or random order.
    """)

    # Check for unauthenticated users first to show demo content
    if not user_email:
        # Show preview mode for unauthenticated users
        show_preview_mode(
            "Practice",
            """
            This feature allows you to practice with your flashcards using AI feedback.
            
            - Choose questions by subject and week
            - Test yourself in sequential or random order
            - Get instant AI feedback on your answers
            - Track your progress over time
            """
        )
        
        # Show demo/preview content
        show_demo_content()
        return

    # Load data first if not already loaded
    if "data" not in st.session_state:
        st.session_state.data = load_data(user_email)
        st.rerun()
        return

    # Initialize practice-specific session state
    if not all(key in st.session_state for key in ["practice_active", "questions_queue", "current_question_idx"]):
        init_session_state()
        st.rerun()
        return

    # Practice setup screen
    if not st.session_state.practice_active:
        if not st.session_state.data:
            st.warning("No questions available. Add some questions first!")
            st.link_button("Go to Add Cards with AI", "/render_add_ai")
        else:
            display_setup_screen(is_authenticated)
    
    # Practice in progress
    else:
        # Top control bar
        col1, col3 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"Question {st.session_state.current_question_idx + 1} of {len(st.session_state.questions_queue)}")
        
        with col3:
            st.write("")  # Spacing
            if st.button("End Practice", use_container_width=True, type="primary"):
                reset_practice()
                st.rerun()
        
        # Current question
        if st.session_state.current_question_idx < len(st.session_state.questions_queue):
            current_q = st.session_state.questions_queue[st.session_state.current_question_idx]
            display_practice_question(current_q, is_authenticated, user_email)
    
    # For authenticated but non-subscribed users - show premium benefits
    if is_authenticated and not is_subscribed:
        show_premium_benefits()

if __name__ == "__main__":
    run()

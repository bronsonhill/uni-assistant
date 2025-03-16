"""
Subject Tutor content module.

This module integrates the Subject Tutor functionality components and manages the UI.
"""
import streamlit as st
import sys
import os

# Add parent directory to path so we can import from parent modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import from st_paywall
try:
    from st_paywall import add_auth
except ImportError:
    # Fallback if there's an issue with st_paywall
    def add_auth(required=False, login_button_text="Login", login_button_color="primary", login_sidebar=False):
        if "email" not in st.session_state:
            st.session_state.email = "test@example.com"  # Fallback to test user
        return True  # Always return subscribed in fallback mode

# Import from Home and base content
import Home
from features.content.base_content import show_preview_mode

# Import from refactored tutor modules
from features.content.tutor.tutor_core import (
    init_session_state,
    reset_chat
)
from features.content.tutor.tutor_ui import (
    display_subject_selection,
    display_chat_history,
    display_chat_interface
)
# Import the new vector store manager module
from features.content.tutor.vector_store_manager import display_vector_store_files

from features.content.tutor.tutor_demo import (
    show_demo_content,
    show_premium_benefits
)

def run():
    """Main tutor page content - this gets run by the navigation system"""
    # Check if user is authenticated and subscribed
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    # Title and description
    st.title("💬 Chat with Subject Tutor")
    st.markdown("""
    Talk to your personal AI study buddy who knows your course materials!
    Ask questions, get explanations, and deepen your understanding of course topics.
    """)

    # Handle different access scenarios
    if not is_authenticated:
        # Show preview mode for unauthenticated users
        show_preview_mode(
            "Subject Tutor",
            """
            Chat with an AI tutor that understands your course materials.
            Ask questions, get explanations, and improve your understanding
            of complex topics from your lectures and readings.
            
            Your AI study buddy makes learning more interactive and effective.
            """
        )
        
        # Show demo content for unauthenticated users
        show_demo_content()
        return
    
    if not is_subscribed:
        # Show premium feature notice for authenticated but non-subscribed users
        st.warning("This is a premium feature that requires a subscription.")
        show_premium_benefits()
        
        # Show demo content for non-subscribed users
        show_demo_content()
        
        # Add prominent upgrade button
        st.button("Upgrade to Premium", type="primary", disabled=True)
        return
    
    # If we get here, user is authenticated and subscribed - proceed with full functionality
    
    # Initialize session state for chat
    init_session_state()
    
    # Load data if not already in session state
    if "data" not in st.session_state:
        st.session_state.data = Home.load_data(email=user_email)
    
    # Callback for when a chat is loaded from history
    def on_chat_load(subject, week):
        """Update UI selections when a chat is loaded"""
        if subject and week:
            # Set the subject and week selection
            st.session_state.subject_selection = subject
            st.session_state.week_selection = week
    
    # Subject and week selection layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create tabs for material selection and chat history
        tabs = st.tabs(["Course Materials", "Chat History"])
        
        # Material selection tab
        with tabs[0]:
            selected_subject, selected_week, vector_store_id = display_subject_selection()
            
            # Reset chat button
            if st.button("Reset Chat", type="secondary"):
                reset_chat()
                st.rerun()
        
        # Chat history tab
        with tabs[1]:
            display_chat_history(user_email, on_chat_load)
    
    with col2:
        # Display chat interface if materials are selected
        if "subject_selection" in st.session_state and "week_selection" in st.session_state:
            # Use values from session state (might be set by loading a chat)
            subject = st.session_state.subject_selection
            week = st.session_state.week_selection
            
            # Get vector store ID
            if (subject in st.session_state.data and 
                "vector_store_metadata" in st.session_state.data[subject] and
                week in st.session_state.data[subject]["vector_store_metadata"]):
                vector_store_id = st.session_state.data[subject]["vector_store_metadata"][week]
                
                # Display the chat interface
                display_chat_interface(vector_store_id, subject, week)
        elif selected_subject and selected_week and vector_store_id:
            # Display chat interface with selected values
            display_chat_interface(vector_store_id, selected_subject, selected_week)
        else:
            st.info("Please select a subject and week with uploaded course materials to start chatting.")

if __name__ == "__main__":
    run()
"""
AI Question Generator content module.

This module integrates the AI Question Generator functionality components and manages the UI.
"""
import streamlit as st
import sys
import os

# Add parent directory to path so we can import from parent modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import from Home
from Home import load_data, get_user_email
from features.content.base_content import show_preview_mode

# Import from refactored add_ai modules
from features.content.add_ai.add_ai_core_refactored import (
    init_session_state,
    init_rag_manager
)
from features.content.add_ai.add_ai_ui_refactored import (
    display_file_upload,
    display_question_review,
    display_kb_management,
    display_error_message
)
from features.content.add_ai.add_ai_demo import (
    show_premium_benefits,
    show_demo_content,
    show_kb_demo_content
)

def run():
    """Main AI question generation page content - this gets run by the navigation system"""
    st.title("🤖 AI-Generated Questions")
    
    # Check if user is authenticated and subscribed using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    # Handle different access scenarios
    if not is_authenticated:
        # Show preview mode for unauthenticated users
        show_preview_mode(
            "AI Question Generator",
            """
            Upload your lecture notes or course materials, and let AI generate study questions for you.
            The system builds a knowledge base for each subject and week, allowing for more relevant questions.
            
            Files you upload will also be available to the assistant chat bot, making it more knowledgeable
            and tailored to your subject content.
            """
        )
        
        # Create tabs for demo content
        demo_tab1, demo_tab2 = st.tabs(["Generate Questions", "Manage Knowledge Base"])
        
        with demo_tab1:
            # Show demo content for questions generation
            show_demo_content()
        
        with demo_tab2:
            # Show demo content for knowledge base management
            show_kb_demo_content()
            
        return
    
    if not is_subscribed:
        # Show premium feature notice for authenticated but non-subscribed users
        st.markdown("""
        Generate questions from your lecture notes or course materials with AI.
        Upload your files and let the system create tailored study questions.
        """)
        
        st.warning("This is a premium feature that requires a subscription.")
        show_premium_benefits()
        
        # Create tabs for demo content
        demo_tab1, demo_tab2 = st.tabs(["Generate Questions", "Manage Knowledge Base"])
        
        with demo_tab1:
            # Show demo content for questions generation
            show_demo_content()
        
        with demo_tab2:
            # Show demo content for knowledge base management
            show_kb_demo_content()
        
        # Add prominent upgrade button
        st.button("Upgrade to Premium", type="primary", disabled=True)
        return
    
    # If we get here, user is authenticated and subscribed - proceed with full functionality
    
    # Get the most reliable user email
    user_email = get_user_email() or user_email
    
    # Make sure we have the user's email in all the right places
    if user_email:
        st.session_state.user_email = user_email
    
    # Load data if not already in session state
    if "data" not in st.session_state:
        st.session_state.data = load_data(user_email)
    
    # Initialize session state variables
    init_session_state()
    
    # Initialize the RAG manager
    rag_manager_ok = init_rag_manager(user_email)
    
    if not rag_manager_ok:
        display_error_message("Could not initialize the RAG Manager. Make sure you have the required dependencies installed.")
        st.info("Run: `pip install sentence-transformers chromadb pdfplumber`")
        st.stop()
    
    # Create tabs for the different sections
    tab1, tab2 = st.tabs(["Generate Questions", "Manage Knowledge Base"])
    
    with tab1:
        # File upload interface
        display_file_upload(is_subscribed)
        
        # Question review and selection
        display_question_review()
    
    with tab2:
        # Knowledge base management
        display_kb_management()

if __name__ == "__main__":
    run()
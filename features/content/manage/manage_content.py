"""
Manage Questions content module.

This module integrates the Manage Questions functionality components and manages the UI.
"""
import streamlit as st
import sys
import os

# Add parent directory to path so we can import from parent modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import from base module
from features.content.base_content import init_data

# Import from refactored manage modules
from features.content.manage.manage_core import init_editing_state
from features.content.manage.manage_ui import (
    display_questions,
    handle_edit_form
)
from features.content.manage.manage_demo import (
    show_demo_content,
    show_premium_benefits
)

def run():
    """Main manage questions page content - this gets run by the navigation system"""
    # Check if user is logged in and subscribed using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None  # User is authenticated if email exists
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    # Show demo content for unauthenticated users
    if not is_authenticated:
        show_demo_content()
        return
    
    # Initialize data in session state for authenticated users
    init_data(email=user_email)
    
    # Initialize editing state if needed
    init_editing_state()
    
    st.title("📝 Manage Questions")
    st.markdown("""
    View, edit, and delete your existing questions on this page. 
    Questions are organized by subject and week number.
    
    Each question now shows its current score and includes a history of your past answers.
    """)
    
    # Edit question form
    if st.session_state.editing:
        handle_edit_form()
    
    # Display existing questions or show demo content for authenticated but unsubscribed users
    elif not st.session_state.data:
        if is_subscribed:
            st.info("No questions added yet. Use the 'Add Questions' page to create some.")
        else:
            # For authenticated but unsubscribed users with no data, show demo content
            st.info("No questions added yet. Here's a preview of what the question management looks like:")
            show_demo_content()
    else:
        display_questions(user_email, is_subscribed)
        
        # Show premium preview for authenticated but unsubscribed users with existing data
        if is_authenticated and not is_subscribed:
            show_premium_benefits()

if __name__ == "__main__":
    run()
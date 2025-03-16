"""
Add Questions Manually content module.

This module provides the content for the Add Questions Manually page.
"""
import streamlit as st
import sys
import os

# Add parent directory to path so we can import from parent modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import from Home and base_content
from Home import add_question, save_data
from features.content.base_content import init_data

def show_demo_form():
    """Show a disabled demo form for unauthenticated users"""
    with st.form("disabled_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Subject", value="Computer Science", disabled=True)
        with col2:
            st.number_input("Week", min_value=1, max_value=52, value=1, step=1, disabled=True)
        
        st.text_area("Question", 
                     value="What is the difference between a stack and a queue?",
                     height=100, disabled=True)
        
        st.text_area("Expected Answer (Optional)", 
                     value="A stack follows the Last-In-First-Out (LIFO) principle, while a queue follows the First-In-First-Out (FIFO) principle.",
                     height=150, disabled=True)
        
        st.form_submit_button("Add Question", disabled=True, use_container_width=True)
    
    # Additional guidance
    st.info("👆 Sign in using the button in the sidebar to add your own questions.")

def show_add_question_form(user_email):
    """Show the actual form for adding questions"""
    with st.form("add_question_form"):
        # Get unique subjects for dropdown
        subjects = list(st.session_state.data.keys())
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_subject = st.text_input("Subject (or select existing)")
            
            if subjects:  # Only show if there are existing subjects
                subject_options = ["New subject"] + subjects
                selected_subject_option = st.selectbox("Select existing subject", subject_options)
                
                if selected_subject_option != "New subject":
                    new_subject = selected_subject_option
        
        with col2:
            week = st.number_input("Week", min_value=1, max_value=52, step=1)
        
        question = st.text_area("Question", height=100, 
                              placeholder="Enter your question here...")
        
        answer = st.text_area("Expected Answer (Optional)", height=150,
                            placeholder="Enter the expected answer here (optional)...")
        
        submit = st.form_submit_button("Add Question", use_container_width=True)
        
        if submit:
            if not new_subject:
                st.error("Please enter a subject name.")
            elif not question:
                st.error("Please enter a question.")
            else:
                st.session_state.data = add_question(st.session_state.data, new_subject, week, question, answer, email=user_email)
                save_data(st.session_state.data, email=user_email)
                st.success(f"Added question to {new_subject}, Week {week}")
                st.balloons()

def run():
    """Main add questions manually page content - this gets run by the navigation system"""
    # Initialize data in session state
    user_email = st.session_state.get("email")
    init_data(email=user_email)
    
    # Page title
    st.title("🆕 Add New Questions")
    st.markdown("""
    Create new study questions by filling out the form below. Questions are organized by subject and week number.
    You can also provide an expected answer for self-checking during practice.
    """)
    
    # More robust check for authentication - ensure email exists and is not empty
    is_authenticated = user_email is not None and user_email != ""
    
    if not is_authenticated:
        # User is not logged in - show message and disabled form
        st.warning("⚠️ Please sign in to add questions. The form below is disabled for preview only.")
        
        # Show demo form (disabled)
        show_demo_form()
        return
    
    # If logged in, show the actual form
    show_add_question_form(user_email)

if __name__ == "__main__":
    run()
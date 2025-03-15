"""
Add Questions Manually content module.

This module provides the content for the Add Questions Manually page.
"""
import streamlit as st
from . import base_content

# Import specific functions needed from Home
from Home import add_question, save_data

def run():
    """Main add questions manually page content - this gets run by the navigation system"""
    # Initialize data in session state
    user_email = base_content.get_user_email()
    base_content.init_data(email=user_email)
    
    # Page title
    st.title("🆕 Add New Questions")
    st.markdown("""
    Create new study questions by filling out the form below. Questions are organized by subject and week number.
    You can also provide an expected answer for self-checking during practice.
    """)
    
    # Form for adding new questions
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
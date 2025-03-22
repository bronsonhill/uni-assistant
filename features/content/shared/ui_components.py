"""
Shared UI components for content features.

This module provides reusable UI elements that can be used across different content features.
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional, Callable

def render_questions_with_selection(
    questions: List[Dict[str, Any]], 
    selected_questions: Dict, 
    on_select_callback: Optional[Callable] = None
):
    """
    Render a list of questions with checkboxes for selection
    
    Args:
        questions: List of question dictionaries with 'question' and 'answer' keys
        selected_questions: Dictionary to track selected questions
        on_select_callback: Optional callback when a question is selected/deselected
    """
    if not questions:
        return
    
    # Display each question with a checkbox
    for i, q in enumerate(questions):
        # Create unique key for each checkbox and text areas
        checkbox_key = f"q_{i}"
        question_key = f"question_{i}"
        answer_key = f"answer_{i}"
        
        # Get current values, using edited values if they exist
        current_question = st.session_state.get(question_key, q.get("question", ""))
        current_answer = st.session_state.get(answer_key, q.get("answer", ""))
        
        # Check if this question is already selected
        is_selected = checkbox_key in selected_questions
        
        with st.container(border=True):
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                # Make question editable
                edited_question = st.text_area(
                    f"Q{i+1}:",
                    value=current_question,
                    key=question_key,
                    height=100
                )
                
                # Create columns for answer editing and preview
                answer_col1, answer_col2 = st.columns(2)
                
                with answer_col1:
                    # Make answer editable in expander
                    with st.expander("Edit answer"):
                        edited_answer = st.text_area(
                            "Answer:",
                            value=current_answer,
                            key=answer_key,
                            height=150
                        )
                
                with answer_col2:
                    # Show preview of answer in a separate expander
                    with st.expander("Preview answer"):
                        st.write(edited_answer if edited_answer else "No answer provided.")
            
            with col2:
                # Use the checkbox to select/deselect the question with a label
                selected = st.checkbox("Select", value=True, key=checkbox_key)
                
                # Update the selected questions dictionary with edited content
                if selected:
                    # Create a copy of the question with edited content
                    edited_q = q.copy()
                    edited_q["question"] = edited_question
                    edited_q["answer"] = edited_answer
                    
                    if checkbox_key not in selected_questions:
                        selected_questions[checkbox_key] = edited_q
                    else:
                        # Update existing selected question with edited content
                        selected_questions[checkbox_key] = edited_q
                elif checkbox_key in selected_questions:
                    del selected_questions[checkbox_key]
                
                # Call the callback if provided
                if on_select_callback and selected != is_selected:
                    on_select_callback(checkbox_key, selected, q)

def create_subject_week_selector(
    data: Dict, 
    subject_key: str = "subject_selector", 
    week_key: str = "week_selector",
    filter_with_kb_only: bool = False
):
    """
    Create a subject and week selector with proper filtering
    
    Args:
        data: The user's data dictionary
        subject_key: Key for the subject selectbox
        week_key: Key for the week selectbox
        filter_with_kb_only: Only show subjects/weeks with knowledge bases
        
    Returns:
        Tuple of (selected_subject, selected_week)
    """
    col1, col2 = st.columns(2)
    
    # Get subjects with KB if filtering is enabled
    subjects = []
    if filter_with_kb_only:
        for subject in data:
            if "vector_store_metadata" in data[subject] and data[subject]["vector_store_metadata"]:
                subjects.append(subject)
    else:
        subjects = list(data.keys())
    
    # Sort subjects alphabetically
    subjects.sort()
    
    # Subject selection
    with col1:
        if subject_key in st.session_state:
            # Keep the selected subject if it's still valid
            current_subject = st.session_state[subject_key]
            if current_subject not in subjects:
                current_subject = subjects[0] if subjects else None
        else:
            current_subject = subjects[0] if subjects else None
            
        selected_subject = st.selectbox(
            "Subject",
            options=subjects,
            index=subjects.index(current_subject) if current_subject in subjects else 0,
            key=subject_key
        )
    
    # Get weeks for the selected subject
    weeks = []
    if selected_subject in data:
        if filter_with_kb_only:
            if "vector_store_metadata" in data[selected_subject]:
                weeks = list(data[selected_subject]["vector_store_metadata"].keys())
        else:
            weeks = [w for w in data[selected_subject].keys() if w != "vector_store_metadata"]
    
    # Sort weeks numerically
    weeks.sort(key=lambda x: int(x) if str(x).isdigit() else float('inf'))
    
    # Week selection
    with col2:
        if week_key in st.session_state and selected_subject == st.session_state.get(subject_key, ""):
            # Keep the selected week if subject hasn't changed and week is still valid
            current_week = st.session_state[week_key]
            if current_week not in weeks:
                current_week = weeks[0] if weeks else None
        else:
            current_week = weeks[0] if weeks else None
            
        selected_week = st.selectbox(
            "Week",
            options=weeks,
            index=weeks.index(current_week) if current_week in weeks else 0,
            key=week_key
        )
    
    return selected_subject, selected_week

def display_file_upload_interface(
    on_generate_callback: Callable,
    subject_value: str = "",
    week_value: int = 1,
    subject_key: str = "subject_input",
    week_key: str = "week_input", 
    file_key: str = "file_upload",
    subject_options: List[str] = None,
    allow_custom_subject: bool = True
):
    """
    Display a standardized file upload interface
    
    Args:
        on_generate_callback: Callback function when generate button is clicked
        subject_value: Initial value for subject input
        week_value: Initial value for week input
        subject_key: Key for subject input
        week_key: Key for week input
        file_key: Key for file uploader
        subject_options: List of subject options for the dropdown (if None, uses a text input)
        allow_custom_subject: Whether to allow custom subject input (shows a "Create New" option)
    
    Returns:
        Tuple of (subject, week, uploaded_file)
    """
    # Define columns for input fields
    col1, col2 = st.columns(2)
    
    with col1:
        # Subject input - either dropdown or text input
        if subject_options:
            # If we have subject options, use a dropdown
            if allow_custom_subject:
                # Add "Create New" option to allow custom input
                all_options = subject_options.copy()
                if "Create New" not in all_options:
                    all_options.append(" + New")
                
                selected_subject = st.selectbox(
                    "Subject", 
                    options=all_options,
                    index=all_options.index(subject_value) if subject_value in all_options else 0,
                    key=f"{subject_key}_select"
                )
                
                # If "Create New" is selected, show a text input
                if selected_subject == " + New":
                    subject = st.text_input(
                        "New Subject Name", 
                        value="",
                        placeholder="e.g., Computer Science",
                        key=f"{subject_key}_custom"
                    )
                else:
                    subject = selected_subject
            else:
                # Just use the dropdown without custom option
                subject = st.selectbox(
                    "Subject", 
                    options=subject_options,
                    index=subject_options.index(subject_value) if subject_value in subject_options else 0,
                    key=subject_key
                )
        else:
            # If no subject options provided, fall back to text input
            subject = st.text_input(
                "Subject", 
                value=subject_value,
                placeholder="e.g., Computer Science",
                key=subject_key
            )
    
    with col2:
        # Week input
        week = st.number_input(
            "Week", 
            min_value=1, 
            max_value=52,
            value=week_value,
            key=week_key
        )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a file (PDF or TXT)",
        type=["pdf", "txt"],
        key=file_key,
        accept_multiple_files=False
    )
    
    # Show upload button if a file is selected
    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Questions from Upload", key="generate_btn", use_container_width=True):
                if not subject:
                    st.error("Please enter a subject.")
                else:
                    # Call the callback with the uploaded file info
                    on_generate_callback(subject, week, uploaded_file)
    
    return subject, week, uploaded_file 
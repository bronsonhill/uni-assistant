"""
UI components for add_ai module.

This module provides UI elements and display functions for the AI Question Generator feature.
"""
import streamlit as st
import pandas as pd
import time
from typing import Dict, List, Any, Optional

# Import core functionality
from features.content.add_ai.add_ai_core import (
    process_uploaded_file,
    generate_questions_without_upload,
    add_selected_questions_to_data,
    delete_vector_store,
    init_rag_manager
)

# Import vector store management
from features.content.add_ai.add_ai_vector_manager import (
    extract_vector_store_id,
    display_vector_store_files,
    display_enhanced_kb_management
)

def display_file_upload(is_subscribed: bool):
    """Display the file upload interface for generating questions"""
    # Define columns for input fields
    col1, col2 = st.columns(2)
    
    with col1:
        # Subject input
        subject = st.text_input(
            "Subject", 
            value=st.session_state.generation_subject,
            placeholder="e.g., Computer Science",
            key="subject_input"
        )
    
    with col2:
        # Week input
        week = st.number_input(
            "Week", 
            min_value=1, 
            max_value=52,
            value=st.session_state.generation_week,
            key="week_input"
        )
    
    # Number of questions slider
    num_questions = st.slider(
        "Number of questions to generate",
        min_value=1,
        max_value=10,
        value=5,
        step=1,
        key="num_questions_slider"
    )
    
    # Save subject and week to session state
    st.session_state.generation_subject = subject
    st.session_state.generation_week = week
    st.session_state.num_questions = num_questions
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload a file (PDF or TXT)",
        type=["pdf", "txt"],
        key="file_upload",
        accept_multiple_files=False
    )
    
    # Show upload button if a file is selected
    if uploaded_file:
        st.session_state.file_uploaded = True
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Questions from Upload", key="generate_btn", use_container_width=True):
                if not subject:
                    st.error("Please enter a subject.")
                else:
                    # Process the file and generate questions
                    with st.spinner("Processing file and generating questions..."):
                        questions = process_uploaded_file(
                            uploaded_file, 
                            subject, 
                            week,
                            st.session_state.email,
                            num_questions=st.session_state.num_questions
                        )
                        st.session_state.generated_questions = questions
                        st.session_state.selected_questions = {}
                        
                        # Show success or error message
                        if st.session_state.api_error:
                            st.error(st.session_state.api_error)
                        elif questions:
                            st.success(f"Generated {len(questions)} questions!")
                        else:
                            st.warning("No questions could be generated from this file.")
    
    # Allow generating additional questions if there's a knowledge base available
    if not uploaded_file and is_subscribed:
        # Check if there's an existing knowledge base for this subject/week
        has_kb = False
        if subject and subject in st.session_state.data:
            if "vector_store_metadata" in st.session_state.data[subject]:
                if str(week) in st.session_state.data[subject]["vector_store_metadata"]:
                    has_kb = True
        
        if has_kb:
            st.info(f"You already have a knowledge base for {subject}, Week {week}.")
            
            if st.button("Generate More Questions", key="generate_more_btn", use_container_width=True):
                # Generate questions without uploading a new file
                with st.spinner("Generating additional questions..."):
                    questions = generate_questions_without_upload(
                        subject, 
                        week, 
                        st.session_state.email
                    )
                    st.session_state.generated_questions = questions
                    st.session_state.selected_questions = {}
                    
                    # Show success or error message
                    if st.session_state.api_error:
                        st.error(st.session_state.api_error)
                    elif questions:
                        st.success(f"Generated {len(questions)} additional questions!")
                    else:
                        st.warning("No additional questions could be generated.")

def display_question_review():
    """Display the generated questions and allow selection"""
    # Check if we have generated questions
    if not st.session_state.generated_questions:
        return
    
    # Divider before questions
    st.divider()
    st.subheader("Review Generated Questions")
    st.write("Select the questions you want to add to your study collection.")
    
    # Reset selection if clicking reset
    if st.button("Reset Selection", key="reset_selection", use_container_width=True):
        st.session_state.selected_questions = {}
        st.rerun()
    
    # Display each question with a checkbox
    for i, q in enumerate(st.session_state.generated_questions):
        question = q.get("question", "")
        answer = q.get("answer", "")
        
        # Create unique key for each checkbox
        checkbox_key = f"q_{i}"
        
        # Check if this question is already selected
        is_selected = checkbox_key in st.session_state.selected_questions
        
        with st.container(border=True):
            col1, col2 = st.columns([0.9, 0.1])
            
            with col1:
                st.markdown(f"**Q{i+1}: {question}**")
            
            with col2:
                # Use the checkbox to select/deselect the question
                selected = st.checkbox("", value=is_selected, key=checkbox_key)
                
                # Update the selected questions dictionary
                if selected and checkbox_key not in st.session_state.selected_questions:
                    st.session_state.selected_questions[checkbox_key] = q
                elif not selected and checkbox_key in st.session_state.selected_questions:
                    del st.session_state.selected_questions[checkbox_key]
            
            # Show expected answer in an expander
            with st.expander("View expected answer"):
                st.write(answer if answer else "No answer provided.")
    
    # Show add button if questions are selected
    if st.session_state.selected_questions:
        st.success(f"{len(st.session_state.selected_questions)} questions selected.")
        
        if st.button("Add Selected Questions", key="add_selected", type="primary", use_container_width=True):
            subject = st.session_state.generation_subject
            week = st.session_state.generation_week
            
            if not subject:
                st.error("Please enter a subject.")
            else:
                # Add selected questions to data
                st.session_state.data = add_selected_questions_to_data(
                    subject, 
                    week, 
                    st.session_state.selected_questions, 
                    st.session_state.email
                )
                
                # Show success message and clear selected questions
                st.success(f"Added {len(st.session_state.selected_questions)} questions to {subject}, Week {week}!")
                st.session_state.selected_questions = {}
                st.session_state.generated_questions = []
                
                # Show balloons
                st.balloons()
                
                # Rerun to update UI
                time.sleep(1)  # Brief pause for visual feedback
                st.rerun()

def display_kb_management():
    """Display the knowledge base management interface"""
    # Use the enhanced KB management from our new module
    display_enhanced_kb_management()

def display_error_message(error_msg: str):
    """Display an error message"""
    st.error(error_msg) 
"""
Refactored UI components for add_ai module.

This module provides UI elements and display functions for the AI Question Generator feature,
using the shared modules for code reuse.
"""
import streamlit as st
import time
from typing import Dict, List, Any, Optional

# Import from shared modules
from features.content.shared.vector_store_manager import display_enhanced_kb_management
from features.content.shared.vector_store_utils import (
    generate_questions_from_vector_store,
    add_selected_questions_to_data
)
from features.content.shared.ui_components import (
    render_questions_with_selection,
    display_file_upload_interface
)

# Import core functionality still needed from add_ai_core
from features.content.add_ai.add_ai_core import process_uploaded_file, generate_questions_without_upload

def init_session_state():
    """Initialize session state variables for the AI question generator"""
    # Generation state
    if "generation_subject" not in st.session_state:
        st.session_state.generation_subject = ""
    if "generation_week" not in st.session_state:
        st.session_state.generation_week = 1
    if "generation_in_progress" not in st.session_state:
        st.session_state.generation_in_progress = False
    if "generated_questions" not in st.session_state:
        st.session_state.generated_questions = []
    if "selected_questions" not in st.session_state:
        st.session_state.selected_questions = {}
    if "api_error" not in st.session_state:
        st.session_state.api_error = None
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False

def on_generate_questions(subject: str, week: int, uploaded_file):
    """Callback for when the generate button is clicked"""
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

def display_file_upload(is_subscribed: bool):
    """Display the file upload interface for generating questions"""
    # Get the list of existing subjects from the user's data
    subject_options = []
    if "data" in st.session_state and st.session_state.data:
        # Just use the subjects from the user's data, no common subjects added
        subject_options = list(st.session_state.data.keys())
        
        # Sort alphabetically
        subject_options.sort()
    else:
        # Empty list if no data is available - will show "Create New" option only
        subject_options = []
    
    # Use the shared file upload interface with subject dropdown but without the generate button
    col1, col2 = st.columns(2)
    
    with col1:
        # Subject input 
        if subject_options:
            # Add "Create New" option to allow custom input
            all_options = subject_options.copy()
            if "Create New" not in all_options:
                all_options.append(" + New")
            
            selected_subject = st.selectbox(
                "Subject", 
                options=all_options,
                index=all_options.index(st.session_state.generation_subject) if st.session_state.generation_subject in all_options else 0,
                key="subject_input_select"
            )
            
            # If "Create New" is selected, show a text input
            if selected_subject == " + New":
                subject = st.text_input(
                    "New Subject Name", 
                    value="",
                    placeholder="e.g., Computer Science",
                    key="subject_input_custom"
                )
            else:
                subject = selected_subject
        else:
            # If no subject options provided, fall back to text input
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
        max_value=20,
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
    
    # Set file uploaded flag
    file_uploaded = uploaded_file is not None
    st.session_state.file_uploaded = file_uploaded
    
    # Check if there's an existing knowledge base for this subject/week
    has_kb = False
    if subject and subject in st.session_state.data:
        if "vector_store_metadata" in st.session_state.data[subject]:
            if str(week) in st.session_state.data[subject]["vector_store_metadata"]:
                has_kb = True
    
    # Display two buttons side by side
    col1, col2 = st.columns(2)
    
    with col1:
        # Generate from Upload button - enabled only if a file is uploaded
        if st.button("Generate from Upload", 
                    key="generate_from_upload_btn", 
                    use_container_width=True,
                    disabled=not file_uploaded,
                    type="primary" if file_uploaded else "secondary"):
            if not subject:
                st.error("Please enter a subject.")
            elif file_uploaded:
                # Call the callback with the uploaded file info
                on_generate_questions(subject, week, uploaded_file)
    
    with col2:
        # Generate from Previous Uploads button - enabled only if a knowledge base exists
        if st.button("Generate from Previous Uploads", 
                    key="generate_from_previous_btn", 
                    use_container_width=True,
                    disabled=not has_kb,
                    type="primary" if has_kb else "secondary"):
            if not subject:
                st.error("Please enter a subject.")
            elif has_kb:
                # Generate questions without uploading a new file
                with st.spinner("Generating additional questions..."):
                    questions = generate_questions_without_upload(
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
                        st.success(f"Generated {len(questions)} additional questions!")
                    else:
                        st.warning("No additional questions could be generated.")

    # Button state explanation
    if not file_uploaded and not has_kb:
        st.info("Upload a file to generate questions or select a subject and week that has previous uploads.")
    elif not file_uploaded:
        st.info("Previous uploads found for this subject and week. You can generate more questions from them or upload a new file.")
    elif not has_kb:
        st.info("First time using this subject and week. Upload your file to start building a knowledge base.")

    # Add collapsible information section at the bottom
    with st.expander("💡 Tips for Generating Questions"):
        st.markdown("""
        ### Recommendations for Best Results
        
        - **Generate questions one file at a time** for the most focused and relevant questions
        - You can upload various materials such as:
          - Lecture slides
          - Transcripts
          - Reading materials
          - Course notes
        - Each file you upload is stored in your knowledge base
        - You can chat with an AI tutor about this content on the **Subject Tutor** page
        - For best results, use PDF files with clear text formatting
        
        Questions are generated based on the content's key concepts, so more specific materials will yield better questions!
        """)

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
    
    # Use the shared questions renderer
    render_questions_with_selection(
        questions=st.session_state.generated_questions,
        selected_questions=st.session_state.selected_questions
    )
    
    # Show add button if questions are selected
    if st.session_state.selected_questions:
        st.success(f"{len(st.session_state.selected_questions)} questions selected.")
        
        if st.button("Add Selected Questions", key="add_selected", type="primary", use_container_width=True):
            subject = st.session_state.generation_subject
            week = st.session_state.generation_week
            
            if not subject:
                st.error("Please enter a subject.")
            else:
                # Add selected questions to data using the shared function
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
    # Use the shared KB management from our shared module
    display_enhanced_kb_management()

def display_error_message(error_msg: str):
    """Display an error message"""
    st.error(error_msg) 
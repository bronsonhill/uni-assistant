"""
Refactored UI components for add_ai module.

This module provides UI elements and display functions for the AI Question Generator feature,
using OpenAI's file and response API.
"""
import streamlit as st
import time
import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
import logging
from pathlib import Path

# Import UI components
from features.content.shared.ui_components import (
    render_questions_with_selection,
    display_file_upload_interface
)

# Import question generator
from question_generator import generate_questions_from_file


from features.content.add_ai.add_ai_core_refactored import add_selected_questions_to_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    if "custom_questions" not in st.session_state:
        st.session_state.custom_questions = ""

def process_uploaded_file(uploaded_file, subject: str, week: int, user_email: str, num_questions: int = 5):
    """
    Process the uploaded file and generate questions using OpenAI's file and response API
    
    Args:
        uploaded_file: The streamlit uploaded file object (can be None if using custom text)
        subject: The subject for the questions
        week: The week number for the questions
        user_email: The user's email address
        num_questions: Number of questions to generate (default: 5)
    
    Returns:
        List of generated questions
    """
    st.session_state.generation_in_progress = True
    st.session_state.api_error = None
    st.session_state.num_questions = num_questions
    
    try:
        # If no file is uploaded but custom text is provided, generate directly from text
        if not uploaded_file and st.session_state.custom_questions.strip():
            # Initialize OpenAI client
            client = setup_openai_client()
            if not client:
                st.session_state.api_error = "Could not initialize OpenAI client."
                st.session_state.generation_in_progress = False
                return []
            
            # Generate questions from custom text using the responses API
            response = client.responses.create(
                model="gpt-4o",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"Generate {num_questions} questions about {subject} week {week}. {st.session_state.custom_questions}"
                            }
                        ]
                    }
                ]
            )
            
            # Process the response into questions
            questions = []
            content = response.choices[0].message.content
            # Split content into question-answer pairs
            qa_pairs = content.split("\n\n")
            for pair in qa_pairs:
                if "Question:" in pair and "Answer:" in pair:
                    q, a = pair.split("Answer:", 1)
                    questions.append({
                        "question": q.replace("Question:", "").strip(),
                        "answer": a.strip()
                    })
            
            return questions[:num_questions]
        
        # If no file is uploaded and no custom text, return empty list
        if not uploaded_file:
            st.session_state.api_error = "Please upload a file or provide custom text to generate questions."
            st.session_state.generation_in_progress = False
            return []
        
        # Handle uploaded file
        if isinstance(uploaded_file, list):
            if not uploaded_file:  # Empty list
                st.session_state.api_error = "No file was uploaded."
                st.session_state.generation_in_progress = False
                return []
            file_to_process = uploaded_file[0]
        else:
            file_to_process = uploaded_file
            
        # Validate file object
        if not hasattr(file_to_process, 'name'):
            st.session_state.api_error = "Invalid file object."
            st.session_state.generation_in_progress = False
            return []
            
        # Get file info
        file_name = file_to_process.name
        file_type = file_name.split('.')[-1].lower() if '.' in file_name else ''
        
        # Validate file type
        if not file_type or file_type not in ["pdf", "txt"]:
            st.session_state.api_error = "Only PDF and TXT files are supported at this time. Please ensure your file has a .pdf or .txt extension."
            st.session_state.generation_in_progress = False
            return []
        
        # Create a temporary directory if it doesn't exist
        temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the file to disk temporarily
        file_path = os.path.join(temp_dir, file_name)
        with open(file_path, "wb") as f:
            f.write(file_to_process.getvalue())
        
        try:
            # Read the file as bytes
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            # Generate questions using the new question generator
            questions = generate_questions_from_file(
                file_bytes=file_bytes,
                file_type=file_type,
                subject=subject,
                week=str(week),
                num_questions=num_questions
            )
            
            return questions
            
        finally:
            # Clean up the temporary file
            try:
                os.remove(file_path)
            except:
                pass
        
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        logger.error(error_msg)
        st.session_state.api_error = error_msg
        st.session_state.generation_in_progress = False
        return []

def generate_questions_without_upload(subject: str, week: int, user_email: str, num_questions: int = 5, selected_files: List[str] = None):
    """
    Generate questions without uploading a file using OpenAI's response API
    
    Args:
        subject: The subject for the questions
        week: The week number for the questions
        user_email: The user's email address
        num_questions: Number of questions to generate
        selected_files: Optional list of file IDs to use
        
    Returns:
        List of generated questions
    """
    st.session_state.generation_in_progress = True
    st.session_state.api_error = None
    
    try:
        # Initialize OpenAI client
        client = setup_openai_client()
        if not client:
            st.session_state.api_error = "Could not initialize OpenAI client."
            st.session_state.generation_in_progress = False
            return []
        
        # Prepare input content
        input_content = []
        
        # Add selected files if any
        if selected_files:
            for file_id in selected_files:
                input_content.append({
                    "type": "input_file",
                    "file_id": file_id
                })
        
        # Add the question generation prompt
        input_content.append({
            "type": "input_text",
            "text": f"Generate {num_questions} questions about {subject} week {week}. {st.session_state.custom_questions}"
        })
        
        # Generate questions using the responses API
        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content": input_content
                }
            ]
        )
        
        # Process the response into questions
        questions = []
        content = response.choices[0].message.content
        # Split content into question-answer pairs
        qa_pairs = content.split("\n\n")
        for pair in qa_pairs:
            if "Question:" in pair and "Answer:" in pair:
                q, a = pair.split("Answer:", 1)
                questions.append({
                    "question": q.replace("Question:", "").strip(),
                    "answer": a.strip()
                })
        
        return questions[:num_questions]
        
    except Exception as e:
        print(f"Error generating questions without upload: {e}")
        st.session_state.api_error = f"An error occurred: {str(e)}"
        st.session_state.generation_in_progress = False
        return []

def get_api_key() -> Optional[str]:
    """
    Get the OpenAI API key from environment or secrets
    
    Returns:
        API key if found, None otherwise
    """
    try:
        # First check Streamlit secrets
        return st.secrets["OPENAI_API_KEY"]
    except (KeyError, AttributeError):
        # Fallback to environment variable
        return os.getenv("OPENAI_API_KEY")

def setup_openai_client():
    """Initialize and return the OpenAI client"""
    api_key = None
    try:
        # First check Streamlit secrets
        api_key = st.secrets["OPENAI_API_KEY"]
    except (KeyError, AttributeError):
        # Fallback to environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        
    if not api_key:
        st.error("OpenAI API key not found. Please set it in your environment variables or contact support.")
        return None
        
    return OpenAI(api_key=api_key)

def extract_vector_store_id(vector_store_data):
    """
    Extract the vector store ID from the data structure
    
    Args:
        vector_store_data: The vector store data (can be string, dict, etc.)
        
    Returns:
        The vector store ID as a string
    """
    if isinstance(vector_store_data, dict) and "id" in vector_store_data:
        return vector_store_data["id"]
    else:
        return str(vector_store_data)

def get_vector_store_id_for_subject_week(subject, week):
    """
    Get the vector store ID for a subject and week
    
    Args:
        subject: The subject
        week: The week number
        
    Returns:
        The vector store ID or None if not found
    """
    try:
        if "data" not in st.session_state:
            return None
            
        if subject not in st.session_state.data:
            return None
            
        if "vector_store_metadata" not in st.session_state.data[subject]:
            return None
            
        week_str = str(week)
        if week_str not in st.session_state.data[subject]["vector_store_metadata"]:
            return None
            
        # Extract the vector store ID
        vector_store_data = st.session_state.data[subject]["vector_store_metadata"][week_str]
        return extract_vector_store_id(vector_store_data)
        
    except Exception as e:
        print(f"Error getting vector store ID: {e}")
        return None

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
    # Initialize data if user is logged in
    if "email" in st.session_state:
        if "data" not in st.session_state:
            from Home import load_data
            st.session_state.data = load_data(st.session_state.email)
    
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
    
    # Add custom questions text area
    st.text_area(
        "Optional: Specify topics or questions to focus on from your uploaded content, or prompt AI to generate questions based on a specific topic or question.",
        key="custom_questions",
        help="Enter specific topics or questions you'd like to be covered in the generated questions. This will help guide the AI to focus on particular areas of interest."
    )
    
    # Set file uploaded flag
    file_uploaded = uploaded_file is not None
    st.session_state.file_uploaded = file_uploaded
    
    # Display generate button
    if st.button("Generate Questions", 
                key="generate_btn", 
                use_container_width=True,
                type="primary"):
        if not subject:
            st.error("Please enter a subject.")
        else:
            # Call the callback with the uploaded file info (can be None)
            on_generate_questions(subject, week, uploaded_file)
    
    # Button state explanation
    if not file_uploaded and not st.session_state.custom_questions.strip():
        st.info("Upload a file or enter custom text to generate questions.")
    elif not file_uploaded:
        st.info("You can generate questions from your custom text input or upload a file.")
    elif not st.session_state.custom_questions.strip():
        st.info("You can generate questions from your uploaded file or add custom text input.")

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

def display_error_message(error_msg: str):
    """Display an error message"""
    st.error(error_msg)

def setup_page():
    """Setup the Streamlit page configuration"""
    st.set_page_config(
        page_title="AI Question Generator",
        page_icon="❓",
        layout="wide"
    )
    
    # Initialize session state
    if "generation_subject" not in st.session_state:
        st.session_state.generation_subject = ""
    if "generation_week" not in st.session_state:
        st.session_state.generation_week = 1
    if "generation_in_progress" not in st.session_state:
        st.session_state.generation_in_progress = False
    if "generated_questions" not in st.session_state:
        st.session_state.generated_questions = []
    if "file_uploaded" not in st.session_state:
        st.session_state.file_uploaded = False
    if "custom_questions" not in st.session_state:
        st.session_state.custom_questions = ""

def main():
    """Main application entry point"""
    # Setup page
    setup_page()
    
    # Render UI
    st.title("AI Question Generator")
    
    # Display file upload interface
    display_file_upload(is_subscribed=True)
    
    # Display question review
    display_question_review()

if __name__ == "__main__":
    main() 
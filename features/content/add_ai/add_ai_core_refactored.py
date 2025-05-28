"""
Refactored core functionality for add_ai module.

This module provides core functions for the AI Question Generator feature,
using the services for code reuse.
"""
import streamlit as st
import time
import os
import sys
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Home
from Home import load_data, save_data, add_question

# Import from services
from services.rag_manager import RAGManager
from services.openai_service import OpenAIService
from services.vector_store_service import VectorStoreService
from question_generator import generate_questions_from_file

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

def process_uploaded_file(uploaded_file, subject: str, week: int, user_email: str):
    """
    Process the uploaded file and generate questions
    
    Args:
        uploaded_file: The streamlit uploaded file object
        subject: The subject for the questions
        week: The week number for the questions
        user_email: The user's email address
    
    Returns:
        List of generated questions
    """
    st.session_state.generation_in_progress = True
    st.session_state.api_error = None
    
    try:
        # Handle uploaded file - support multiple files or single file
        if isinstance(uploaded_file, list):
            # Multiple files uploaded
            file_to_process = uploaded_file[0]  # Process the first file for now
        else:
            # Single file uploaded
            file_to_process = uploaded_file
            
        # Get file info
        file_name = file_to_process.name
        file_type = file_name.split('.')[-1].lower()
        
        # Validate file type
        if file_type not in ["pdf", "txt"]:
            st.session_state.api_error = "Only PDF and TXT files are supported at this time."
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
                num_questions=5
            )
            
            return questions
            
        finally:
            # Clean up the temporary file
            try:
                os.remove(file_path)
            except:
                pass
    
    except Exception as e:
        print(f"Error processing file: {e}")
        st.session_state.api_error = f"An error occurred: {str(e)}"
        st.session_state.generation_in_progress = False
        return []

def generate_questions_without_upload(subject: str, week: int, user_email: str):
    """
    Generate questions without uploading a file (uses existing vector store)
    
    Args:
        subject: The subject for the questions
        week: The week number for the questions
        user_email: The user's email address
        
    Returns:
        List of generated questions
    """
    st.session_state.generation_in_progress = True
    st.session_state.api_error = None
    
    try:
        # Initialize services
        rag_manager = init_services()
        if not rag_manager:
            st.session_state.api_error = "Could not initialize services."
            st.session_state.generation_in_progress = False
            return []
        
        # Generate questions from the vector store
        questions = rag_manager.generate_questions_with_rag(
            subject=subject,
            week=str(week),
            num_questions=5,
            email=user_email
        )
        
        return questions
        
    except Exception as e:
        print(f"Error generating questions without upload: {e}")
        st.session_state.api_error = f"An error occurred: {str(e)}"
        st.session_state.generation_in_progress = False
        return []

def init_services() -> Optional[RAGManager]:
    """
    Initialize the required services
    
    Returns:
        RAGManager instance if successful, None otherwise
    """
    try:
        # Get API key
        api_key = get_api_key()
        if not api_key:
            return None
            
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Initialize services
        openai_service = OpenAIService(client)
        vector_store_service = VectorStoreService(client)
        rag_manager = RAGManager(openai_service, vector_store_service)
        
        return rag_manager
        
    except Exception as e:
        print(f"Error initializing services: {e}")
        return None

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
    

def add_selected_questions_to_data(subject: str, week: int, selected_questions: Dict, user_email: str) -> Dict:
    """
    Add selected questions to the user's data
    
    Args:
        subject: The subject for the questions
        week: The week number for the questions
        selected_questions: Dictionary of selected questions (index: question)
        user_email: The user's email address
    
    Returns:
        Updated data dictionary
    """
    # Get current data
    data = st.session_state.data
    
    # Add each selected question
    for idx, q in selected_questions.items():
        data = add_question(
            data, 
            subject, 
            week, 
            q.get("question", ""), 
            q.get("answer", ""),
            email=user_email
        )
    
    # Save the updated data
    save_data(data, user_email)
    return data
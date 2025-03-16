"""
Refactored core functionality for add_ai module.

This module provides core functions for the AI Question Generator feature,
using the shared modules for code reuse.
"""
import streamlit as st
import time
import os
import sys
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Home
from Home import load_data, save_data

# Import from shared modules
from features.content.shared.vector_store_manager import extract_vector_store_id, init_rag_manager
from features.content.shared.vector_store_utils import (
    create_vector_store,
    delete_vector_store,
    generate_questions_from_vector_store,
    add_selected_questions_to_data
)

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
            
        # Read file content
        file_bytes = file_to_process.getvalue()
        file_name = file_to_process.name
        file_type = file_name.split('.')[-1].lower()
        
        # Validate file type
        if file_type not in ["pdf", "txt"]:
            st.session_state.api_error = "Only PDF and TXT files are supported at this time."
            st.session_state.generation_in_progress = False
            return []
        
        # Check if OpenAI API key is set
        api_key = None
        try:
            # First check Streamlit secrets
            api_key = st.secrets["OPENAI_API_KEY"]
        except (KeyError, AttributeError):
            # Fallback to environment variable
            api_key = os.getenv("OPENAI_API_KEY")
            
        if not api_key:
            st.session_state.api_error = "OpenAI API key not found. Please set it in your environment variables or contact support."
            st.session_state.generation_in_progress = False
            return []
        
        # Create a vector store for the subject and week using the shared function
        vector_store_id = create_vector_store(subject, week, user_email, file_bytes, file_name)
        
        if not vector_store_id:
            st.session_state.api_error = "Could not create vector store for the uploaded file."
            st.session_state.generation_in_progress = False
            return []
            
        # Generate questions from the vector store using the shared function
        return generate_questions_from_vector_store(vector_store_id, subject, week)
    
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
        # Initialize the RAG manager using the shared function
        if not init_rag_manager(user_email):
            st.session_state.api_error = "Could not initialize RAG manager"
            st.session_state.generation_in_progress = False
            return []
        
        # Get the vector store ID
        vector_store_id = None
        if (subject in st.session_state.data and 
            "vector_store_metadata" in st.session_state.data[subject] and
            str(week) in st.session_state.data[subject]["vector_store_metadata"]):
            
            vector_store_id = st.session_state.data[subject]["vector_store_metadata"][str(week)]
        
        # Extract the actual ID using the shared function
        actual_id = extract_vector_store_id(vector_store_id)
        if actual_id != vector_store_id:
            print(f"Extracted vector store ID for question generation: {actual_id} (from {type(vector_store_id).__name__})")
            vector_store_id = actual_id
        
        if not vector_store_id:
            st.session_state.api_error = "No knowledge base found for this subject and week. Please upload a file first."
            st.session_state.generation_in_progress = False
            return []
        
        # Generate questions from the vector store using the shared function
        return generate_questions_from_vector_store(vector_store_id, subject, week)
        
    except Exception as e:
        print(f"Error generating questions without upload: {e}")
        st.session_state.api_error = f"An error occurred: {str(e)}"
        st.session_state.generation_in_progress = False
        return [] 
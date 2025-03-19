"""
Core functionality for add_ai module.

This module provides core functions for the AI Question Generator feature, 
including file processing, question generation, and knowledge base management.
"""
import streamlit as st
import time
import os
import sys
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Home and related modules
from Home import load_data, save_data, add_question, get_user_email
from rag_manager import RAGManager

# Import vector store ID extraction function from shared module
from features.content.shared.vector_store_manager import extract_vector_store_id

# Import vector store ID extraction (forward reference - will be defined when module is fully loaded)
extract_vector_store_id = None

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

def init_rag_manager(user_email: str):
    """Initialize the RAG manager and load vector stores"""
    if "rag_manager" not in st.session_state or not hasattr(st.session_state.rag_manager, 'delete_vector_store'):
        try:
            # Reinitialize if we don't have the expected methods
            print("Initializing RAGManager with all required methods")
            st.session_state.rag_manager = RAGManager()
            # Load any existing study materials from data
            if "data" in st.session_state:
                st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data, user_email)
            return True
        except Exception as e:
            print(f"Error initializing RAGManager: {e}")
            st.session_state.rag_manager = None
            return False
    return True

def process_uploaded_file(uploaded_file, subject: str, week: int, user_email: str, num_questions: int = 5):
    """
    Process the uploaded file and generate questions
    
    Args:
        uploaded_file: The streamlit uploaded file object
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
        
        # Create a vector store for the subject and week
        vector_store_id = create_vector_store(subject, week, user_email, file_bytes, file_name)
        
        if not vector_store_id:
            st.session_state.api_error = "Could not create vector store for the uploaded file. Check the logs for details."
            st.session_state.generation_in_progress = False
            return []
            
        # Generate questions from the vector store
        return generate_questions_from_vector_store(vector_store_id, subject, week, num_questions)
    
    except Exception as e:
        print(f"Error processing file: {e}")
        st.session_state.api_error = f"An error occurred: {str(e)}"
        st.session_state.generation_in_progress = False
        return []

def generate_questions_without_upload(subject: str, week: int, user_email: str, num_questions: int = 5):
    """
    Generate questions without uploading a file (uses existing vector store)
    
    Args:
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
        # Initialize the RAG manager
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
        
        # Extract the actual ID using our utility
        if vector_store_id and extract_vector_store_id:
            actual_id = extract_vector_store_id(vector_store_id)
            if actual_id != vector_store_id:
                print(f"Extracted vector store ID for question generation: {actual_id} (from {type(vector_store_id).__name__})")
                vector_store_id = actual_id
        
        if not vector_store_id:
            st.session_state.api_error = "No knowledge base found for this subject and week. Please upload a file first."
            st.session_state.generation_in_progress = False
            return []
        
        # Generate questions from the vector store
        return generate_questions_from_vector_store(vector_store_id, subject, week, num_questions)
        
    except Exception as e:
        print(f"Error generating questions without upload: {e}")
        st.session_state.api_error = f"An error occurred: {str(e)}"
        st.session_state.generation_in_progress = False
        return []

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

def create_vector_store(subject: str, week: int, user_email: str, file_bytes: bytes, file_name: str) -> Optional[str]:
    """
    Create a vector store for the subject and week
    
    Args:
        subject: The subject for the vector store
        week: The week number for the vector store
        user_email: The user's email address
        file_bytes: The file content as bytes
        file_name: The name of the file
        
    Returns:
        The vector store ID if successful, otherwise None
    """
    # Initialize the RAG manager
    if not init_rag_manager(user_email):
        print("Could not initialize RAG manager")
        return None
    
    # Check if we already have a vector store for this subject and week
    vector_store_id = None
    
    if (subject in st.session_state.data and 
        "vector_store_metadata" in st.session_state.data[subject] and
        str(week) in st.session_state.data[subject]["vector_store_metadata"]):
        
        # Get the existing vector store ID
        existing_id = st.session_state.data[subject]["vector_store_metadata"][str(week)]
        
        # Use the vector store ID extraction utility to handle various formats
        if extract_vector_store_id:
            vector_store_id = extract_vector_store_id(existing_id)
            if vector_store_id != existing_id:
                print(f"Extracted existing vector store ID: {vector_store_id} (from {type(existing_id).__name__})")
        else:
            # Fallback if extract_vector_store_id is not available
            if isinstance(existing_id, dict) and "id" in existing_id:
                vector_store_id = existing_id["id"]
            else:
                vector_store_id = existing_id
    
    try:
        # If we don't have a vector store, create one
        if not vector_store_id:
            # Create a new vector store
            vector_store = st.session_state.rag_manager.get_or_create_vector_store(
                subject=subject,
                week=str(week),
                email=user_email
            )
            vector_store_id = vector_store["id"]
            
            # Save the vector store ID in the data
            if subject not in st.session_state.data:
                st.session_state.data[subject] = {}
            
            if "vector_store_metadata" not in st.session_state.data[subject]:
                st.session_state.data[subject]["vector_store_metadata"] = {}
            
            st.session_state.data[subject]["vector_store_metadata"][str(week)] = {
                "id": vector_store_id,
                "name": f"{subject}_Week_{week}"
            }
            
            # Save the updated data
            save_data(st.session_state.data, user_email)
        
        # Add the file to the vector store
        try:
            st.session_state.rag_manager.add_file_to_vector_store(
                vector_store_id=vector_store_id,
                file_bytes=file_bytes,
                file_name=file_name
            )
            return vector_store_id
        except Exception as upload_error:
            print(f"Error adding file to vector store: {upload_error}")
            return None
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

def delete_vector_store(subject: str, week: str, user_email: str) -> bool:
    """Delete the vector store for a subject and week"""
    # Initialize the RAG manager
    if not init_rag_manager(user_email):
        return False
    
    # Get the vector store ID
    if (subject in st.session_state.data and 
        "vector_store_metadata" in st.session_state.data[subject] and
        str(week) in st.session_state.data[subject]["vector_store_metadata"]):
        
        # Get the vector store ID
        vector_store_id = st.session_state.data[subject]["vector_store_metadata"][str(week)]
        
        # Use the vector store ID extraction utility to handle various formats
        if extract_vector_store_id:
            actual_id = extract_vector_store_id(vector_store_id)
            if actual_id != vector_store_id:
                print(f"Extracted vector store ID for deletion: {actual_id} (from {type(vector_store_id).__name__})")
                vector_store_id = actual_id
        else:
            # Fallback if extract_vector_store_id is not available
            if isinstance(vector_store_id, dict) and "id" in vector_store_id:
                vector_store_id = vector_store_id["id"]
        
        try:
            # Delete the vector store
            st.session_state.rag_manager.delete_vector_store(vector_store_id)
            
            # Remove the vector store ID from the data
            del st.session_state.data[subject]["vector_store_metadata"][str(week)]
            
            # Save the updated data
            save_data(st.session_state.data, user_email)
            
            return True
        except Exception as e:
            print(f"Error deleting vector store: {e}")
            return False
    
    return False

def generate_questions_from_vector_store(vector_store_id: str, subject: str, week: int, num_questions: int = 5) -> List[Dict[str, Any]]:
    """
    Generate questions from a vector store
    
    Args:
        vector_store_id: The vector store ID
        subject: The subject for the questions
        week: The week number for the questions
        num_questions: Number of questions to generate (default: 5)
        
    Returns:
        List of generated questions
    """
    try:
        # Use the vector store ID extraction utility to handle various formats
        if extract_vector_store_id:
            actual_id = extract_vector_store_id(vector_store_id)
            if actual_id != vector_store_id:
                print(f"Extracted vector store ID for question generation: {actual_id} (from {type(vector_store_id).__name__})")
                vector_store_id = actual_id
                
        # Get existing questions for this subject/week if any
        existing_questions = []
        if (subject in st.session_state.data and 
            str(week) in st.session_state.data[subject] and
            str(week) != "vector_store_metadata"):
            existing_questions = st.session_state.data[subject][str(week)]
        
        # Generate questions using generate_questions_with_rag instead
        # Default to 5 questions if num_questions is not specified
        new_questions = st.session_state.rag_manager.generate_questions_with_rag(
            subject=subject,
            week=str(week),
            num_questions=num_questions,
            existing_questions=existing_questions
        )
        
        return new_questions
        
    except Exception as e:
        print(f"Error generating questions from vector store: {e}")
        st.session_state.api_error = f"Error generating questions: {str(e)}"
        return []
    finally:
        # Make sure to set generation_in_progress to False
        st.session_state.generation_in_progress = False

# Import the extract_vector_store_id after defining our functions to avoid circular imports
try:
    from features.content.add_ai.add_ai_vector_manager import extract_vector_store_id
except ImportError:
    print("Warning: Could not import extract_vector_store_id. Vector store ID extraction will be limited.") 
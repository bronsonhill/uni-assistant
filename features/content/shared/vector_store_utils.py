"""
Shared vector store utilities.

This module provides core functionality for vector store operations like creation and deletion.
"""
import streamlit as st
from typing import Dict, List, Any, Optional

# Import from Home
from Home import load_data, save_data

# Import shared functions
from features.content.shared.vector_store_common import extract_vector_store_id
from features.content.shared.vector_store_manager import init_rag_manager

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
    
    try:
        # File type from the file name
        file_type = file_name.split('.')[-1].lower()
        
        # Create or update vector store using the correct method
        result = st.session_state.rag_manager.create_or_update_vector_store(
            subject=subject,
            week=str(week),
            file_bytes=file_bytes,
            file_type=file_type,
            file_name=file_name,
            email=user_email
        )
        
        # Save the result to session state data
        if result and "id" in result:
            # Update the data in session state
            if subject not in st.session_state.data:
                st.session_state.data[subject] = {}
            
            if "vector_store_metadata" not in st.session_state.data[subject]:
                st.session_state.data[subject]["vector_store_metadata"] = {}
            
            st.session_state.data[subject]["vector_store_metadata"][str(week)] = {
                "id": result["id"],
                "name": result.get("name", f"{subject}_Week_{week}")
            }
            
            # Save the updated data
            save_data(st.session_state.data, user_email)
            
            return result["id"]
            
        return None
    except Exception as e:
        print(f"Error creating vector store: {e}")
        return None

def delete_vector_store(subject: str, week: str, user_email: str) -> bool:
    """
    Delete the vector store for a subject and week
    
    Args:
        subject: The subject for the vector store
        week: The week number/name for the vector store
        user_email: The user's email address
        
    Returns:
        True if deletion was successful, False otherwise
    """
    # Initialize the RAG manager
    if not init_rag_manager(user_email):
        return False
    
    # Get the vector store ID
    if (subject in st.session_state.data and 
        "vector_store_metadata" in st.session_state.data[subject] and
        str(week) in st.session_state.data[subject]["vector_store_metadata"]):
        
        # Get the vector store ID
        vector_store_id = st.session_state.data[subject]["vector_store_metadata"][str(week)]
        
        # Extract the vector store ID
        actual_id = extract_vector_store_id(vector_store_id)
        if actual_id != vector_store_id:
            print(f"Extracted vector store ID for deletion: {actual_id} (from {type(vector_store_id).__name__})")
            vector_store_id = actual_id
        
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

def generate_questions_from_vector_store(vector_store_id: str, subject: str, week: int) -> List[Dict[str, Any]]:
    """
    Generate questions from a vector store
    
    Args:
        vector_store_id: The vector store ID
        subject: The subject for the questions
        week: The week number for the questions
        
    Returns:
        List of generated questions
    """
    try:
        # Extract the vector store ID
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
        
        # Generate questions from the vector store
        new_questions = st.session_state.rag_manager.generate_questions_with_rag(
            subject=subject,
            week=str(week),
            num_questions=5,
            existing_questions=existing_questions
        )
        
        return new_questions
        
    except Exception as e:
        print(f"Error generating questions from vector store: {e}")
        st.session_state.api_error = f"Error generating questions: {str(e)}"
        return []
    finally:
        # Make sure to set generation_in_progress to False if it exists
        if "generation_in_progress" in st.session_state:
            st.session_state.generation_in_progress = False

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
    
    # Import from Home
    from Home import add_question
    
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
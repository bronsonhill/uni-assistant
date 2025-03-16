"""
Core functionality for tutor module.

This module provides core functions to handle threads, assistants, and messages
for the AI tutor feature.
"""
import streamlit as st
import time
import sys
import os
from typing import Dict, List, Optional, Any, Callable

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Home and mongodb
import mongodb
from rag_manager import RAGManager

# Import RAG manager initialization and utilities
from features.content.tutor import init_rag_manager
from features.content.tutor.vector_store_manager import extract_vector_store_id

def init_session_state():
    """Initialize tutor-specific session state variables"""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
        
    if "assistant_id" not in st.session_state:
        st.session_state.assistant_id = None
        
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
        
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = None

def get_or_create_thread():
    """Create a new thread if one doesn't exist"""
    if st.session_state.thread_id is None:
        try:
            thread = st.session_state.rag_manager.client.beta.threads.create()
            st.session_state.thread_id = thread.id
            return thread.id
        except Exception as e:
            st.error(f"Error creating thread: {str(e)}")
            return None
    return st.session_state.thread_id

def is_valid_vector_store(vector_store_id: str) -> bool:
    """
    Check if a vector store is valid and has content
    
    Args:
        vector_store_id: The ID of the vector store to check (string or dict with 'id' field)
        
    Returns:
        Boolean indicating if the vector store is valid and has content
    """
    try:
        # Extract ID if we received a dictionary or JSON string
        actual_id = extract_vector_store_id(vector_store_id)
        if actual_id != vector_store_id:
            print(f"Extracted vector store ID in is_valid_vector_store: {actual_id} (from {type(vector_store_id).__name__})")
        
        # Skip checking if no vector store ID provided
        if not actual_id:
            print("Invalid vector store: No vector store ID provided")
            return False
            
        # Check if the ID format looks valid
        if not isinstance(actual_id, str):
            print(f"Invalid vector store ID type: {type(actual_id).__name__}, expected string")
            return False
            
        if not actual_id.startswith("vs_"):
            print(f"Warning: Vector store ID doesn't follow expected format: {actual_id}")
            # Continue anyway as this is just a warning
            
        # Ensure rag_manager is initialized
        if not hasattr(st.session_state, 'rag_manager') or st.session_state.rag_manager is None:
            # Initialize RAG manager if needed
            user_email = st.session_state.get('email')
            if user_email:
                init_success = init_rag_manager(user_email)
                if not init_success:
                    print("Unable to initialize RAG manager")
                    return False
            else:
                print("No user email found in session state")
                return False
            
        # Try to list files in the vector store
        print(f"Checking vector store files for ID: {actual_id}")
        files = st.session_state.rag_manager.list_vector_store_files(actual_id)
        
        # Vector store is valid if it has at least one file
        is_valid = len(files) > 0
        print(f"Vector store {actual_id} is valid: {is_valid} (contains {len(files)} files)")
        return is_valid
        
    except Exception as e:
        print(f"Error checking vector store {vector_store_id}: {str(e)}")
        # Try to give more specific error messages
        error_str = str(e).lower()
        if "not found" in error_str:
            print("The vector store ID appears to be invalid or the store has been deleted")
        elif "unauthorized" in error_str:
            print("API authorization error. Check your API key and permissions")
        elif "timeout" in error_str or "connection" in error_str:
            print("Network error when checking vector store. Check your connection")
        return False

def create_assistant_for_chat(vector_store_id: str):
    """Create or get an assistant that can access the selected course materials"""
    try:
        # Ensure rag_manager is initialized
        if not hasattr(st.session_state, 'rag_manager') or st.session_state.rag_manager is None:
            # Initialize RAG manager if needed
            user_email = st.session_state.get('email')
            if user_email:
                init_success = init_rag_manager(user_email)
                if not init_success:
                    st.error("RAG Manager could not be initialized. Please refresh the page.")
                    return None
            else:
                st.error("User email not found. Please refresh the page.")
                return None
        
        # Extract ID if we received a dictionary or JSON string
        actual_id = extract_vector_store_id(vector_store_id)
        if actual_id != vector_store_id:
            print(f"Extracted vector store ID in create_assistant_for_chat: {actual_id} (from {type(vector_store_id).__name__})")
        
        # Verify the vector store ID
        if not actual_id:
            st.error("No vector store ID provided for assistant creation.")
            return None
            
        # Check if the vector store is valid and has content
        if not is_valid_vector_store(actual_id):
            st.error("The vector store appears to be empty or invalid. Please make sure course materials have been properly uploaded.")
            return None
            
        # Create a new assistant focused on explaining concepts
        assistant = st.session_state.rag_manager.client.beta.assistants.create(
            name="Course Assistant",
            instructions="""You are a helpful teaching assistant for university students.
Your goal is to help students understand concepts from their course materials.
Always provide thorough, accurate explanations based on the content you have access to.
If you're not sure about something, be clear about that rather than making up information.
Use examples and analogies when helpful to explain complex topics.""",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={"file_search": {"vector_store_ids": [actual_id]}}
        )
        
        st.session_state.assistant_id = assistant.id
        return assistant.id
    except Exception as e:
        # Log the detailed error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating assistant: {str(e)}\n{error_details}")
        st.error(f"Error creating assistant: {str(e)}")
        return None

def send_message(
    message: str, 
    vector_store_id: str, 
    subject: str, 
    week: str, 
    stream_handler: Optional[Callable[[str], None]] = None, 
    stream: bool = True
):
    """
    Send a message to the AI tutor
    
    Args:
        message: The user's message
        vector_store_id: The vector store ID to use (string or dict with 'id' field)
        subject: The subject name
        week: The week number
        stream_handler: Optional callback for streaming responses
        stream: Whether to stream the response
        
    Returns:
        The assistant's response
    """
    # Extract ID if we received a dictionary or JSON string
    actual_id = extract_vector_store_id(vector_store_id)
    if actual_id != vector_store_id:
        print(f"Extracted vector store ID in send_message: {actual_id} (from {type(vector_store_id).__name__})")
    
    # Ensure rag_manager is initialized
    if not hasattr(st.session_state, 'rag_manager') or st.session_state.rag_manager is None:
        # Initialize RAG manager if needed
        user_email = st.session_state.get('email')
        if user_email:
            init_success = init_rag_manager(user_email)
            if not init_success:
                return "Error: Unable to initialize RAG Manager. Please refresh the page and try again."
        else:
            return "Error: User not recognized. Please refresh the page and try again."
            
    try:
        # Make sure we have a thread
        thread_id = get_or_create_thread()
        
        if not thread_id:
            return "Error: Could not create or retrieve thread. Please refresh the page and try again."
        
        # Make sure we have an assistant
        if st.session_state.assistant_id is None:
            # Attempt to create the assistant
            assistant_id = create_assistant_for_chat(actual_id)
            if not assistant_id:
                # More detailed error to help diagnose the issue
                st.error("Failed to create AI assistant. This could be due to API limits, network issues, or problems with the vector store.")
                return "I'm having trouble connecting to the AI service. Please try again in a few moments, or refresh the page."
        else:
            assistant_id = st.session_state.assistant_id
        
        # Add the user message to the thread
        st.session_state.rag_manager.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        
        # Create a run
        run = st.session_state.rag_manager.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            stream=stream
        )
        
        response_text = ""
        
        # Handle streaming if requested
        if stream and stream_handler:
            # Process the stream
            for chunk in run:
                if chunk.event == "thread.message.delta" and hasattr(chunk, "data") and hasattr(chunk.data, "delta") and hasattr(chunk.data.delta, "content"):
                    for content in chunk.data.delta.content:
                        if content.type == "text" and hasattr(content.text, "value"):
                            delta_text = content.text.value
                            response_text += delta_text
                            stream_handler(delta_text)
        else:
            # Wait for the run to complete without streaming
            while run.status in ["queued", "in_progress"]:
                time.sleep(1)
                run = st.session_state.rag_manager.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            
            # Get the latest messages (should include the assistant's response)
            messages = st.session_state.rag_manager.client.beta.threads.messages.list(
                thread_id=thread_id
            )
            
            # Find the assistant's response (the most recent assistant message)
            response_text = "No response from the assistant."
            for message in messages.data:
                if message.role == "assistant":
                    # Extract and return the text content
                    response_text = ""
                    for content in message.content:
                        if content.type == "text":
                            response_text += content.text.value
                    break
        
        # Save the conversation to MongoDB if we have a user email
        if "email" in st.session_state and st.session_state.email:
            # Get or create chat title
            chat_title = None
            if "chat_title" in st.session_state and st.session_state.chat_title:
                chat_title = st.session_state.chat_title
            
            # Save conversation to MongoDB
            mongodb.save_chat_session(
                email=st.session_state.email,
                subject=subject,
                week=week,
                vector_store_id=actual_id,  # Use the extracted ID
                messages=st.session_state.chat_messages + [{"role": "assistant", "content": response_text}],
                thread_id=thread_id,
                assistant_id=assistant_id,
                chat_type=mongodb.CHAT_TYPE_TUTOR,
                title=chat_title
            )
        
        return response_text
    
    except Exception as e:
        return f"Error: {str(e)}"

def reset_chat():
    """Reset the chat state"""
    st.session_state.chat_messages = []
    st.session_state.thread_id = None
    st.session_state.assistant_id = None
    st.session_state.chat_title = None

def get_vector_store_for_subject_week(subject: str, week: str):
    """
    Get the vector store ID for a given subject and week
    
    Returns:
        String vector store ID if found, otherwise None
    """
    # Debug info
    print(f"Looking for vector store for {subject} - Week {week}")
    
    # Look for the vector store ID in the data
    if (subject in st.session_state.data and 
        "vector_store_metadata" in st.session_state.data[subject] and
        week in st.session_state.data[subject]["vector_store_metadata"]):
        
        metadata = st.session_state.data[subject]["vector_store_metadata"][week]
        print(f"Found metadata for {subject} - Week {week}: {metadata} (type: {type(metadata).__name__})")
        
        # Handle various formats of metadata
        vector_store_id = None
        
        # Case 1: Dictionary with id field
        if isinstance(metadata, dict) and "id" in metadata:
            vector_store_id = metadata["id"]
            print(f"Case 1: Extracted ID from dictionary: {vector_store_id}")
        
        # Case 2: JSON string in format: "{\"id\":\"vs_xxx\",\"name\":\"Subject_Week\"}"
        elif isinstance(metadata, str) and metadata.startswith("{") and "id" in metadata:
            try:
                import json
                # Try to parse the JSON string
                parsed_metadata = json.loads(metadata)
                if isinstance(parsed_metadata, dict) and "id" in parsed_metadata:
                    vector_store_id = parsed_metadata["id"]
                    print(f"Case 2: Extracted ID from JSON string: {vector_store_id}")
            except Exception as e:
                print(f"Error parsing vector store metadata JSON: {e}")
                # If parsing fails, use the string as is
                vector_store_id = metadata
                print(f"Case 2 fallback: Using original string as ID: {vector_store_id}")
        
        # Case 3: Plain string ID
        else:
            vector_store_id = metadata
            print(f"Case 3: Using metadata as plain string ID: {vector_store_id}")
            
        # Validate the ID length - if it's too long, return None to avoid errors
        if vector_store_id and len(vector_store_id) > 64:
            print(f"WARNING: Found invalid vector store ID (too long): {len(vector_store_id)} chars")
            return None
            
        return vector_store_id
    else:
        if subject not in st.session_state.data:
            print(f"Subject '{subject}' not found in session state data")
        elif "vector_store_metadata" not in st.session_state.data[subject]:
            print(f"No vector_store_metadata for subject '{subject}'")
        elif week not in st.session_state.data[subject]["vector_store_metadata"]:
            print(f"Week '{week}' not found in vector_store_metadata for '{subject}'")
        
    return None

def load_chat_session(session_id: str):
    """Load a saved chat session"""
    # Get the full session data
    full_session = mongodb.get_chat_session(session_id)
    
    if full_session:
        # Set the session state variables to match this conversation
        st.session_state.chat_messages = full_session.get("messages", [])
        st.session_state.thread_id = full_session.get("thread_id")
        st.session_state.assistant_id = full_session.get("assistant_id")
        st.session_state.current_chat_id = session_id
        
        # Set the custom title if available
        if 'title' in full_session:
            st.session_state.chat_title = full_session.get("title")
        
        # Return the subject and week for context
        return full_session.get("subject"), full_session.get("week")
    
    return None, None 
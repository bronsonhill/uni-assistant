"""
MongoDB data access layer for chat history.
Provides functions to manage chat history in MongoDB.
"""
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson.objectid import ObjectId

from .connection import get_collection

# Collection name for chat history
CHAT_HISTORY_COLLECTION = "chat_history"

# Chat type constants
CHAT_TYPE_TUTOR = "tutor"
CHAT_TYPE_PRACTICE = "practice"

def save_chat_session(
    email: str,
    subject: str,
    week: str,
    vector_store_id: str,
    messages: List[Dict[str, str]],
    thread_id: Optional[str] = None,
    assistant_id: Optional[str] = None,
    chat_type: str = CHAT_TYPE_TUTOR,
    title: Optional[str] = None
) -> str:
    """
    Save a chat session to MongoDB.
    
    Args:
        email: User's email address
        subject: Subject of the chat
        week: Week number
        vector_store_id: ID of the vector store used
        messages: List of chat messages
        thread_id: Optional OpenAI thread ID
        assistant_id: Optional OpenAI assistant ID
        chat_type: Type of chat (tutor, practice)
        title: Optional custom title for the chat
    
    Returns:
        The ID of the inserted or updated chat session
    """
    collection = get_collection(CHAT_HISTORY_COLLECTION)
    
    # Get the current time
    current_time = int(time.time())
    
    # Check if there's an existing session with the same thread_id if provided
    existing_session = None
    if thread_id:
        existing_session = collection.find_one({
            "email": email,
            "thread_id": thread_id,
            "chat_type": chat_type  # Include chat_type to prevent conflicts between features
        })
    
    if existing_session:
        # Update the existing session
        session_id = existing_session["_id"]
        update_data = {
            "subject": subject,
            "week": week,
            "vector_store_id": vector_store_id,
            "messages": messages,
            "assistant_id": assistant_id,
            "updated_at": current_time,
            "last_message": messages[-1]["content"] if messages else ""
        }
        
        # Add custom title if provided, otherwise keep existing
        if title is not None:
            update_data["title"] = title
            
        collection.update_one(
            {"_id": session_id},
            {"$set": update_data}
        )
        return str(session_id)
    else:
        # Create a new chat session
        chat_session = {
            "email": email,
            "subject": subject,
            "week": week,
            "vector_store_id": vector_store_id,
            "messages": messages,
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "created_at": current_time,
            "updated_at": current_time,
            "last_message": messages[-1]["content"] if messages else "",
            "chat_type": chat_type
        }
        
        # Add title if provided, otherwise use default from subject/week
        if title is not None:
            chat_session["title"] = title
        else:
            chat_session["title"] = f"{subject} - Week {week}"
        
        result = collection.insert_one(chat_session)
        return str(result.inserted_id)

def get_chat_sessions(email: str, chat_type: str = None) -> List[Dict]:
    """
    Get all chat sessions for a user.
    
    Args:
        email: User's email address
        chat_type: Optional filter for chat type (tutor, practice)
    
    Returns:
        List of chat sessions
    """
    collection = get_collection(CHAT_HISTORY_COLLECTION)
    
    # Create query based on email and optional chat_type
    query = {"email": email}
    if chat_type:
        query["chat_type"] = chat_type
    
    # Query all chat sessions for the user, sorted by updated_at (most recent first)
    chat_sessions = collection.find(
        query,
        projection={
            "subject": 1,
            "week": 1,
            "title": 1,
            "created_at": 1,
            "updated_at": 1,
            "last_message": 1,
            "_id": 1,
            "chat_type": 1
        }
    ).sort("updated_at", -1)
    
    # Convert ObjectId to string
    result = []
    for session in chat_sessions:
        if "_id" in session:
            session["_id"] = str(session["_id"])
        
        # Convert timestamps to readable format
        if "created_at" in session:
            session["created_at_readable"] = datetime.fromtimestamp(
                session["created_at"]
            ).strftime("%Y-%m-%d %H:%M")
        
        if "updated_at" in session:
            session["updated_at_readable"] = datetime.fromtimestamp(
                session["updated_at"]
            ).strftime("%Y-%m-%d %H:%M")
        
        result.append(session)
    
    return result

def get_chat_session(session_id: str) -> Optional[Dict]:
    """
    Get a specific chat session.
    
    Args:
        session_id: The ID of the chat session
    
    Returns:
        Chat session data or None if not found
    """
    collection = get_collection(CHAT_HISTORY_COLLECTION)
    
    try:
        chat_session = collection.find_one({"_id": ObjectId(session_id)})
        
        if chat_session:
            # Convert ObjectId to string
            chat_session["_id"] = str(chat_session["_id"])
            
            # Convert timestamps to readable format
            if "created_at" in chat_session:
                chat_session["created_at_readable"] = datetime.fromtimestamp(
                    chat_session["created_at"]
                ).strftime("%Y-%m-%d %H:%M")
            
            if "updated_at" in chat_session:
                chat_session["updated_at_readable"] = datetime.fromtimestamp(
                    chat_session["updated_at"]
                ).strftime("%Y-%m-%d %H:%M")
            
            return chat_session
    except Exception as e:
        print(f"Error retrieving chat session: {e}")
    
    return None

def rename_chat_session(session_id: str, email: str, new_title: str) -> bool:
    """
    Rename a chat session by updating its title.
    Email is required for security to ensure only the owner can rename.
    
    Args:
        session_id: The ID of the chat session
        email: User's email address
        new_title: New title for the chat session
        
    Returns:
        True if session was renamed, False if not found or not owned by user
    """
    collection = get_collection(CHAT_HISTORY_COLLECTION)
    
    try:
        result = collection.update_one(
            {
                "_id": ObjectId(session_id),
                "email": email  # Ensure only the owner can rename
            },
            {
                "$set": {
                    "title": new_title,
                    "updated_at": int(time.time())
                }
            }
        )
        
        return result.modified_count > 0
    except Exception as e:
        print(f"Error renaming chat session: {e}")
        return False

def delete_chat_session(session_id: str, email: str) -> bool:
    """
    Delete a chat session.
    Email is required for security to ensure only the owner can delete.
    
    Args:
        session_id: The ID of the chat session
        email: User's email address
    
    Returns:
        True if session was deleted, False if not found or not owned by user
    """
    collection = get_collection(CHAT_HISTORY_COLLECTION)
    
    try:
        result = collection.delete_one({
            "_id": ObjectId(session_id),
            "email": email  # Ensure only the owner can delete
        })
        
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting chat session: {e}")
        return False
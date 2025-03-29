"""
MongoDB data access layer for users.
Provides functions to manage user data in MongoDB.
"""
import json
import time
from typing import Dict, List, Optional, Any

from .connection import get_collection
from pymongo.collection import Collection

# Collection name for users
USERS_COLLECTION = "users"

DEFAULT_DECAY_FACTOR = 0.1
DEFAULT_FORGETTING_DECAY_FACTOR = 0.05

def load_users() -> Dict:
    """
    Load users data from MongoDB.
    
    Returns:
        Dict: Users data with email as key and user information as value
    """
    collection = get_collection(USERS_COLLECTION)
    
    # Query all users
    users = collection.find({})
    
    # Build the user dictionary with email as key
    users_data = {}
    
    for user in users:
        email = user.pop("email", None)
        if email:
            # Remove MongoDB's _id from the document
            if "_id" in user:
                del user["_id"]
            
            users_data[email] = user
    
    return users_data


def save_users(users_data: Dict) -> None:
    """
    Save users data to MongoDB.
    
    Args:
        users_data (Dict): Users data with email as key and user information as value
    """
    collection = get_collection(USERS_COLLECTION)
    
    # Clear existing data
    collection.delete_many({})
    
    # Add each user as a document
    for email, user_info in users_data.items():
        # Create user document with email field
        user_doc = {"email": email}
        user_doc.update(user_info)
        
        # Add updated_at timestamp
        user_doc["updated_at"] = int(time.time())
        
        # Insert the document
        collection.insert_one(user_doc)


def get_user(email: str) -> Optional[Dict]:
    """
    Get a specific user by email.
    
    Args:
        email: User's email address
    
    Returns:
        User data or None if not found
    """
    collection = get_collection(USERS_COLLECTION)
    
    user = collection.find_one({"email": email})
    
    if user:
        # Remove MongoDB's _id from the document
        if "_id" in user:
            del user["_id"]
        
        return user
    
    return None


def add_user(email: str, user_data: Dict) -> None:
    """
    Add or update a user.
    
    Args:
        email: User's email address
        user_data: User data to store
    """
    collection = get_collection(USERS_COLLECTION)
    
    # Create user document
    user_doc = {"email": email}
    user_doc.update(user_data)
    
    # Add updated_at timestamp
    user_doc["updated_at"] = int(time.time())
    
    # Use upsert to insert if not exists or update if exists
    collection.update_one(
        {"email": email},
        {"$set": user_doc},
        upsert=True
    )


def delete_user(email: str) -> bool:
    """
    Delete a user.
    
    Args:
        email: User's email address
    
    Returns:
        True if user was deleted, False if not found
    """
    collection = get_collection(USERS_COLLECTION)
    
    result = collection.delete_one({"email": email})
    
    return result.deleted_count > 0


def update_user_field(email: str, field: str, value: Any) -> bool:
    """
    Update a specific field for a user.
    
    Args:
        email: User's email address
        field: Field to update
        value: New value for the field
    
    Returns:
        True if updated, False if user not found
    """
    collection = get_collection(USERS_COLLECTION)
    
    result = collection.update_one(
        {"email": email},
        {
            "$set": {
                field: value,
                "updated_at": int(time.time())
            }
        }
    )
    
    return result.matched_count > 0


def get_user_score_settings(email: str) -> Dict[str, float]:
    """
    Retrieve score calculation settings for a user.
    Returns default settings if none are found.
    """
    collection = get_collection("users")
    user = collection.find_one({"email": email})
    
    if user and "score_settings" in user and isinstance(user["score_settings"], dict):
        settings = user["score_settings"]
        # Ensure both keys exist, fall back to default if one is missing
        return {
            "decay_factor": settings.get("decay_factor", DEFAULT_DECAY_FACTOR),
            "forgetting_decay_factor": settings.get("forgetting_decay_factor", DEFAULT_FORGETTING_DECAY_FACTOR)
        }
    else:
        # Return defaults if user or settings don't exist
        return {
            "decay_factor": DEFAULT_DECAY_FACTOR,
            "forgetting_decay_factor": DEFAULT_FORGETTING_DECAY_FACTOR
        }


def update_user_score_settings(email: str, settings: Dict[str, float]) -> bool:
    """
    Update score calculation settings for a user.
    """
    collection = get_collection("users")
    result = collection.update_one(
        {"email": email},
        {"$set": {"score_settings": settings}},
        upsert=False # Don't create user if not found, should exist already
    )
    
    if result.matched_count == 0:
        print(f"Warning: Attempted to update score settings for non-existent user: {email}")
        return False
        
    return result.modified_count > 0 or result.matched_count > 0 # Return True if updated or already matched
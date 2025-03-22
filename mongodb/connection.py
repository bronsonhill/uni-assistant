"""
MongoDB connection and utility functions.
Provides a consistent interface for connecting to MongoDB.
"""
import os
import streamlit as st
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from typing import Optional

# Get the connection string from Streamlit secrets
def get_connection_string() -> str:
    """Get the MongoDB connection string from environment or secrets."""
    # First try to get from environment variable
    conn_str = os.environ.get("MONGODB_CONNECTION_STRING")
    
    # If not in environment, try to get from Streamlit secrets
    if not conn_str and hasattr(st, "secrets") and "db_connection_string" in st.secrets:
        conn_str = st.secrets["db_connection_string"]
        
    if not conn_str:
        raise ValueError(
            "MongoDB connection string not found. "
            "Set the MONGODB_CONNECTION_STRING environment variable "
            "or add db_connection_string to .streamlit/secrets.toml"
        )
    
    return conn_str

@st.cache_resource
def get_mongodb_client() -> MongoClient:
    """
    Get a MongoDB client instance.
    Uses Streamlit's cache_resource decorator to reuse the connection.
    """
    connection_string = get_connection_string()
    return MongoClient(connection_string)

def get_database(db_name: str = "study_legend") -> Database:
    """Get a MongoDB database instance."""
    client = get_mongodb_client()
    return client[db_name]

def get_collection(collection_name: str, db_name: str = "study_legend") -> Collection:
    """Get a MongoDB collection instance."""
    db = get_database(db_name)
    return db[collection_name]

def create_indexes():
    """
    Create indexes for MongoDB collections to optimize query performance.
    This function should be called once during application initialization.
    """
    # Get database and collections
    db = get_database()
    queue_cards = db["queue_cards"]
    users = db["users"]
    assessments = db["assessments"]
    chat_history = db["chat_sessions"]
    
    # Create index for queue_cards collection
    queue_cards.create_index("user_email")
    
    # Create index for users collection
    users.create_index("email", unique=True)
    
    # Create index for assessments collection
    assessments.create_index("user_email")
    
    # Create index for chat_history collection
    chat_history.create_index("user_email")
    chat_history.create_index("timestamp")
    
    print("MongoDB indexes created successfully.")
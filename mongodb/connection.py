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
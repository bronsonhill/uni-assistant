"""
MongoDB Integration Package

This package provides integration with MongoDB for the university assistant app.
It handles all database operations including connection, data storage, and retrieval.

The package includes the following modules:
- connection: Handles connection to the MongoDB database
- queue_cards: Manages storage and retrieval of queue cards data
- users: Manages user data operations
- assessments: Manages assessment data
- chat_history: Manages chat history data

Usage:
    from mongodb import get_mongodb_client, save_data, load_data
"""

# Re-export connection functions
from mongodb.connection import (
    get_mongodb_client,
    get_database,
    get_collection
)

# Re-export queue_cards functions
from mongodb.queue_cards import (
    save_data,
    load_data,
    add_question,
    update_question,
    delete_question,
    update_question_score,
    calculate_weighted_score,
    add_file_metadata,
    get_file_metadata
)

# Import migration function from init_db
from mongodb.init_db import migrate_json_to_mongodb

# Re-export users functions
from mongodb.users import (
    get_user,
    add_user,
    delete_user,
    update_user_field,
    load_users,
    save_users
)

# Re-export assessments functions
from mongodb.assessments import (
    load_assessments,
    save_assessments,
    get_user_assessments,
    add_assessment,
    update_assessment,
    delete_assessment
)

# Re-export chat_history functions
from mongodb.chat_history import (
    save_chat_session,
    get_chat_sessions,
    get_chat_session,
    rename_chat_session,
    delete_chat_session
)

# All exported functions and constants
__all__ = [
    # Connection functions
    'get_mongodb_client',
    'get_database',
    'get_collection',
    
    # Queue cards functions
    'save_data',
    'load_data',
    'add_question',
    'update_question',
    'delete_question',
    'update_question_score',
    'calculate_weighted_score',
    'add_file_metadata',
    'get_file_metadata',
    'migrate_json_to_mongodb',
    
    # Users functions
    'get_user',
    'add_user',
    'delete_user',
    'update_user_field',
    'load_users',
    'save_users',
    
    # Assessment functions
    'load_assessments',
    'save_assessments',
    'get_user_assessments',
    'add_assessment',
    'update_assessment',
    'delete_assessment',
    
    # Chat history functions
    'save_chat_session',
    'get_chat_sessions',
    'get_chat_session',
    'rename_chat_session',
    'delete_chat_session'
]
"""
MongoDB connection and utility functions.
Provides a consistent interface for connecting to MongoDB.
"""
from .connection_manager import (
    MongoDBConnectionManager,
    handle_mongodb_operation,
    MongoDBTransaction,
    MongoDBError,
    ConnectionError,
    QueryError,
    TransactionError
)

# Create a singleton instance of the connection manager
_manager = MongoDBConnectionManager()

@handle_mongodb_operation
def get_mongodb_client():
    """
    Get a MongoDB client instance.
    Uses Streamlit's cache_resource decorator to reuse the connection.
    """
    return _manager.get_client()

@handle_mongodb_operation
def get_database(db_name: str = "study_legend"):
    """Get a MongoDB database instance."""
    return _manager.get_database(db_name)

@handle_mongodb_operation
def get_collection(collection_name: str, db_name: str = "study_legend"):
    """Get a MongoDB collection instance."""
    return _manager.get_collection(collection_name, db_name)

def create_indexes():
    """
    Create indexes for MongoDB collections to optimize query performance.
    This function should be called once during application initialization.
    """
    try:
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
    except Exception as e:
        print(f"Error creating MongoDB indexes: {str(e)}")
        raise

def close_connection():
    """Close the MongoDB connection."""
    _manager.close()

# Export all necessary components
__all__ = [
    'get_mongodb_client',
    'get_database',
    'get_collection',
    'create_indexes',
    'close_connection',
    'MongoDBTransaction',
    'MongoDBError',
    'ConnectionError',
    'QueryError',
    'TransactionError'
]
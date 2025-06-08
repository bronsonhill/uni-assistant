"""
MongoDB Connection Manager

Provides a robust connection management system for MongoDB with connection pooling,
transaction support, and comprehensive error handling.
"""
import os
import time
import logging
from typing import Optional, Any
from functools import wraps
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
from pymongo.database import Database
from pymongo.collection import Collection
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

class MongoDBError(Exception):
    """Base exception for MongoDB-related errors."""
    pass

class ConnectionError(MongoDBError):
    """Raised when there are issues connecting to MongoDB."""
    pass

class QueryError(MongoDBError):
    """Raised when there are issues executing queries."""
    pass

class TransactionError(MongoDBError):
    """Raised when there are issues with transactions."""
    pass

class MongoDBConnectionManager:
    """Singleton class to manage MongoDB connections with connection pooling."""
    
    _instance = None
    _client = None
    _database = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._max_pool_size = int(os.getenv("MONGODB_MAX_POOL_SIZE", "100"))
            self._server_selection_timeout = int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT", "5000"))
            self._connect_timeout = int(os.getenv("MONGODB_CONNECT_TIMEOUT", "2000"))
            self._retry_attempts = int(os.getenv("MONGODB_RETRY_ATTEMPTS", "3"))
            self._retry_delay = int(os.getenv("MONGODB_RETRY_DELAY", "1000"))
    
    def get_connection_string(self) -> str:
        """Get the MongoDB connection string from environment or secrets."""
        # First try to get from environment variable
        conn_str = os.environ.get("MONGODB_CONNECTION_STRING")
        
        # If not in environment, try to get from Streamlit secrets
        if not conn_str and hasattr(st, "secrets") and "db_connection_string" in st.secrets:
            conn_str = st.secrets["db_connection_string"]
            
        if not conn_str:
            raise ConnectionError(
                "MongoDB connection string not found. "
                "Set the MONGODB_CONNECTION_STRING environment variable "
                "or add db_connection_string to .streamlit/secrets.toml"
            )
        
        return conn_str
    
    @st.cache_resource
    def get_client(_self) -> MongoClient:
        """Get a MongoDB client instance with connection pooling."""
        if _self._client is None:
            try:
                connection_string = _self.get_connection_string()
                _self._client = MongoClient(
                    connection_string,
                    maxPoolSize=_self._max_pool_size,
                    serverSelectionTimeoutMS=_self._server_selection_timeout,
                    connectTimeoutMS=_self._connect_timeout
                )
                # Test the connection
                _self._client.admin.command('ping')
                logger.info("Successfully connected to MongoDB")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"Failed to connect to MongoDB: {str(e)}")
                raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
        return _self._client
    
    def get_database(self, db_name: str = "study_legend") -> Database:
        """Get a MongoDB database instance."""
        if self._database is None:
            try:
                client = self.get_client()
                self._database = client[db_name]
            except Exception as e:
                logger.error(f"Failed to get database {db_name}: {str(e)}")
                raise ConnectionError(f"Failed to get database {db_name}: {str(e)}")
        return self._database
    
    def get_collection(self, collection_name: str, db_name: str = "study_legend") -> Collection:
        """Get a MongoDB collection instance."""
        try:
            db = self.get_database(db_name)
            return db[collection_name]
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}: {str(e)}")
            raise ConnectionError(f"Failed to get collection {collection_name}: {str(e)}")
    
    def close(self) -> None:
        """Close the MongoDB connection."""
        if self._client:
            try:
                self._client.close()
                self._client = None
                self._database = None
                logger.info("MongoDB connection closed")
            except Exception as e:
                logger.error(f"Error closing MongoDB connection: {str(e)}")
                raise ConnectionError(f"Error closing MongoDB connection: {str(e)}")

def handle_mongodb_operation(func):
    """Decorator to handle MongoDB operations with retries and error handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        manager = MongoDBConnectionManager()
        last_error = None
        
        for attempt in range(manager._retry_attempts):
            try:
                return func(*args, **kwargs)
            except ConnectionFailure as e:
                last_error = e
                logger.warning(f"Connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < manager._retry_attempts - 1:
                    time.sleep(manager._retry_delay / 1000)  # Convert to seconds
            except OperationFailure as e:
                logger.error(f"Operation failed: {str(e)}")
                raise QueryError(f"Operation failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                raise MongoDBError(f"Unexpected error: {str(e)}")
        
        raise ConnectionError(f"Failed after {manager._retry_attempts} attempts: {str(last_error)}")
    
    return wrapper

class MongoDBTransaction:
    """Context manager for MongoDB transactions."""
    
    def __init__(self, database: Database):
        self.database = database
        self.session = None
    
    def __enter__(self):
        try:
            self.session = self.database.client.start_session()
            self.session.start_transaction()
            return self.session
        except Exception as e:
            logger.error(f"Failed to start transaction: {str(e)}")
            raise TransactionError(f"Failed to start transaction: {str(e)}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type is None:
                    self.session.commit_transaction()
                else:
                    self.session.abort_transaction()
            except Exception as e:
                logger.error(f"Error in transaction: {str(e)}")
                raise TransactionError(f"Error in transaction: {str(e)}")
            finally:
                self.session.end_session() 
"""
Tests for MongoDB integration.
"""
import unittest
import os
import time
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure, OperationFailure
from mongodb.connection_manager import (
    MongoDBConnectionManager,
    MongoDBError,
    ConnectionError,
    QueryError,
    TransactionError,
    handle_mongodb_operation
)

class TestMongoDBConnectionManager(unittest.TestCase):
    """Test cases for MongoDBConnectionManager."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'MONGODB_CONNECTION_STRING': 'mongodb://localhost:27017/test',
            'MONGODB_MAX_POOL_SIZE': '50',
            'MONGODB_SERVER_SELECTION_TIMEOUT': '2000',
            'MONGODB_CONNECT_TIMEOUT': '1000',
            'MONGODB_RETRY_ATTEMPTS': '2',
            'MONGODB_RETRY_DELAY': '500'
        })
        self.env_patcher.start()
        
        # Create a new instance for each test
        self.manager = MongoDBConnectionManager()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
        if hasattr(self.manager, '_client') and self.manager._client:
            self.manager.close()
    
    @patch('pymongo.MongoClient')
    def test_get_client_success(self, mock_client):
        """Test successful client creation."""
        # Mock successful connection
        mock_instance = MagicMock()
        mock_instance.admin.command.return_value = True
        mock_client.return_value = mock_instance
        
        client = self.manager.get_client()
        
        self.assertIsNotNone(client)
        mock_client.assert_called_once()
    
    @patch('pymongo.MongoClient')
    def test_get_client_connection_failure(self, mock_client):
        """Test client creation with connection failure."""
        # Mock connection failure
        mock_client.side_effect = ConnectionFailure("Connection failed")
        
        with self.assertRaises(ConnectionError):
            self.manager.get_client()
    
    @patch('pymongo.MongoClient')
    def test_get_database(self, mock_client):
        """Test getting database instance."""
        # Mock successful connection
        mock_instance = MagicMock()
        mock_instance.admin.command.return_value = True
        mock_client.return_value = mock_instance
        
        db = self.manager.get_database("test_db")
        
        self.assertIsNotNone(db)
        self.assertEqual(db.name, "test_db")
    
    @patch('pymongo.MongoClient')
    def test_get_collection(self, mock_client):
        """Test getting collection instance."""
        # Mock successful connection
        mock_instance = MagicMock()
        mock_instance.admin.command.return_value = True
        mock_client.return_value = mock_instance
        
        collection = self.manager.get_collection("test_collection", "test_db")
        
        self.assertIsNotNone(collection)
        self.assertEqual(collection.name, "test_collection")
    
    def test_close_connection(self):
        """Test closing connection."""
        # Mock client
        mock_client = MagicMock()
        self.manager._client = mock_client
        
        self.manager.close()
        
        mock_client.close.assert_called_once()
        self.assertIsNone(self.manager._client)
        self.assertIsNone(self.manager._database)

class TestMongoDBTransaction(unittest.TestCase):
    """Test cases for MongoDBTransaction."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_database = MagicMock()
        self.mock_session = MagicMock()
        self.mock_database.client.start_session.return_value = self.mock_session
    
    def test_transaction_success(self):
        """Test successful transaction."""
        with MongoDBTransaction(self.mock_database) as session:
            self.assertEqual(session, self.mock_session)
        
        self.mock_session.start_transaction.assert_called_once()
        self.mock_session.commit_transaction.assert_called_once()
        self.mock_session.end_session.assert_called_once()
    
    def test_transaction_failure(self):
        """Test failed transaction."""
        with self.assertRaises(Exception):
            with MongoDBTransaction(self.mock_database) as session:
                raise Exception("Test error")
        
        self.mock_session.start_transaction.assert_called_once()
        self.mock_session.abort_transaction.assert_called_once()
        self.mock_session.end_session.assert_called_once()

class TestMongoDBOperationDecorator(unittest.TestCase):
    """Test cases for handle_mongodb_operation decorator."""
    
    def setUp(self):
        """Set up test environment."""
        self.manager = MongoDBConnectionManager()
    
    @handle_mongodb_operation
    def test_operation(self):
        """Test successful operation."""
        return "success"
    
    @handle_mongodb_operation
    def test_operation_failure(self):
        """Test operation that fails."""
        raise ConnectionFailure("Connection failed")
    
    def test_successful_operation(self):
        """Test successful operation with decorator."""
        result = self.test_operation()
        self.assertEqual(result, "success")
    
    def test_failed_operation(self):
        """Test failed operation with decorator."""
        with self.assertRaises(ConnectionError):
            self.test_operation_failure()

if __name__ == '__main__':
    unittest.main() 
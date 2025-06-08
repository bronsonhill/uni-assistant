from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseRepository(ABC):
    """Base repository interface defining common database operations"""
    
    def __init__(self, collection_name: str):
        """Initialize the repository with a collection name.
        
        Args:
            collection_name (str): Name of the collection/database table
        """
        self.collection_name = collection_name
        self._validate_collection_name()
    
    def _validate_collection_name(self) -> None:
        """Validate the collection name.
        
        Raises:
            ValueError: If collection name is invalid
        """
        if not self.collection_name or not isinstance(self.collection_name, str):
            raise ValueError("Collection name must be a non-empty string")
    
    def _validate_id(self, id: str) -> bool:
        """Validate document ID format"""
        if not id or not isinstance(id, str):
            raise ValueError("Invalid ID format")
        return True
    
    def _validate_data(self, data: Dict) -> bool:
        """Validate document data format"""
        if not data or not isinstance(data, dict):
            raise ValueError("Invalid data format")
        return True
    
    def _add_timestamps(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add created_at and updated_at timestamps to data.
        
        Args:
            data (Dict[str, Any]): Data to add timestamps to
            
        Returns:
            Dict[str, Any]: Data with timestamps
        """
        now = datetime.utcnow()
        if '_id' not in data:
            data['created_at'] = now
        data['updated_at'] = now
        return data
    
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[Dict]:
        """Find a document by its ID"""
        pass
    
    @abstractmethod
    def find_all(self, filters: Dict = None) -> List[Dict]:
        """Find all documents matching optional filters"""
        pass
    
    @abstractmethod
    def create(self, data: Dict) -> str:
        """Create a new document and return its ID"""
        pass
    
    @abstractmethod
    def update(self, id: str, data: Dict) -> bool:
        """Update a document by ID"""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """Delete a document by ID"""
        pass
    
    @abstractmethod
    def exists(self, id: str) -> bool:
        """Check if a document exists.
        
        Args:
            id (str): Document ID
            
        Returns:
            bool: True if document exists
        """
        pass 
from typing import Dict, List, Optional, Any, Union
import logging
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib
from io import BytesIO

from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreServiceError(Exception):
    """Custom exception for Vector Store Service errors"""
    pass

@dataclass
class VectorStore:
    """Data class for vector store information"""
    id: str
    name: str
    created_at: datetime
    file_count: int
    metadata: Dict[str, Any]

class VectorStoreService:
    def __init__(self, client: OpenAI):
        """Initialize the Vector Store Service with OpenAI client"""
        self.client = client
        self._vector_stores: Dict[str, Dict] = {}  # Cache for vector store IDs
        logger.info("Vector Store Service initialized successfully")

    def _generate_store_key(self, subject: str, week: str, email: Optional[str] = None) -> str:
        """Generate a unique key for the vector store"""
        key_parts = [subject, week]
        if email:
            key_parts.append(email)
        return "_".join(key_parts)

    def get_vector_store_id(self, subject: str, week: str, email: Optional[str] = None) -> Optional[str]:
        """
        Get vector store ID for subject and week
        
        Args:
            subject: Subject name
            week: Week number
            email: Optional user email
            
        Returns:
            Vector store ID if found, None otherwise
        """
        store_key = self._generate_store_key(subject, week, email)
        return self._vector_stores.get(store_key, {}).get("id")

    def create_vector_store(self, subject: str, week: str, email: Optional[str] = None) -> Dict:
        """
        Create a new vector store or get existing one
        
        Args:
            subject: Subject name
            week: Week number
            email: Optional user email
            
        Returns:
            Dictionary with vector store information
            
        Raises:
            VectorStoreServiceError: If vector store creation fails
        """
        try:
            store_key = self._generate_store_key(subject, week, email)
            
            # Check if vector store already exists
            if store_key in self._vector_stores:
                return self._vector_stores[store_key]
            
            # Create new vector store
            name = f"{subject}_week{week}"
            if email:
                name = f"{name}_{email}"
                
            response = self.client.vector_stores.create(
                name=name,
                metadata={
                    "subject": subject,
                    "week": week,
                    "email": email,
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            # Cache the vector store information
            store_info = {
                "id": response.id,
                "name": response.name,
                "created_at": response.created_at,
                "file_count": 0,
                "metadata": response.metadata
            }
            self._vector_stores[store_key] = store_info
            
            logger.info(f"Created new vector store: {name}")
            return store_info
            
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise VectorStoreServiceError(f"Failed to create vector store: {e}")

    def add_file_to_vector_store(self,
                               vector_store_id: str,
                               file_bytes: bytes,
                               file_name: str) -> Dict:
        """
        Add a file to the vector store
        
        Args:
            vector_store_id: ID of the vector store
            file_bytes: File contents as bytes
            file_name: Original file name
            
        Returns:
            Dictionary with file batch information
            
        Raises:
            VectorStoreServiceError: If file addition fails
        """
        try:
            # Create a file-like object with the correct name
            file_obj = BytesIO(file_bytes)
            file_obj.name = file_name  # Set the name attribute which is used by the API
            
            # First create the file using file bytes
            file_response = self.client.files.create(
                file=file_obj,
                purpose="assistants"
            )
            
            # Then create the file batch using the correct API structure
            response = self.client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=file_response.id
            )
            
            # Update file count in cache
            for store_key, store_info in self._vector_stores.items():
                if store_info["id"] == vector_store_id:
                    store_info["file_count"] += 1
                    break
            
            logger.info(f"Added file {file_name} to vector store {vector_store_id}")
            return {
                "id": response.id,
                "status": response.status,
                "file_id": file_response.id
            }
            
        except Exception as e:
            logger.error(f"Error adding file to vector store: {e}")
            raise VectorStoreServiceError(f"Failed to add file: {e}")

    def list_vector_store_files(self, vector_store_id: str) -> List[Dict]:
        """
        List files in the vector store
        
        Args:
            vector_store_id: ID of the vector store
            
        Returns:
            List of file information dictionaries
            
        Raises:
            VectorStoreServiceError: If file listing fails
        """
        try:
            response = self.client.vector_stores.files.list(
                vector_store_id=vector_store_id
            )
            
            return [{
                "id": file.id,
                "filename": file.filename,
                "status": file.status,
                "created_at": file.created_at,
                "metadata": file.metadata
            } for file in response.data]
            
        except Exception as e:
            logger.error(f"Error listing vector store files: {e}")
            raise VectorStoreServiceError(f"Failed to list files: {e}")

    def delete_vector_store_file(self, vector_store_id: str, file_id: str) -> bool:
        """
        Delete a file from the vector store
        
        Args:
            vector_store_id: ID of the vector store
            file_id: ID of the file to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            VectorStoreServiceError: If file deletion fails
        """
        try:
            self.client.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            # Update file count in cache
            for store_key, store_info in self._vector_stores.items():
                if store_info["id"] == vector_store_id:
                    store_info["file_count"] = max(0, store_info["file_count"] - 1)
                    break
            
            logger.info(f"Deleted file {file_id} from vector store {vector_store_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector store file: {e}")
            raise VectorStoreServiceError(f"Failed to delete file: {e}")

    def delete_vector_store(self, vector_store_id: str) -> bool:
        """
        Delete an entire vector store
        
        Args:
            vector_store_id: ID of the vector store to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            VectorStoreServiceError: If vector store deletion fails
        """
        try:
            self.client.vector_stores.delete(vector_store_id=vector_store_id)
            
            # Remove from cache
            for store_key, store_info in list(self._vector_stores.items()):
                if store_info["id"] == vector_store_id:
                    del self._vector_stores[store_key]
                    break
            
            logger.info(f"Deleted vector store {vector_store_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting vector store: {e}")
            raise VectorStoreServiceError(f"Failed to delete vector store: {e}")

    def get_vector_store_file_content(self, file_id: str) -> Optional[Dict]:
        """
        Get content of a specific file from the vector store
        
        Args:
            file_id: ID of the file to retrieve
            
        Returns:
            Dictionary with file content and metadata, or None if not found
            
        Raises:
            VectorStoreServiceError: If content retrieval fails
        """
        try:
            response = self.client.vector_stores.files.retrieve(file_id=file_id)
            
            return {
                "id": response.id,
                "filename": response.filename,
                "status": response.status,
                "created_at": response.created_at,
                "metadata": response.metadata,
                "content": response.content if hasattr(response, 'content') else None
            }
            
        except Exception as e:
            logger.error(f"Error retrieving vector store file content: {e}")
            raise VectorStoreServiceError(f"Failed to retrieve content: {e}")

    def search_vector_store(self,
                          vector_store_id: str,
                          query: str,
                          max_results: int = 10) -> List[Dict]:
        """
        Search the vector store for relevant content
        
        Args:
            vector_store_id: ID of the vector store
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with relevance scores
            
        Raises:
            VectorStoreServiceError: If search fails
        """
        try:
            response = self.client.vector_stores.search(
                vector_store_id=vector_store_id,
                query=query,
                limit=max_results
            )
            
            return [{
                "id": result.id,
                "filename": result.filename,
                "content": result.content,
                "score": result.score,
                "metadata": result.metadata
            } for result in response.data]
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise VectorStoreServiceError(f"Failed to search vector store: {e}")

    def create_vector_store_with_file(self,
                                    subject: str,
                                    week: str,
                                    file_path: str,
                                    file_name: str,
                                    email: Optional[str] = None) -> Dict:
        """
        Create a vector store and add a file to it
        
        Args:
            subject: Subject name
            week: Week number
            file_path: Path to the file
            file_name: Original file name
            email: Optional user email
            
        Returns:
            Dictionary with vector store and file information
            
        Raises:
            VectorStoreServiceError: If creation or file addition fails
        """
        try:
            # Create vector store
            vector_store = self.create_vector_store(subject, week, email)
            
            # Read file bytes
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
            
            # Add file to vector store
            file_batch = self.add_file_to_vector_store(
                vector_store_id=vector_store["id"],
                file_bytes=file_bytes,
                file_name=file_name
            )
            
            return {
                "vector_store": vector_store,
                "file_batch": file_batch,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error creating vector store with file: {e}")
            raise VectorStoreServiceError(f"Failed to create vector store with file: {e}")

    def delete_vector_store_by_subject_week(self,
                                          subject: str,
                                          week: str,
                                          email: Optional[str] = None) -> bool:
        """
        Delete a vector store by subject and week
        
        Args:
            subject: Subject name
            week: Week number
            email: Optional user email
            
        Returns:
            True if deletion was successful
            
        Raises:
            VectorStoreServiceError: If deletion fails
        """
        try:
            # Get vector store ID
            vector_store_id = self.get_vector_store_id(subject, week, email)
            if not vector_store_id:
                logger.warning(f"No vector store found for {subject} week {week}")
                return False
            
            # Delete vector store
            success = self.delete_vector_store(vector_store_id)
            
            if success:
                # Remove from cache
                store_key = self._generate_store_key(subject, week, email)
                if store_key in self._vector_stores:
                    del self._vector_stores[store_key]
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting vector store by subject/week: {e}")
            raise VectorStoreServiceError(f"Failed to delete vector store: {e}")

    def generate_questions_from_store(self,
                                    subject: str,
                                    week: str,
                                    num_questions: int = 5,
                                    existing_questions: Optional[List[Dict]] = None,
                                    email: Optional[str] = None) -> List[Dict]:
        """
        Generate questions from a vector store
        
        Args:
            subject: Subject name
            week: Week number
            num_questions: Number of questions to generate
            existing_questions: Optional list of existing questions
            email: Optional user email
            
        Returns:
            List of generated questions
            
        Raises:
            VectorStoreServiceError: If question generation fails
        """
        try:
            # Get vector store ID
            vector_store_id = self.get_vector_store_id(subject, week, email)
            if not vector_store_id:
                raise VectorStoreServiceError(f"No vector store found for {subject} week {week}")
            
            # Search vector store for relevant content
            search_results = self.search_vector_store(
                vector_store_id=vector_store_id,
                query=f"Generate {num_questions} questions about {subject} week {week}",
                max_results=10
            )
            
            # Process search results into questions
            questions = []
            for result in search_results:
                # Extract question and answer from content
                content = result.get("content", "")
                if content:
                    # Split content into question and answer
                    parts = content.split("Answer:", 1)
                    if len(parts) == 2:
                        question = parts[0].strip()
                        answer = parts[1].strip()
                        questions.append({
                            "question": question,
                            "answer": answer
                        })
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating questions from store: {e}")
            raise VectorStoreServiceError(f"Failed to generate questions: {e}") 
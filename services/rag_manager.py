from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime

from .openai_service import OpenAIService, Question, OpenAIServiceError
from .vector_store_service import VectorStoreService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGManagerError(Exception):
    """Custom exception for RAG Manager errors"""
    pass

@dataclass
class GenerationConfig:
    """Configuration for question generation"""
    num_questions: int
    difficulty: Optional[str] = None
    topics: Optional[List[str]] = None
    custom_prompt: Optional[str] = None
    temperature: float = 0.7
    max_output_tokens: int = 2000

class RAGManager:
    def __init__(self, openai_service: OpenAIService, vector_store_service: VectorStoreService):
        """Initialize the RAG Manager with required services"""
        self.openai_service = openai_service
        self.vector_store_service = vector_store_service
        logger.info("RAG Manager initialized successfully")

    def generate_questions(self,
                         subject: str,
                         week: str,
                         config: GenerationConfig,
                         email: Optional[str] = None) -> List[Question]:
        """
        Generate questions using RAG approach
        
        Args:
            subject: Subject name
            week: Week number
            config: Generation configuration
            email: Optional user email for user-specific vector stores
            
        Returns:
            List of generated Question objects
            
        Raises:
            RAGManagerError: If question generation fails
        """
        try:
            # Get vector store ID
            vector_store_id = self.vector_store_service.get_vector_store_id(subject, week, email)
            if not vector_store_id:
                raise RAGManagerError(f"No vector store found for {subject} week {week}")
                
            # Generate questions using OpenAI service
            questions = self.openai_service.generate_questions(
                vector_store_id=vector_store_id,
                subject=subject,
                week=week,
                num_questions=config.num_questions,
                custom_prompt=config.custom_prompt,
                difficulty=config.difficulty,
                topics=config.topics
            )
            
            # Validate and clean up questions
            valid_questions = self.openai_service.validate_questions(questions)
            
            if len(valid_questions) < config.num_questions:
                logger.warning(
                    f"Generated fewer questions than requested: {len(valid_questions)} vs {config.num_questions}"
                )
            
            return valid_questions[:config.num_questions]
            
        except OpenAIServiceError as e:
            logger.error(f"OpenAI service error: {e}")
            raise RAGManagerError(f"Failed to generate questions: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in RAG Manager: {e}")
            raise RAGManagerError(f"Unexpected error: {e}")

    def process_uploaded_file(self,
                            file_path: str,
                            file_name: str,
                            subject: str,
                            week: str,
                            email: Optional[str] = None) -> Dict:
        """
        Process an uploaded file and add it to the vector store
        
        Args:
            file_path: Path to the file
            file_name: Original file name
            subject: Subject name
            week: Week number
            email: Optional user email
            
        Returns:
            Dictionary with processing results
            
        Raises:
            RAGManagerError: If file processing fails
        """
        try:
            return self.vector_store_service.create_vector_store_with_file(
                subject=subject,
                week=week,
                file_path=file_path,
                file_name=file_name,
                email=email
            )
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            raise RAGManagerError(f"Failed to process file: {e}")

    def get_vector_store_files(self,
                             subject: str,
                             week: str,
                             email: Optional[str] = None) -> List[Dict]:
        """
        Get list of files in the vector store
        
        Args:
            subject: Subject name
            week: Week number
            email: Optional user email
            
        Returns:
            List of file information dictionaries
            
        Raises:
            RAGManagerError: If file listing fails
        """
        try:
            vector_store_id = self.vector_store_service.get_vector_store_id(subject, week, email)
            if not vector_store_id:
                return []
                
            return self.vector_store_service.list_vector_store_files(vector_store_id)
            
        except Exception as e:
            logger.error(f"Error listing vector store files: {e}")
            raise RAGManagerError(f"Failed to list files: {e}")

    def delete_vector_store_file(self,
                               subject: str,
                               week: str,
                               file_id: str,
                               email: Optional[str] = None) -> bool:
        """
        Delete a file from the vector store
        
        Args:
            subject: Subject name
            week: Week number
            file_id: ID of the file to delete
            email: Optional user email
            
        Returns:
            True if deletion was successful
            
        Raises:
            RAGManagerError: If file deletion fails
        """
        try:
            vector_store_id = self.vector_store_service.get_vector_store_id(subject, week, email)
            if not vector_store_id:
                raise RAGManagerError(f"No vector store found for {subject} week {week}")
                
            return self.vector_store_service.delete_vector_store_file(vector_store_id, file_id)
            
        except Exception as e:
            logger.error(f"Error deleting vector store file: {e}")
            raise RAGManagerError(f"Failed to delete file: {e}")

    def delete_vector_store(self,
                          subject: str,
                          week: str,
                          email: Optional[str] = None) -> bool:
        """
        Delete an entire vector store
        
        Args:
            subject: Subject name
            week: Week number
            email: Optional user email
            
        Returns:
            True if deletion was successful
            
        Raises:
            RAGManagerError: If vector store deletion fails
        """
        try:
            return self.vector_store_service.delete_vector_store_by_subject_week(
                subject=subject,
                week=week,
                email=email
            )
            
        except Exception as e:
            logger.error(f"Error deleting vector store: {e}")
            raise RAGManagerError(f"Failed to delete vector store: {e}")

    def get_vector_store_content(self,
                               subject: str,
                               week: str,
                               file_id: str,
                               email: Optional[str] = None) -> Optional[Dict]:
        """
        Get content of a specific file from the vector store
        
        Args:
            subject: Subject name
            week: Week number
            file_id: ID of the file to retrieve
            email: Optional user email
            
        Returns:
            Dictionary with file content and metadata, or None if not found
            
        Raises:
            RAGManagerError: If content retrieval fails
        """
        try:
            vector_store_id = self.vector_store_service.get_vector_store_id(subject, week, email)
            if not vector_store_id:
                raise RAGManagerError(f"No vector store found for {subject} week {week}")
                
            return self.vector_store_service.get_vector_store_file_content(file_id)
            
        except Exception as e:
            logger.error(f"Error retrieving vector store content: {e}")
            raise RAGManagerError(f"Failed to retrieve content: {e}")

    def generate_questions_with_rag(self,
                                  subject: str,
                                  week: str,
                                  num_questions: int = 5,
                                  existing_questions: Optional[List[Dict]] = None,
                                  email: Optional[str] = None) -> List[Dict]:
        """
        Generate questions using RAG approach with existing questions context
        
        Args:
            subject: Subject name
            week: Week number
            num_questions: Number of questions to generate
            existing_questions: Optional list of existing questions
            email: Optional user email
            
        Returns:
            List of generated questions
            
        Raises:
            RAGManagerError: If question generation fails
        """
        try:
            # First try to generate questions from vector store
            questions = self.vector_store_service.generate_questions_from_store(
                subject=subject,
                week=week,
                num_questions=num_questions,
                existing_questions=existing_questions,
                email=email
            )
            
            # If not enough questions generated, use OpenAI service
            if len(questions) < num_questions:
                config = GenerationConfig(
                    num_questions=num_questions - len(questions),
                    custom_prompt=f"Generate questions about {subject} week {week}"
                )
                
                openai_questions = self.generate_questions(
                    subject=subject,
                    week=week,
                    config=config,
                    email=email
                )
                
                # Convert OpenAI questions to dict format
                openai_questions_dict = [
                    {
                        "question": q.question,
                        "answer": q.answer
                    } for q in openai_questions
                ]
                
                questions.extend(openai_questions_dict)
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating questions with RAG: {e}")
            raise RAGManagerError(f"Failed to generate questions: {e}") 
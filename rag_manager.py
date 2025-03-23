import os
import json
import time
from typing import List, Dict, Optional, Any, Tuple
from openai import OpenAI
import tempfile
import streamlit as st
from dotenv import load_dotenv

# Load environment variables as fallback
load_dotenv()

class RAGManager:
    def __init__(self):
        """Initialize the RAG Manager."""
        print("Initializing RAG Manager")
        
        # Initialize the OpenAI client using Streamlit secrets if available
        api_key = None
        
        try:
            if "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
                print("Using OpenAI API key from Streamlit secrets")
        except Exception as e:
            print(f"Could not access Streamlit secrets: {e}")
            print("Will use default OpenAI API key from environment variable")
        
        self.client = OpenAI(api_key=api_key)
        
        # Dictionary to track vector stores we've created
        self.vector_stores = {}
        
        # Check for vector store ID compliance
        self.check_vector_store_id_compliance()
        
    def check_vector_store_id_compliance(self):
        """
        Check existing vector stores for compliance with the 64-character limit.
        Warns about any vector store IDs that exceed the limit, as they won't work with the API.
        """
        try:
            # Try to list all vector stores
            vector_stores = self.client.vector_stores.list()
            oversized_ids = []
            
            for store in vector_stores.data:
                if len(store.id) > 64:
                    oversized_ids.append({
                        "id": store.id,
                        "name": store.name,
                        "length": len(store.id)
                    })
            
            if oversized_ids:
                print(f"WARNING: Found {len(oversized_ids)} vector stores with IDs exceeding the 64-character limit:")
                for store in oversized_ids:
                    print(f"  - {store['name']} (ID: {store['id'][:20]}... - {store['length']} chars)")
                print("These vector stores cannot be used with the OpenAI API and should be recreated.")
        except Exception as e:
            print(f"Could not check vector store ID compliance: {e}")
        
    def get_vector_store_name(self, subject: str, week: str, email: str = None) -> str:
        """
        Generate a unique, descriptive name for a vector store.
        
        Args:
            subject: The subject name
            week: The week number
            email: Optional user email to create user-specific vector store
            
        Returns:
            A sanitized vector store name (limited to 64 characters)
        """
        # Make sure the subject and week are sanitized for OpenAI vector store name
        sanitized_subject = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in subject)
        
        # Set a maximum length for the subject to leave room for other components
        max_subject_length = 30
        if len(sanitized_subject) > max_subject_length:
            sanitized_subject = sanitized_subject[:max_subject_length]
        
        # Sanitize and limit the week field too
        sanitized_week = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in str(week))
        max_week_length = 5
        if len(sanitized_week) > max_week_length:
            sanitized_week = sanitized_week[:max_week_length]
        
        # Generate vector store name
        if email:
            import hashlib
            # Create a short hash (first 8 chars) of the email
            email_hash = hashlib.md5(email.encode()).hexdigest()[:8]
            vector_store_name = f"{sanitized_subject}_W{sanitized_week}_U{email_hash}"
        else:
            vector_store_name = f"{sanitized_subject}_W{sanitized_week}"
        
        # OpenAI has a 64 character limit on vector store IDs
        if len(vector_store_name) > 64:
            # If we're still over the limit, truncate the whole name
            vector_store_name = vector_store_name[:64]
            print(f"WARNING: Vector store name truncated to {vector_store_name}")
        
        return vector_store_name
    
    def get_or_create_vector_store(self, subject: str, week: str, email: str = None) -> Dict:
        """
        Get or create a vector store for a specific subject and week.
        
        Args:
            subject: The subject name
            week: The week number or identifier
            email: Optional user email to create user-specific vector store
        
        Returns:
            A dict with vector store information
        """
        vector_store_name = self.get_vector_store_name(subject, week, email)
        
        # Create a unique key that includes email if provided
        store_key = f"{subject}_{week}" if not email else f"{subject}_{week}_{email}"
        
        # For debugging
        print(f"Looking for vector store with key: {store_key}, name: {vector_store_name}")
        
        if store_key in self.vector_stores:
            print(f"Found existing vector store for {store_key}")
            return self.vector_stores[store_key]
        
        # Try to list vector stores to see if it already exists
        try:
            vector_stores = self.client.vector_stores.list()
            for store in vector_stores.data:
                print(f"Checking OpenAI vector store: {store.name}")
                if store.name == vector_store_name:
                    # Found an existing vector store
                    print(f"Found matching vector store in OpenAI: {store.name} with ID: {store.id}")
                    self.vector_stores[store_key] = {
                        "id": store.id,
                        "name": store.name,
                        "subject": subject,
                        "week": week,
                        "email": email  # Store user email if provided
                    }
                    return self.vector_stores[store_key]
        except Exception as e:
            print(f"Warning: Could not list vector stores: {e}")
            # Continue with creating a new one
        
        # Create a new vector store
        try:
            print(f"Creating new vector store with name: {vector_store_name}")
            vector_store = self.client.vector_stores.create(
                name=vector_store_name,
                expires_after=None  # Don't expire
            )
            
            print(f"Successfully created vector store: {vector_store.name} with ID: {vector_store.id}")
            
            # Store it in our tracking dictionary
            self.vector_stores[store_key] = {
                "id": vector_store.id,
                "name": vector_store.name,
                "subject": subject,
                "week": week,
                "email": email  # Store user email if provided
            }
            
            print(f"Vector store added to tracking with key: {store_key}")
            return self.vector_stores[store_key]
        except Exception as e:
            raise ValueError(f"Failed to create vector store: {e}")
            
    def save_vector_store_to_data(self, data: Dict, subject: str, week: str, vector_store_info: Dict, email: str = None) -> Dict:
        """
        Save vector store information to the data dictionary for persistent storage.
        
        Parameters:
            data: The main data dictionary
            subject: Subject name
            week: Week number (as string)
            vector_store_info: Dictionary with vector store information
            email: Optional user email to associate with this vector store
            
        Returns:
            Updated data dictionary
        """
        if subject not in data:
            data[subject] = {}
            
        week_str = str(week)
        if week_str not in data[subject]:
            data[subject][week_str] = []
            
        # Add or update the vector_store_metadata at the subject/week level
        if "vector_store_metadata" not in data[subject]:
            data[subject]["vector_store_metadata"] = {}
            
        # Save the vector store ID and name
        vector_store_data = {
            "id": vector_store_info["id"],
            "name": vector_store_info["name"]
        }
        
        # Add email to vector store metadata if provided
        if email:
            vector_store_data["email"] = email
            
        data[subject]["vector_store_metadata"][week_str] = vector_store_data
        
        return data
        
    def load_vector_stores_from_data(self, data: Dict, email: str = None) -> None:
        """
        Load previously saved vector stores from the data dictionary.
        
        Parameters:
            data: The main data dictionary
            email: Optional user email to filter by ownership
        """
        loaded_count = 0
        for subject in data:
            if isinstance(data[subject], dict) and "vector_store_metadata" in data[subject]:
                for week, metadata in data[subject]["vector_store_metadata"].items():
                    if isinstance(metadata, dict) and "id" in metadata and "name" in metadata:
                        # Determine if this vector store should be loaded based on ownership:
                        # 1. If email is provided, load vector stores owned by this user OR legacy stores with no owner
                        # 2. If no email provided, only load vector stores with no owner
                        
                        metadata_has_email = "email" in metadata
                        metadata_email = metadata.get("email", None)
                        
                        if email:
                            # Skip if vector store has an email that doesn't match
                            if metadata_has_email and metadata_email != email:
                                continue
                        else:
                            # If no email provided, only load legacy vector stores (no email)
                            if metadata_has_email:
                                continue
                        
                        # Create store key based on whether it has an email
                        store_email = metadata.get("email")
                        store_key = f"{subject}_{week}" if not store_email else f"{subject}_{week}_{store_email}"
                        
                        # Store in our dictionary
                        store_data = {
                            "id": metadata["id"],
                            "name": metadata["name"],
                            "subject": subject,
                            "week": week
                        }
                        
                        # Include email if present
                        if "email" in metadata:
                            store_data["email"] = metadata["email"]
                            
                        self.vector_stores[store_key] = store_data
                        loaded_count += 1
        
        print(f"Loaded {loaded_count} vector stores from data")
    
    def add_file_to_vector_store(self, 
                               vector_store_id: str, 
                               file_bytes: bytes, 
                               file_name: str) -> Dict:
        """
        Add a file to an OpenAI vector store.
        
        Returns:
            Dictionary with file batch information
        
        Raises:
            ValueError: If the vector store ID is invalid or too long
        """
        # Validate the vector store ID length before making the API call
        if len(vector_store_id) > 64:
            raise ValueError(f"Vector store ID is too long ({len(vector_store_id)} chars). Maximum allowed is 64 characters.")
        
        print(f"Adding file {file_name} to vector store with ID: {vector_store_id}")
        
        # Write the file bytes to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
        
        try:
            # Open the file for OpenAI upload
            with open(temp_path, "rb") as file_stream:
                print(f"Uploading file to OpenAI vector store")
                # Upload and poll for completion
                file_batch = self.client.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store_id,
                    files=[file_stream]
                )
                print(f"File batch created with ID: {file_batch.id}, status: {file_batch.status}")
                
                # Wait for the file to finish processing if needed
                timeout = 60  # 60 seconds max wait
                start_time = time.time()
                while file_batch.status != "completed" and time.time() - start_time < timeout:
                    time.sleep(2)
                    file_batch = self.client.vector_stores.file_batches.retrieve(
                        vector_store_id=vector_store_id,
                        file_batch_id=file_batch.id
                    )
                
                result = {
                    "id": file_batch.id,
                    "status": file_batch.status,
                    "file_counts": file_batch.file_counts,
                    "original_filename": file_name
                }
                
                # Try to get the file IDs
                if hasattr(file_batch, 'file_ids') and file_batch.file_ids:
                    result["file_ids"] = file_batch.file_ids
                
                return result
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    def list_vector_store_files(self, vector_store_id: str) -> List[Dict]:
        """
        List all files in a vector store.
        
        Parameters:
            vector_store_id: The ID of the vector store
            
        Returns:
            List of file information dicts
        
        Raises:
            ValueError: If the vector store ID is invalid or too long
        """
        try:
            # Add more detailed logging for troubleshooting
            print(f"Attempting to list files for vector store ID: '{vector_store_id}' (length: {len(vector_store_id)})")
            
            # Validate the vector store ID length before making the API call
            if len(vector_store_id) > 64:
                # Provide more detailed error message to help with debugging
                print(f"ERROR: Vector store ID is too long: {len(vector_store_id)} chars. First 20 chars: '{vector_store_id[:20]}...'")
                raise ValueError(f"Vector store ID is too long ({len(vector_store_id)} chars). Maximum allowed is 64 characters.")
            
            vector_store_files = self.client.vector_stores.files.list(
                vector_store_id=vector_store_id
            )
            
            # Convert to a more usable format
            files = []
            for file in vector_store_files.data:
                # Try to get additional file information
                file_details = None
                try:
                    # Try to get information from the file ID
                    if file.id.startswith("file-"):
                        # Extract the original file ID
                        original_file_id = file.id
                        file_details = self.client.files.retrieve(file_id=original_file_id)
                except Exception as file_err:
                    print(f"Could not retrieve additional file details: {file_err}")
                
                file_info = {
                    "id": file.id,
                    "object": file.object,
                    "created_at": file.created_at,
                    "status": getattr(file, 'status', None),
                    "filename": getattr(file_details, 'filename', 'Unknown')
                }
                
                files.append(file_info)
            
            return files
        except Exception as e:
            print(f"Error listing vector store files: {e}")
            # Re-raise with more specific information
            if "string too long" in str(e) or "above_max_length" in str(e):
                raise ValueError(f"Vector store ID is invalid: {str(e)}")
            elif "not_found" in str(e):
                raise ValueError(f"Vector store not found: {vector_store_id}")
            else:
                raise
            return []
            
    def get_vector_store_file(self, vector_store_id: str, file_id: str) -> Dict:
        """
        Get details about a specific file in a vector store.
        
        Parameters:
            vector_store_id: The ID of the vector store
            file_id: The ID of the file
            
        Returns:
            File information dict
        """
        try:
            file = self.client.vector_stores.files.retrieve(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            # Try to get additional file information
            file_details = None
            try:
                # Try to get information from the file ID
                if file.id.startswith("file-"):
                    # Extract the original file ID
                    original_file_id = file.id
                    file_details = self.client.files.retrieve(file_id=original_file_id)
            except Exception as file_err:
                print(f"Could not retrieve additional file details: {file_err}")
            
            return {
                "id": file.id,
                "object": file.object,
                "created_at": file.created_at,
                "status": getattr(file, 'status', None),
                "filename": getattr(file_details, 'filename', 'Unknown')
            }
        except Exception as e:
            print(f"Error retrieving vector store file: {e}")
            return None
            
    def delete_vector_store_file(self, vector_store_id: str, file_id: str) -> bool:
        """
        Delete a file from a vector store.
        
        Parameters:
            vector_store_id: The ID of the vector store
            file_id: The ID of the file
            
        Returns:
            Boolean indicating success
            
        Raises:
            ValueError: If the vector store ID is invalid or too long
        """
        try:
            # Validate the vector store ID length before making the API call
            if len(vector_store_id) > 64:
                raise ValueError(f"Vector store ID is too long ({len(vector_store_id)} chars). Maximum allowed is 64 characters.")
            
            deleted_file = self.client.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            
            # Return True if deletion was successful
            return deleted_file.deleted
        except Exception as e:
            print(f"Error deleting vector store file: {e}")
            return False
            
    def delete_vector_store(self, vector_store_id: str) -> bool:
        """
        Delete an entire vector store and all its files.
        
        Parameters:
            vector_store_id: The ID of the vector store to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            print(f"Attempting to delete vector store with ID: {vector_store_id}")
            
            # Delete the vector store using the OpenAI API
            result = self.client.vector_stores.delete(
                vector_store_id=vector_store_id
            )
            
            # Find and remove from our tracking dictionary
            keys_to_remove = []
            for key, store_info in self.vector_stores.items():
                if store_info.get("id") == vector_store_id:
                    keys_to_remove.append(key)
            
            # Remove the matching entries
            for key in keys_to_remove:
                self.vector_stores.pop(key)
                print(f"Removed vector store with key {key} from tracking dictionary")
            
            print(f"Vector store deleted successfully: {result.deleted}")
            return result.deleted
        except Exception as e:
            print(f"Error deleting vector store: {e}")
            return False
            
    def get_vector_store_file_content(self, file_id: str) -> Optional[Dict]:
        """
        Get the content of a specific file from a vector store.
        
        Parameters:
            file_id: The ID of the file
            
        Returns:
            Dictionary with content and content_type or None if retrieval fails
        """
        try:
            if not file_id.startswith("file-"):
                print(f"File ID {file_id} is not in the expected format")
                return None
                
            # Try to download the file content
            response = self.client.files.content(file_id=file_id)
            file_bytes = response.read()
            
            # Try to get file details to determine content type
            try:
                file_details = self.client.files.retrieve(file_id=file_id)
                filename = getattr(file_details, 'filename', '')
                if filename.lower().endswith('.pdf'):
                    return {
                        "content_type": "pdf",
                        "content": file_bytes,
                        "text_content": "PDF file content cannot be directly displayed. Use the download button to view."
                    }
                else:
                    # Assume text file
                    try:
                        text_content = file_bytes.decode("utf-8")
                        return {
                            "content_type": "text",
                            "content": file_bytes,
                            "text_content": text_content
                        }
                    except UnicodeDecodeError:
                        # Not a text file
                        return {
                            "content_type": "binary",
                            "content": file_bytes,
                            "text_content": "Binary file content cannot be directly displayed. Use the download button to view."
                        }
            except Exception as details_err:
                # If we can't get file details, try to decode as text
                try:
                    text_content = file_bytes.decode("utf-8")
                    return {
                        "content_type": "text",
                        "content": file_bytes,
                        "text_content": text_content
                    }
                except UnicodeDecodeError:
                    # Not a text file
                    return {
                        "content_type": "binary",
                        "content": file_bytes,
                        "text_content": "Binary file content cannot be directly displayed. Use the download button to view."
                    }
            
        except Exception as e:
            print(f"Error retrieving file content: {e}")
            return None
            
    def rename_file_in_tracking(self, subject: str, week: str, old_filename: str, new_filename: str, 
                              data: Dict) -> Dict:
        """
        Rename a file in the local tracking system.
        
        Parameters:
            subject: Subject name
            week: Week number
            old_filename: The original filename
            new_filename: The new filename
            data: The data dictionary (not used directly but included for API consistency)
            
        Returns:
            Updated data dictionary
        """
        try:
            # This is a no-op for the data dict since we now store uploads in session_state.uploaded_files
            # We're keeping the method for API consistency and future extensibility
            print(f"Rename tracking: {subject}/{week} - {old_filename} -> {new_filename}")
            return data
        except Exception as e:
            print(f"Error renaming file in tracking: {e}")
            return data
            
    def remove_vector_store_from_data(self, data: Dict, subject: str, week: str, email: str = None) -> Dict:
        """
        Remove vector store metadata from the data dictionary.
        
        Parameters:
            data: The main data dictionary
            subject: Subject name
            week: Week number (as string)
            email: Optional user email associated with the vector store
            
        Returns:
            Updated data dictionary with the vector store metadata removed
        """
        try:
            if subject in data and "vector_store_metadata" in data[subject] and week in data[subject]["vector_store_metadata"]:
                # Check if this is the user's vector store (if email is provided)
                if email:
                    metadata_email = data[subject]["vector_store_metadata"][week].get("email")
                    if metadata_email and metadata_email != email:
                        # Not this user's vector store, don't remove it
                        print(f"Skipping removal - vector store belongs to {metadata_email}, not {email}")
                        return data
                
                # Remove the vector store metadata
                print(f"Removing vector store metadata for {subject}/{week}")
                data[subject]["vector_store_metadata"].pop(week)
                
                # If this was the last vector store for this subject, remove the vector_store_metadata dict
                if not data[subject]["vector_store_metadata"]:
                    data[subject].pop("vector_store_metadata")
            
            return data
        except Exception as e:
            print(f"Error removing vector store from data: {e}")
            return data
    
    def create_assistant_for_vector_store(self, vector_store_id: str) -> Dict:
        """
        Create an assistant that can search the vector store.
        
        Returns:
            The assistant object
        """
        print(f"Creating assistant with vector_store_id: {vector_store_id}")
        try:
            assistant = self.client.beta.assistants.create(
                name="Study Question Generator",
                instructions="""You are an expert teacher creating study questions for university students.
Generate thought-provoking questions based on the provided content from course materials.
Each question should test understanding, not just memorization.
For each question, also provide a comprehensive answer that would be useful for studying.""",
                model="gpt-4o",
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
            )
            print(f"Successfully created assistant with ID: {assistant.id}")
        except Exception as e:
            print(f"Error creating assistant: {e}")
            raise
        
        return assistant
    
    def create_or_update_vector_store(self, 
                                     subject: str, 
                                     week: str, 
                                     file_bytes: bytes, 
                                     file_type: str,
                                     file_name: str,
                                     email: str = None) -> Dict:
        """
        Create or update a vector store for a specific subject and week.
        
        Returns:
            Dict with vector store information
        """
        print(f"create_or_update_vector_store: subject={subject}, week={week}, email={email}")
        
        # Get or create the vector store
        vector_store = self.get_or_create_vector_store(subject, week, email)
        
        print(f"Got vector store with ID: {vector_store['id']}, name: {vector_store['name']}")
        
        # Add the file to the vector store
        file_batch = self.add_file_to_vector_store(
            vector_store_id=vector_store["id"],
            file_bytes=file_bytes,
            file_name=file_name
        )
        
        # Return combined information
        return {
            "vector_store": vector_store,
            "file_batch": file_batch
        }
    
    def generate_questions_with_rag(self,
                                   subject: str,
                                   week: str, 
                                   num_questions: int,
                                   existing_questions: List[Dict[str, Any]] = None,
                                   email: str = None) -> List[Dict[str, str]]:
        """
        Generate questions for a specific subject and week using RAG approach.
        
        Parameters:
            subject: The course subject
            week: The week number
            num_questions: How many questions to generate
            existing_questions: Optional list of existing questions to avoid duplication
            email: User's email to filter vector stores by ownership
            
        Returns:
            List of generated question-answer pairs
        """
        # Get the vector store - create a unique key that includes email if provided
        store_key = f"{subject}_{week}" if not email else f"{subject}_{week}_{email}"
        
        print(f"generate_questions_with_rag: Looking for vector store with key: {store_key}")
        print(f"Available vector stores: {list(self.vector_stores.keys())}")
        
        if store_key not in self.vector_stores:
            print(f"Vector store not found in memory, trying to find in API")
            # Try to find it in the API
            self.get_or_create_vector_store(subject, week, email)
            
            # Check again
            if store_key not in self.vector_stores:
                raise ValueError(f"No content has been uploaded for {subject} week {week}. Please upload content first.")
        
        vector_store = self.vector_stores[store_key]
        print(f"Using vector store: {vector_store['name']} with ID: {vector_store['id']}")
        
        # Format existing questions to avoid duplication
        existing_q_texts = []
        if existing_questions:
            existing_q_texts = [q["question"] for q in existing_questions]
        existing_qs_str = "\n".join([f"- {q}" for q in existing_q_texts])
        
        # Create an assistant with access to the vector store
        print(f"Creating assistant with vector store ID: {vector_store['id']}")
        assistant = self.create_assistant_for_vector_store(vector_store["id"])
        
        # Create a thread with instructions to generate questions
        thread_message = f"""Please generate {num_questions} study questions based on the course content for {subject}, Week {week}.
Each question should have a detailed answer suitable for studying.
The questions should cover key concepts from the content and be varied in difficulty.
"""
        print(f"Creating thread with instructions for {subject}, Week {week}")
        
        # Add existing questions to avoid duplication if there are any
        if existing_q_texts:
            thread_message += f"""
IMPORTANT: Avoid duplicating these existing questions:
{existing_qs_str}
"""
        
        thread = self.client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": thread_message
                }
            ]
        )
        
        # Create a run with instructions to format responses as JSON
        print(f"Creating run with thread ID: {thread.id} and assistant ID: {assistant.id}")
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
            instructions="""When generating questions, please format your response as a valid JSON object with the following structure:
{
  "questions": [
    {
      "question": "What is X?",
      "answer": "X is..."
    },
    ...
  ]
}

Make sure to parse relevant information from the files using the file_search tool before generating questions.
"""
        )
        print(f"Created run with ID: {run.id}, status: {run.status}")
        
        # Poll for completion
        timeout = 120  # 120 seconds max wait
        start_time = time.time()
        while run.status not in ["completed", "failed", "expired", "cancelled"] and time.time() - start_time < timeout:
            time.sleep(2)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        if run.status != "completed":
            raise ValueError(f"Question generation failed with status: {run.status}")
        
        # Get the messages
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id
        )
        
        # Extract the response from the assistant
        response_text = ""
        for message in messages.data:
            if message.role == "assistant":
                for content in message.content:
                    if content.type == "text":
                        response_text += content.text.value
        
        # Extract JSON from the response
        try:
            # Find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                data = json.loads(json_text)
                
                # Extract questions
                if "questions" in data and isinstance(data["questions"], list):
                    questions = data["questions"]
                    
                    # Validate and format the questions
                    validated_questions = []
                    for q in questions:
                        if "question" in q and "answer" in q:
                            validated_questions.append({
                                "question": q["question"],
                                "answer": q["answer"]
                            })
                    
                    # Limit to requested number
                    return validated_questions[:num_questions]
                else:
                    # Try to find an array directly
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0 and "question" in value[0]:
                            return [{"question": q.get("question", ""), "answer": q.get("answer", "")} 
                                   for q in value if "question" in q and "answer" in q][:num_questions]
            
            # If we couldn't find a proper JSON structure, try to parse the whole response
            try:
                data = json.loads(response_text)
                if "questions" in data:
                    return [{"question": q.get("question", ""), "answer": q.get("answer", "")} 
                           for q in data["questions"] if "question" in q and "answer" in q][:num_questions]
            except:
                pass
                
            # Fall back to generating questions using a direct API call
            return self._fallback_generate_questions(subject, week, num_questions, existing_questions)
            
        except Exception as e:
            print(f"Error parsing assistant response: {e}")
            return self._fallback_generate_questions(subject, week, num_questions, existing_questions)
        
    def _fallback_generate_questions(self, subject, week, num_questions, existing_questions):
        """Fallback method to generate questions directly with a chat completion."""
        # Format existing questions to avoid duplication
        existing_q_texts = []
        if existing_questions:
            existing_q_texts = [q["question"] for q in existing_questions]
        existing_qs_str = "\n".join([f"- {q}" for q in existing_q_texts])
        
        # Construct system prompt
        system_prompt = """You are an expert teacher creating study questions for university students. 
Generate thought-provoking questions based on your knowledge of the subject.
Each question should test understanding, not just memorization.
For each question, also provide a comprehensive answer that would be useful for studying."""
        
        # Construct user prompt
        user_prompt = f"""Please generate {num_questions} questions for {subject}, Week {week}.
Each question should have a detailed answer suitable for studying.

The questions should cover key concepts and be varied in difficulty.
"""
        
        # Add existing questions to avoid duplication if there are any
        if existing_q_texts:
            user_prompt += f"""
IMPORTANT: Avoid duplicating these existing questions:
{existing_qs_str}
"""
        
        # Define the function for generating questions
        functions = [
            {
                "name": "generate_study_questions",
                "description": "Generate study questions and answers based on course content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "questions": {
                            "type": "array",
                            "description": "List of generated questions with answers",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "question": {
                                        "type": "string",
                                        "description": "A thought-provoking study question"
                                    },
                                    "answer": {
                                        "type": "string",
                                        "description": "A comprehensive answer to the question"
                                    }
                                },
                                "required": ["question", "answer"]
                            }
                        }
                    },
                    "required": ["questions"]
                }
            }
        ]
        
        try:
            # Send request to OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                functions=functions,
                function_call={"name": "generate_study_questions"},
                temperature=0.7
            )
            
            # Extract the function call arguments
            function_args = json.loads(response.choices[0].message.function_call.arguments)
            questions = function_args.get("questions", [])
            
            # Validate and format the questions
            validated_questions = []
            for q in questions:
                if "question" in q and "answer" in q:
                    validated_questions.append({
                        "question": q["question"],
                        "answer": q["answer"]
                    })
            
            # Limit to requested number
            return validated_questions[:num_questions]
            
        except Exception as e:
            print(f"Error in fallback question generation: {e}")
            raise ValueError("Failed to generate questions. Please try again later.")
    
    def generate_questions_from_file(self,
                                   file_bytes: bytes, 
                                   file_type: str, 
                                   file_name: str,
                                   subject: str, 
                                   week: str, 
                                   num_questions: int,
                                   existing_questions: List[Dict[str, Any]] = None,
                                   data: Dict = None,
                                   email: str = None) -> Tuple[List[Dict[str, str]], Dict]:
        """
        Process uploaded file, store in vector database, and generate questions.
        
        Parameters:
            file_bytes: The bytes of the uploaded file
            file_type: The type of file (pdf or txt)
            file_name: Original filename
            subject: The course subject
            week: The week number
            num_questions: How many questions to generate
            existing_questions: List of existing questions to avoid duplication
            data: The main data dictionary for saving vector store info
            email: User's email to associate with the vector store
            
        Returns:
            Tuple containing:
              - List of generated question-answer pairs
              - Updated data dictionary (if data was provided)
        """
        # First, create or update the vector store
        print(f"generate_questions_from_file: email={email}")
        vector_store_info = self.create_or_update_vector_store(
            subject=subject,
            week=week,
            file_bytes=file_bytes,
            file_type=file_type,
            file_name=file_name,
            email=email
        )
        
        # If data is provided, save vector store info to it
        if data is not None:
            data = self.save_vector_store_to_data(
                data=data,
                subject=subject,
                week=str(week),
                vector_store_info=vector_store_info["vector_store"],
                email=email
            )
        
        # Generate questions from the content
        questions = self.generate_questions_with_rag(
            subject=subject,
            week=week,
            num_questions=num_questions,
            existing_questions=existing_questions,
            email=email
        )
        
        return questions, data

    def sanitize_vector_store_ids(self, data: Dict) -> Dict:
        """
        Scans the data dictionary and fixes any vector store IDs that exceed the 64-character limit.
        
        Parameters:
            data: The data dictionary containing vector store metadata
            
        Returns:
            Updated data dictionary with sanitized vector store IDs
            
        Note:
            This is a fix for existing data that might have vector store IDs exceeding OpenAI's 64-character limit.
            After applying this fix, you should save the updated data back to storage.
        """
        modified = False
        
        # Scan through subjects and their vector store metadata
        for subject in data:
            if isinstance(data[subject], dict) and "vector_store_metadata" in data[subject]:
                metadata = data[subject]["vector_store_metadata"]
                for week in list(metadata.keys()):
                    # Check the format - could be either a string ID or a dictionary with id/name
                    if isinstance(metadata[week], dict) and "id" in metadata[week]:
                        vector_store_id = metadata[week]["id"]
                        # Check if the ID is too long
                        if len(vector_store_id) > 64:
                            print(f"Found oversized vector store ID ({len(vector_store_id)} chars): {vector_store_id}")
                            # Remove the oversized ID - it's invalid and cannot be used with the API
                            del metadata[week]
                            print(f"Removed invalid vector store ID for {subject} week {week}")
                            modified = True
                    elif isinstance(metadata[week], str):
                        vector_store_id = metadata[week]
                        # Check if the ID is too long
                        if len(vector_store_id) > 64:
                            print(f"Found oversized vector store ID ({len(vector_store_id)} chars): {vector_store_id}")
                            # Remove the oversized ID - it's invalid and cannot be used with the API
                            del metadata[week]
                            print(f"Removed invalid vector store ID for {subject} week {week}")
                            modified = True
        
        if modified:
            print("WARNING: Some vector store IDs were removed from the data because they exceeded OpenAI's 64-character limit.")
            print("You will need to recreate these vector stores with shorter names.")
        
        return data
"""
MongoDB data access layer for queue cards.
Provides functions to load, save, and manipulate queue cards data.
"""
import time
from typing import Dict, List, Optional, Any
import math

from .connection import get_collection

# Collection name for queue cards
QUEUE_CARDS_COLLECTION = "queue_cards"


def load_data(email: str = None) -> Dict:
    """
    Load queue cards data from MongoDB.
    Maintains the same structure as the JSON file:
    {
        subject: {
            week: [
                {"question": "...", "answer": "...", "scores": [...], "last_practiced": timestamp}
            ],
            "file_metadata": {
                week_str: [
                    {"file_id": "...", "file_name": "...", "upload_date": "..."}
                ]
            }
        }
    }
    
    Args:
        email: Optional email to filter data by user. If provided, only returns data owned by this user.
    
    Returns:
        Dict: The queue cards data organized by subject and week
    """
    collection = get_collection(QUEUE_CARDS_COLLECTION)
    
    print(f"MongoDB load_data called with email: {email}")
    
    # Build query based on email
    if email:
        # If email is provided, we need to query for:
        # 1. Documents with this specific email
        # 2. Documents with no email field (legacy data)
        query = {"$or": [
            {"email": email},  # Documents owned by this user
            {"email": {"$exists": False}}  # Legacy documents with no email
        ]}
        print(f"MongoDB query with email: {query}")
    else:
        # If no email provided, only return documents without email field
        query = {"email": {"$exists": False}}
        print("MongoDB query for legacy data only (no email)")
    
    # Query documents from the collection with filter
    documents = collection.find(query)
    
    # Build the data structure
    data = {}
    
    for doc in documents:
        subject = doc.get("subject")
        if subject:
            if subject not in data:
                data[subject] = {}
            
            # Handle vector store metadata if present
            if "vector_store_metadata" in doc:
                if "vector_store_metadata" not in data[subject]:
                    data[subject]["vector_store_metadata"] = {}
                
                data[subject]["vector_store_metadata"].update(doc["vector_store_metadata"])
                continue
            
            # Handle file metadata if present
            if "file_metadata" in doc:
                if "file_metadata" not in data[subject]:
                    data[subject]["file_metadata"] = {}
                
                # Update with new file metadata
                for week_str, files in doc["file_metadata"].items():
                    if week_str not in data[subject]["file_metadata"]:
                        data[subject]["file_metadata"][week_str] = []
                    
                    data[subject]["file_metadata"][week_str].extend(files)
                continue
            
            # Regular question data
            week = doc.get("week")
            if week and "questions" in doc:
                if week not in data[subject]:
                    data[subject][week] = []
                
                # Add all questions from this document
                data[subject][week].extend(doc["questions"])
    
    return data


def save_data(data: Dict, email: str = None) -> None:
    """
    Save queue cards data to MongoDB.
    Structure in MongoDB:
    - Each subject+week combination stored as a document
    - Vector store metadata stored separately
    - File metadata stored separately
    - Each document is associated with user email if provided
    
    Args:
        data (Dict): The queue cards data organized by subject and week
        email (str): Optional user email to associate with the data
    """
    collection = get_collection(QUEUE_CARDS_COLLECTION)
    
    print(f"MongoDB save_data called with email: {email}")
    
    # If we have an email, only delete documents associated with this email
    if email:
        # Only delete documents with this specific email
        # Do not touch legacy data or other users' data
        print(f"Deleting documents with email: {email} before saving new data")
        result = collection.delete_many({"email": email})
        print(f"Deleted {result.deleted_count} documents with email: {email}")
    else:
        # Only delete legacy data (no email field)
        # Do not touch any user-specific data
        print("Deleting legacy documents (no email) before saving new data")
        result = collection.delete_many({"email": {"$exists": False}})
        print(f"Deleted {result.deleted_count} legacy documents without email")
    
    # Process and save data by subject and week
    for subject, weeks in data.items():
        for week, questions in weeks.items():
            # Handle vector store metadata
            if week == "vector_store_metadata":
                doc = {
                    "subject": subject,
                    "vector_store_metadata": questions,
                    "updated_at": int(time.time())
                }
                # Add email if provided
                if email:
                    doc["email"] = email
                    print(f"Adding document with email: {email} for subject: {subject}, vector_store_metadata")
                else:
                    print(f"Adding legacy document (no email) for subject: {subject}, vector_store_metadata")
                collection.insert_one(doc)
            # Handle file metadata
            elif week == "file_metadata":
                doc = {
                    "subject": subject,
                    "file_metadata": questions,
                    "updated_at": int(time.time())
                }
                # Add email if provided
                if email:
                    doc["email"] = email
                    print(f"Adding document with email: {email} for subject: {subject}, file_metadata")
                else:
                    print(f"Adding legacy document (no email) for subject: {subject}, file_metadata")
                collection.insert_one(doc)
            else:
                # Regular questions - store in batches of 100 to avoid document size limits
                for i in range(0, len(questions), 100):
                    batch = questions[i:i+100]
                    doc = {
                        "subject": subject,
                        "week": week,
                        "questions": batch,
                        "updated_at": int(time.time())
                    }
                    # Add email if provided
                    if email:
                        doc["email"] = email
                        print(f"Adding document with email: {email} for subject: {subject}, week: {week}, questions: {len(batch)}")
                    else:
                        print(f"Adding legacy document (no email) for subject: {subject}, week: {week}, questions: {len(batch)}")
                    collection.insert_one(doc)


def add_file_metadata(data: Dict, subject: str, week: int, file_id: str, file_name: str, email: str = None) -> Dict:
    """
    Add file metadata to the data.
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
        file_id: OpenAI file ID
        file_name: Original file name
        email: User's email to associate with this file (optional)
    
    Returns:
        Updated data dictionary
    """
    if subject not in data:
        data[subject] = {}
    
    # Initialize file_metadata structure if it doesn't exist
    if "file_metadata" not in data[subject]:
        data[subject]["file_metadata"] = {}
        
    week_str = str(week)
    if week_str not in data[subject]["file_metadata"]:
        data[subject]["file_metadata"][week_str] = []
        
    # Add the file metadata
    file_metadata = {
        "file_id": file_id,
        "file_name": file_name,
        "upload_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add to the list of files for this week
    data[subject]["file_metadata"][week_str].append(file_metadata)
    
    # Save the updated data to MongoDB
    save_data(data, email)
    
    return data


def get_file_metadata(data: Dict, subject: str, week: int) -> List[Dict[str, str]]:
    """
    Get file metadata for a subject and week.
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
    
    Returns:
        List of file metadata dictionaries
    """
    if subject not in data:
        return []
        
    if "file_metadata" not in data[subject]:
        return []
        
    week_str = str(week)
    if week_str not in data[subject]["file_metadata"]:
        return []
        
    return data[subject]["file_metadata"][week_str]


def add_question(data: Dict, subject: str, week: int, question: str, answer: Optional[str] = None, email: str = None) -> Dict:
    """
    Add a new question to the data.
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
        question: Question text
        answer: Answer text (optional)
        email: User's email to associate with this question (optional)
    
    Returns:
        Updated data dictionary
    """
    if subject not in data:
        data[subject] = {}
    
    week_str = str(week)
    if week_str not in data[subject]:
        data[subject][week_str] = []
    
    # Add the question with score tracking
    data[subject][week_str].append({
        "question": question,
        "answer": answer or "",
        "scores": [],  # Will store score history with timestamps
        "last_practiced": None,  # Will track when it was last practiced
        "created_at": int(time.time())
    })
    
    # Save the updated data to MongoDB
    save_data(data, email)
    
    return data


def delete_question(data: Dict, subject: str, week: int, question_idx: int, email: str = None) -> Dict:
    """
    Delete a question from the data.
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
        question_idx: Index of the question to delete
        email: User's email (optional)
    
    Returns:
        Updated data dictionary
    """
    week_str = str(week)
    if subject in data and week_str in data[subject] and question_idx < len(data[subject][week_str]):
        data[subject][week_str].pop(question_idx)
        
        # Save the updated data to MongoDB
        save_data(data, email)
    
    return data


def update_question(data: Dict, subject: str, week: int, question_idx: int, new_question: str, new_answer: str, email: str = None) -> Dict:
    """
    Update an existing question.
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number
        question_idx: Index of the question to update
        new_question: New question text
        new_answer: New answer text
        email: User's email (optional)
    
    Returns:
        Updated data dictionary
    """
    week_str = str(week)
    if subject in data and week_str in data[subject] and question_idx < len(data[subject][week_str]):
        # Keep existing scores and tracking when updating a question
        existing_scores = data[subject][week_str][question_idx].get("scores", [])
        last_practiced = data[subject][week_str][question_idx].get("last_practiced", None)
        created_at = data[subject][week_str][question_idx].get("created_at", int(time.time()))
        
        data[subject][week_str][question_idx] = {
            "question": new_question,
            "answer": new_answer,
            "scores": existing_scores,
            "last_practiced": last_practiced,
            "created_at": created_at,
            "updated_at": int(time.time())
        }
        
        # Save the updated data to MongoDB
        save_data(data, email)
    
    return data


def update_question_score(data: Dict, subject: str, week: str, question_idx: int, score: int, user_answer: str = None, email: str = None) -> Dict:
    """
    Update the score for a specific question in MongoDB with improved error handling and atomic updates.
    """
    print(f"\n=== MongoDB update_question_score called ===")
    print(f"Subject: {subject}, Week: {week}, Question idx: {question_idx}")
    print(f"Score: {score}, User email: {email}")
    
    try:
        collection = get_collection(QUEUE_CARDS_COLLECTION)
        print("Got MongoDB collection")
        
        # Validate inputs
        if not isinstance(score, int) or score < 1 or score > 5:
            raise ValueError(f"Invalid score value: {score}. Score must be between 1 and 5.")
            
        # Create the score entry
        timestamp = int(time.time())
        score_entry = {
            "score": score,
            "timestamp": timestamp
        }
        if user_answer:
            score_entry["user_answer"] = user_answer
            
        print(f"Created score entry: {score_entry}")
            
        # Build the query
        query = {
            "subject": subject,
            "week": week
        }
        if email:
            query["email"] = email
            
        print(f"MongoDB query: {query}")
            
        # Find the document containing this question
        doc = collection.find_one(query)
        print(f"Found document: {bool(doc)}")
        
        if not doc:
            print(f"No document found for subject {subject}, week {week}")
            # Create new document
            print("Creating new document...")
            new_doc = {
                "subject": subject,
                "week": week,
                "email": email,
                "questions": [],
                "updated_at": timestamp
            }
            # Ensure we have enough slots for the question index
            while len(new_doc["questions"]) <= question_idx:
                new_doc["questions"].append({"scores": [], "last_practiced": None})
            collection.insert_one(new_doc)
            print("New document created")
            doc = new_doc
            
        # Update the specific question's scores
        questions = doc.get("questions", [])
        if question_idx >= len(questions):
            print(f"Question index {question_idx} out of range, extending questions array")
            # Extend the questions array if needed
            while len(questions) <= question_idx:
                questions.append({"scores": [], "last_practiced": None})
            
        if "scores" not in questions[question_idx]:
            print("Initializing scores array for question")
            questions[question_idx]["scores"] = []
            
        questions[question_idx]["scores"].append(score_entry)
        questions[question_idx]["last_practiced"] = timestamp
        
        print("Performing atomic update...")
        # Perform atomic update
        update_result = collection.update_one(
            query,
            {
                "$set": {
                    "questions": questions,
                    "updated_at": timestamp
                }
            }
        )
        
        print(f"Update result - matched: {update_result.matched_count}, modified: {update_result.modified_count}")
        
        if update_result.modified_count == 0 and update_result.matched_count == 0:
            print("No document was updated, attempting to insert new document")
            try:
                collection.insert_one({
                    "subject": subject,
                    "week": week,
                    "email": email,
                    "questions": questions,
                    "updated_at": timestamp
                })
                print("New document inserted successfully")
            except Exception as e:
                print(f"Error inserting new document: {str(e)}")
                raise
            
        # Update the in-memory data structure
        if subject not in data:
            data[subject] = {}
        if week not in data[subject]:
            data[subject][week] = []
        while len(data[subject][week]) <= question_idx:
            data[subject][week].append({"scores": [], "last_practiced": None})
            
        data[subject][week][question_idx]["scores"] = questions[question_idx]["scores"]
        data[subject][week][question_idx]["last_practiced"] = timestamp
        
        print("In-memory data structure updated")
        return data
        
    except Exception as e:
        print(f"Error in MongoDB update_question_score: {str(e)}")
        import traceback
        print(f"Full error traceback:\n{traceback.format_exc()}")
        raise  # Re-raise the exception to be handled by the caller


def save_ai_feedback(data: Dict, question_item: Dict, feedback_data: Dict) -> Dict:
    """
    Save AI feedback to the most recent score entry
    
    Args:
        data: The data dictionary
        question_item: The question item dictionary
        feedback_data: The feedback data dictionary
    
    Returns:
        Updated data dictionary
    """
    subject = question_item["subject"]
    week = question_item["week"]
    idx = question_item["question_idx"]
    
    if (subject in data and 
        week in data[subject] and 
        idx < len(data[subject][week]) and
        "scores" in data[subject][week][idx] and
        data[subject][week][idx]["scores"]):
        
        # Get the most recent score entry
        latest_score = data[subject][week][idx]["scores"][-1]
        
        # Add feedback data
        latest_score["ai_feedback"] = {
            "feedback": feedback_data.get("feedback", ""),
            "hint": feedback_data.get("hint", "")
        }
    
    return data


def calculate_weighted_score(scores, last_practiced=None, decay_factor=0.1, forgetting_decay_factor=0.05):
    """
    Calculate a time-weighted score for a question based on score history,
    adjusted for time since last practice.
    
    This calculation is performed in memory and does not require a DB call
    once the score data is loaded.
    
    Args:
        scores: List of score objects {score, timestamp}.
        last_practiced: Timestamp (float/int) of the last practice session.
        decay_factor: How much to decay older scores (weights past performance).
        forgetting_decay_factor: How much the score decays due to inactivity.
        
    Returns:
        Adjusted weighted score (float) or None.
    """
    # --- Part 1: Calculate weighted score based on past performance ---
    if not scores:
        return None
    
    current_time = time.time()
    total_weight = 0
    total_weighted_score = 0
    
    for score_obj in scores:
        # Ensure score_obj is a dictionary and has the required keys
        if isinstance(score_obj, dict) and "score" in score_obj and "timestamp" in score_obj:
            score = score_obj["score"]
            timestamp = score_obj["timestamp"]
            
            # Calculate time difference in days
            time_diff_days = (current_time - timestamp) / (60 * 60 * 24) # Convert seconds to days
            
            # Exponential decay weight based on recency
            weight = math.exp(-decay_factor * time_diff_days)
            
            total_weighted_score += score * weight
            total_weight += weight
        else:
            # Log or handle malformed score objects if necessary
            print(f"Skipping malformed score object in calculate_weighted_score: {score_obj}")

    if total_weight <= 0:
         # Avoid division by zero if weights are negligible or no valid scores found
         return None 
    
    weighted_score = total_weighted_score / total_weight

    # --- Part 2: Apply decay based on time since last practice ---
    adjusted_score = weighted_score # Start with the weighted score
    
    if last_practiced is not None:
        try:
            time_since_last_practice_days = (current_time - last_practiced) / (60 * 60 * 24)
            
            # Ensure time difference isn't negative
            if time_since_last_practice_days < 0:
                time_since_last_practice_days = 0 
                
            # Calculate the forgetting multiplier
            # Ensure forgetting_decay_factor is non-negative
            if forgetting_decay_factor < 0: forgetting_decay_factor = 0 
            forgetting_multiplier = math.exp(-forgetting_decay_factor * time_since_last_practice_days)
            
            # Apply the forgetting decay
            adjusted_score = weighted_score * forgetting_multiplier

        except Exception as decay_error:
             print(f"Error applying forgetting decay in mongodb/queue_cards.py: {decay_error}")
             # If error during decay calculation, return the unadjusted weighted_score
             return weighted_score
    
    # Return the final adjusted score
    return adjusted_score


def update_single_question_score(data: Dict, subject: str, week: str, question_idx: int, score: int, user_answer: str = None, feedback_data: Dict = None, email: str = None) -> Dict:
    """
    Update a single question's score directly in MongoDB without rewriting the entire database.
    Also adds AI feedback if provided.
    
    Args:
        data: The data dictionary (for in-memory updates)
        subject: Subject name
        week: Week number (as string)
        question_idx: Index of the question
        score: Score value (1-5)
        user_answer: Optional user's answer to log
        feedback_data: Optional AI feedback data
        email: User's email (required for MongoDB update)
        
    Returns:
        Updated data dictionary
    """
    if not email:
        # If no email provided, fall back to regular update
        data = update_question_score(data, subject, week, question_idx, score, user_answer, email)
        return data
        
    try:
        collection = get_collection(QUEUE_CARDS_COLLECTION)
        
        # First update the in-memory data
        if subject in data and week in data[subject] and question_idx < len(data[subject][week]):
            # Get the current timestamp
            current_time = int(time.time())
            
            # Initialize scores list if it doesn't exist
            if "scores" not in data[subject][week][question_idx]:
                data[subject][week][question_idx]["scores"] = []
                
            # Create score entry
            score_entry = {
                "score": score,
                "timestamp": current_time
            }
            
            # Add user answer if provided
            if user_answer is not None:
                score_entry["user_answer"] = user_answer
                
            # Add AI feedback if provided
            if feedback_data is not None:
                score_entry["ai_feedback"] = {
                    "feedback": feedback_data.get("feedback", ""),
                    "hint": feedback_data.get("hint", "")
                }
                
            # Add the new score with timestamp and user answer
            data[subject][week][question_idx]["scores"].append(score_entry)
            
            # Update last practiced timestamp
            data[subject][week][question_idx]["last_practiced"] = current_time
            
            # Now update directly in MongoDB
            # Find the document containing this question
            query = {
                "email": email,
                "subject": subject,
                "week": week
            }
            
            # Get the document to find the correct batch
            doc = collection.find_one(query)
            if doc and "questions" in doc:
                questions = doc["questions"]
                
                # Find which batch contains our question
                batch_size = 100  # Same as in save_data
                batch_index = question_idx // batch_size
                question_index_in_batch = question_idx % batch_size
                
                # If the question is in a valid batch
                if batch_index < len(questions) // batch_size + 1:
                    # Update just this specific question's scores and last_practiced
                    update_path = f"questions.{question_index_in_batch}.scores"
                    last_practiced_path = f"questions.{question_index_in_batch}.last_practiced"
                    
                    # Update the document
                    result = collection.update_one(
                        {
                            "email": email,
                            "subject": subject,
                            "week": week,
                            # Ensure we're updating the right batch
                            "questions": {"$exists": True}
                        },
                        {
                            "$set": {
                                update_path: data[subject][week][question_idx]["scores"],
                                last_practiced_path: current_time,
                                "updated_at": current_time
                            }
                        }
                    )
                    
                    if result.modified_count == 0:
                        print(f"Warning: No document was updated for {subject}, week {week}, question {question_idx}")
                        # Fall back to full save if direct update fails
                        save_data(data, email)
                    else:
                        print(f"Successfully updated single question score for {subject}, week {week}, question {question_idx}")
                else:
                    print(f"Question index {question_idx} is out of bounds for batches")
                    # Fall back to full save if batch index is out of bounds
                    save_data(data, email)
            else:
                print(f"Document not found for {subject}, week {week}")
                # Create new document if it doesn't exist
                new_doc = {
                    "email": email,
                    "subject": subject,
                    "week": week,
                    "questions": [{"scores": [], "last_practiced": None}] * (question_idx + 1)
                }
                new_doc["questions"][question_idx] = {
                    "scores": data[subject][week][question_idx]["scores"],
                    "last_practiced": current_time
                }
                collection.insert_one(new_doc)
                print(f"Created new document for {subject}, week {week}")
                
    except Exception as e:
        print(f"Error updating single question: {str(e)}")
        # Fall back to full save if direct update fails
        save_data(data, email)
    
    return data
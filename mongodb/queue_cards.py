"""
MongoDB data access layer for queue cards.
Provides functions to load, save, and manipulate queue cards data.
"""
import time
from typing import Dict, List, Optional, Any

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
            ]
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
    Update the score for a specific question
    
    Args:
        data: The data dictionary
        subject: Subject name
        week: Week number (as string)
        question_idx: Index of the question
        score: Score value (0-10)
        user_answer: Optional user's answer to log
        email: User's email (optional)
        
    Returns:
        Updated data dictionary
    """
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
            
        # Add the new score with timestamp and user answer
        data[subject][week][question_idx]["scores"].append(score_entry)
        
        # Update last practiced timestamp
        data[subject][week][question_idx]["last_practiced"] = current_time
        
        # Save the updated data to MongoDB
        save_data(data, email)
    
    return data


def calculate_weighted_score(scores, decay_factor=0.1):
    """
    Calculate a time-weighted score for a question based on score history
    
    Args:
        scores: List of score objects with score and timestamp
        decay_factor: How much to decay older scores (higher = faster decay)
        
    Returns:
        Weighted score (float) or None if no scores available
    """
    import time
    import math
    
    if not scores:
        return None
    
    current_time = time.time()
    total_weight = 0
    total_weighted_score = 0
    
    for score_obj in scores:
        score = score_obj["score"]
        timestamp = score_obj["timestamp"]
        
        # Calculate time difference in days
        time_diff = (current_time - timestamp) / (60 * 60 * 24)  # Convert seconds to days
        
        # Exponential decay weight based on recency
        weight = math.exp(-decay_factor * time_diff)
        
        total_weighted_score += score * weight
        total_weight += weight
    
    if total_weight == 0:  # Avoid division by zero
        return None
        
    return total_weighted_score / total_weight
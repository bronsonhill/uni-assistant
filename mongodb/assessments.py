"""
MongoDB data access layer for assessments.
Provides functions to manage assessment data in MongoDB.
"""
import time
from typing import Dict, List, Optional, Any

from .connection import get_collection

# Collection name for assessments
ASSESSMENTS_COLLECTION = "assessments"


def load_assessments() -> Dict:
    """
    Load assessments data from MongoDB.
    
    Returns:
        Dict: Assessments data structure with a flat list under "assessments" key
    """
    collection = get_collection(ASSESSMENTS_COLLECTION)
    
    # Get the assessments document
    doc = collection.find_one({})
    
    if doc and "assessments" in doc:
        return doc
    
    return {"assessments": []}


def save_assessments(assessments_data: Dict) -> None:
    """
    Save assessments data to MongoDB.
    
    Args:
        assessments_data (Dict): Assessments data structure with a flat list under "assessments" key
    """
    collection = get_collection(ASSESSMENTS_COLLECTION)
    
    # Clear existing data
    collection.delete_many({})
    
    # Add updated_at timestamp if not present
    if "updated_at" not in assessments_data:
        assessments_data["updated_at"] = int(time.time())
    
    # Insert the assessments data as a single document
    collection.insert_one(assessments_data)


def add_assessment(assessments_data: Dict, assessment: Dict) -> Dict:
    """
    Add a new assessment to the data.
    
    Args:
        assessments_data: The assessments dictionary with "assessments" key
        assessment: Complete assessment object to add
        
    Returns:
        Updated assessments data dictionary
    """
    # Ensure assessments list exists
    if "assessments" not in assessments_data:
        assessments_data["assessments"] = []
    
    # Add the assessment to the list
    assessments_data["assessments"].append(assessment)
    
    # Save the updated data to MongoDB
    save_assessments(assessments_data)
    
    return assessments_data


def update_assessment(assessments_data: Dict, assessment_id: str, updated_fields: Dict) -> Dict:
    """
    Update an existing assessment.
    
    Args:
        assessments_data: The assessments dictionary with "assessments" key
        assessment_id: ID of the assessment to update
        updated_fields: Dictionary of fields to update
        
    Returns:
        Updated assessments data dictionary
    """
    if "assessments" not in assessments_data:
        return assessments_data
    
    # Find the assessment with the given ID
    for i, assessment in enumerate(assessments_data["assessments"]):
        if assessment.get("id") == assessment_id:
            # Update the fields
            assessments_data["assessments"][i].update(updated_fields)
            
            # Add updated timestamp
            assessments_data["updated_at"] = int(time.time())
            
            # Save the updated data to MongoDB
            save_assessments(assessments_data)
            break
    
    return assessments_data


def delete_assessment(assessments_data: Dict, assessment_id: str) -> Dict:
    """
    Delete an assessment from the data.
    
    Args:
        assessments_data: The assessments dictionary with "assessments" key
        assessment_id: ID of the assessment to delete
        
    Returns:
        Updated assessments data dictionary
    """
    if "assessments" not in assessments_data:
        return assessments_data
    
    # Filter out the assessment with the given ID
    assessments_data["assessments"] = [
        a for a in assessments_data["assessments"] 
        if a.get("id") != assessment_id
    ]
    
    # Add updated timestamp
    assessments_data["updated_at"] = int(time.time())
    
    # Save the updated data to MongoDB
    save_assessments(assessments_data)
    
    return assessments_data
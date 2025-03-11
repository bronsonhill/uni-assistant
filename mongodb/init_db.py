"""
MongoDB initialization script.
Migrates data from JSON files to MongoDB.
"""
import json
import os
import time

from .connection import get_collection
from .queue_cards import save_data as save_queue_cards

def migrate_json_to_mongodb():
    """
    Migrate data from JSON files to MongoDB.
    Will only migrate if MongoDB is empty to prevent duplicates.
    """
    # Migrate queue cards
    migrate_queue_cards()
    
    # Migrate users (if needed)
    migrate_users()
    
    # Migrate assessments (if needed)
    migrate_assessments()
    
    print("Migration complete.")


def migrate_queue_cards():
    """Migrate queue cards data from JSON to MongoDB."""
    collection = get_collection("queue_cards")
    
    # Check if the collection already has data
    if collection.count_documents({}) > 0:
        print("Queue cards collection already has data. Skipping migration.")
        return
    
    # Check if the JSON file exists
    if not os.path.exists("queue_cards.json"):
        print("No queue_cards.json file found. Skipping migration.")
        return
    
    # Load data from JSON
    try:
        with open("queue_cards.json", "r") as f:
            data = json.load(f)
        
        # Save data to MongoDB
        save_queue_cards(data)
        
        print(f"Migrated queue cards to MongoDB: {len(data)} subjects")
    except Exception as e:
        print(f"Error migrating queue cards: {str(e)}")


def migrate_users():
    """Migrate users data from JSON to MongoDB."""
    collection = get_collection("users")
    
    # Check if the collection already has data
    if collection.count_documents({}) > 0:
        print("Users collection already has data. Skipping migration.")
        return
    
    # Check if the JSON file exists
    if not os.path.exists("users.json"):
        print("No users.json file found. Skipping migration.")
        return
    
    # Load data from JSON
    try:
        with open("users.json", "r") as f:
            users_data = json.load(f)
        
        # Insert each user as a document
        for email, user_data in users_data.items():
            # Add the email as a field in the document
            user_document = {"email": email}
            user_document.update(user_data)
            
            collection.insert_one(user_document)
        
        print(f"Migrated users to MongoDB: {len(users_data)} users")
    except Exception as e:
        print(f"Error migrating users: {str(e)}")


def migrate_assessments():
    """Migrate assessments data from JSON to MongoDB."""
    collection = get_collection("assessments")
    
    # Check if the collection already has data
    if collection.count_documents({}) > 0:
        print("Assessments collection already has data. Skipping migration.")
        return
    
    # Check if the JSON file exists
    if not os.path.exists("assessments.json"):
        print("No assessments.json file found. Skipping migration.")
        return
    
    # Load data from JSON
    try:
        with open("assessments.json", "r") as f:
            assessments_data = json.load(f)
        
        # Add updated_at timestamp to the document
        assessments_data["updated_at"] = int(time.time())
        
        # Insert the document as is - it already has the correct structure
        collection.insert_one(assessments_data)
        
        assessment_count = len(assessments_data.get("assessments", []))
        print(f"Migrated assessments to MongoDB: {assessment_count} assessments")
    except Exception as e:
        print(f"Error migrating assessments: {str(e)}")


if __name__ == "__main__":
    migrate_json_to_mongodb()
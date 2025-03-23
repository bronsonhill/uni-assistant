"""
Common vector store utilities shared across modules.
"""
from typing import Any

def extract_vector_store_id(vector_store_id: Any) -> str:
    """
    Safely extract a vector store ID from various formats
    
    Args:
        vector_store_id: The vector store ID in any format (dict, JSON string, or plain string)
        
    Returns:
        Extracted vector store ID as string
    """
    # Case 1: None value
    if not vector_store_id:
        return None
    
    # Case 2: Dictionary with id field
    if isinstance(vector_store_id, dict) and "id" in vector_store_id:
        return vector_store_id["id"]
    
    # Case 3: JSON string in format: "{\"id\":\"vs_xxx\",\"name\":\"Subject_Week\"}"
    if isinstance(vector_store_id, str) and vector_store_id.startswith("{") and "id" in vector_store_id:
        try:
            import json
            parsed = json.loads(vector_store_id)
            if isinstance(parsed, dict) and "id" in parsed:
                return parsed["id"]
        except Exception as e:
            print(f"Error parsing vector store JSON: {e}")
            # Fall through to return the original string
    
    # Case 4: Plain string ID or fallback
    return vector_store_id 
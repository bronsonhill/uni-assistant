"""
MongoDB integration package for Study Legend.
Provides data access layers for the application.
"""

# Re-export key functions from submodules
from .connection import (
    get_mongodb_client,
    get_database,
    get_collection
)

from .queue_cards import (
    load_data,
    save_data,
    add_question,
    delete_question,
    update_question,
    update_question_score,
    calculate_weighted_score
)

from .users import (
    load_users,
    save_users,
    get_user,
    add_user,
    delete_user,
    update_user_field
)

from .assessments import (
    load_assessments,
    save_assessments,
    add_assessment,
    update_assessment,
    delete_assessment
)

from .chat_history import (
    save_chat_session,
    get_chat_sessions,
    get_chat_session,
    delete_chat_session,
    rename_chat_session,
    CHAT_TYPE_TUTOR,
    CHAT_TYPE_PRACTICE
)

from .init_db import migrate_json_to_mongodb

__all__ = [
    # Connection
    'get_mongodb_client',
    'get_database',
    'get_collection',
    
    # Queue cards
    'load_data',
    'save_data',
    'add_question',
    'delete_question',
    'update_question',
    'update_question_score',
    'calculate_weighted_score',
    
    # Users
    'load_users',
    'save_users',
    'get_user',
    'add_user',
    'delete_user',
    'update_user_field',
    
    # Assessments
    'load_assessments',
    'save_assessments',
    'add_assessment',
    'update_assessment',
    'delete_assessment',
    
    # Chat History
    'save_chat_session',
    'get_chat_sessions',
    'get_chat_session', 
    'delete_chat_session',
    'rename_chat_session',
    'CHAT_TYPE_TUTOR',
    'CHAT_TYPE_PRACTICE',
    
    # Initialization
    'migrate_json_to_mongodb'
]
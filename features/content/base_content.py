"""
Base module for content modules in Study Legend.

This module provides common imports and functionality for all content modules.
"""
import streamlit as st
import sys
import os
import datetime
from typing import Optional, Dict, List, Any, Tuple, Callable

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Common imports from parent modules
import Home
from paywall import check_subscription, display_subscription_status

# Function to initialize data in session state
def init_data(email: Optional[str] = None) -> None:
    """Initialize data in session state if not already present."""
    if "data" not in st.session_state:
        st.session_state.data = Home.load_data(email=email)

def init_rag_manager(email: Optional[str] = None) -> None:
    """Initialize RAG manager in session state if not already present."""
    if "rag_manager" not in st.session_state:
        st.session_state.rag_manager = Home.init_rag_manager(email=email)

def get_user_email() -> Optional[str]:
    """Get the user's email from session state."""
    return st.session_state.get("email")

def require_premium(require: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Check if the user has premium access.
    
    Args:
        require: If True, will redirect non-premium users
        
    Returns:
        Tuple of (is_subscribed, user_email)
    """
    return check_subscription(required=require)

def format_date(date_str: str) -> str:
    """Format a date string for display."""
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return "Not specified"
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

# Import st-paywall directly instead of custom paywall module
try:
    from st_paywall import add_auth
except ImportError:
    # Fallback if there's an issue with st_paywall
    def add_auth(required=False, login_button_text="Login", login_button_color="primary", login_sidebar=False):
        if "email" not in st.session_state:
            st.session_state.email = "test@example.com"  # Fallback to test user
        return True  # Always return subscribed in fallback mode

# Common imports from parent modules
import Home

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
    # Use st-paywall's add_auth directly
    is_subscribed = add_auth(required=require)
    user_email = st.session_state.get("email")
    
    return is_subscribed, user_email

def format_date(date_str: str) -> str:
    """Format a date string for display."""
    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return "Not specified"
"""
Base content module providing shared functionality for all content modules.
"""
import streamlit as st
from typing import Optional

def get_user_email() -> Optional[str]:
    """
    Get the current user's email from the session state.
    
    Returns:
        Optional[str]: The user's email if authenticated, None otherwise
    """
    return st.session_state.get("email") 
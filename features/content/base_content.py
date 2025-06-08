"""
Base module for content modules in Study Legend.

This module provides common imports and functionality for all content modules.
"""
import streamlit as st
import sys
import os
import datetime
from typing import Optional, Dict, List, Any, Tuple, Callable
from st_paywall import add_auth

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from mongodb package
from mongodb.queue_cards import load_data

# Function to initialize data in session state
def init_data(email: Optional[str] = None) -> None:
    """Initialize data in session state if not already present."""
    if "data" not in st.session_state:
        st.session_state.data = load_data(email=email)

def init_rag_manager(email: Optional[str] = None) -> None:
    """Initialize RAG manager in session state if not already present."""
    if "rag_manager" not in st.session_state:
        st.session_state.rag_manager = Home.init_rag_manager(email=email)

def get_user_email() -> Optional[str]:
    """Get the user's email from session state."""
    return st.session_state.get("email")

def check_auth_for_action(feature_name: str) -> bool:
    """
    Check if the user is authenticated for performing actions.
    
    Args:
        feature_name: Name of the feature requiring auth
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None and user_email != ""
    
    if is_authenticated:
        return True
        
    # Not authenticated - show message
    st.warning(f"Please sign in to use the {feature_name} feature.")
    
    # No need to add login button here as st-paywall handles it
    return False

def require_premium(require_auth=True, require_premium=True) -> Tuple[bool, Optional[str]]:
    """
    Check if the user has premium access.
    
    Args:
        require_auth (bool): If True, will block actions for unauthenticated users
        require_premium (bool): If True, will block actions for non-premium users
        
    Returns:
        Tuple of (is_subscribed, user_email)
    """
    # Check if user is authenticated using session state
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None and user_email != ""
    
    # If not logged in but require_auth is True, show login message
    if require_auth and not is_authenticated:
        st.warning("Please sign in to use this feature.")
        # st-paywall will handle login button
    
    # Check subscription status using session state
    is_subscribed = False
    if is_authenticated and require_premium:
        is_subscribed = st.session_state.get("user_subscribed", False)
        if not is_subscribed:
            st.warning("This feature requires a premium subscription.")
            # Show premium benefits
            st.markdown("### 🌟 Upgrade to Premium for these benefits:")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("✅ **Unlimited AI-generated questions**")
                st.markdown("✅ **Advanced question filtering**")
                st.markdown("✅ **Detailed progress analytics**")
            with col2:
                st.markdown("✅ **Priority support**")
                st.markdown("✅ **Assessment extraction from documents**")
                st.markdown("✅ **Export/import functionality**")
    
    return is_subscribed, user_email
            
def show_preview_mode(feature_name: str, description: str = None):
    """
    Show a message indicating that the user is in preview mode.
    
    Args:
        feature_name: Name of the feature being previewed
        description: Optional description text
    """
    st.info(f"🔍 **Preview Mode: {feature_name}**")
    
    if description:
        st.markdown(description)
        
    st.markdown("""
    <div class="element-container">
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <p>Sign in to save your progress and access all features.</p>
            <a href="/?auth=login" target="_self" style="background-color: #FF6F00; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 10px;">
                Sign in to Study Legend
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

def format_date(date_str: str) -> str:
    """Format a date string into a human-readable format."""
    try:
        date_obj = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime("%B %d, %Y")
    except:
        return date_str
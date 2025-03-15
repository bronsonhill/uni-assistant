"""
Centralized setup module for feature pages in Study Legend.

This module provides common functionality used by all feature pages,
including page configuration, authentication, and navigation setup.
"""
import streamlit as st
import sys
import os
from typing import Optional, Tuple, Callable

# Add parent directory to path (needed when imported from features/)
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from common_nav import setup_navigation
from paywall import check_subscription, display_subscription_status

def setup_feature_page(display_subscription: bool = True, required: bool = False) -> None:
    """
    Set up a feature page with standard configuration.
    
    This function:
    1. Configures the Streamlit page
    2. Initializes authentication
    3. Sets up navigation
    
    Args:
        display_subscription: Whether to display subscription status
        required: Whether subscription is required for this page
    """
    # Set the page config (should be the same across all pages)
    st.set_page_config(
        page_title="Study Legend AI", 
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check authentication once, ensuring no duplicate buttons
    if "auth_initialized" not in st.session_state:
        # First run of any page, initialize auth
        is_subscribed, user_email = check_subscription(required=required)
        st.session_state.auth_initialized = True
    
    # Display subscription status in sidebar without showing duplicate buttons
    if display_subscription and "email" in st.session_state:
        display_subscription_status()
    
    # Create and run the navigation menu
    pg = setup_navigation()
    pg.run()
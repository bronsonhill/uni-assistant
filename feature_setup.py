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
from st_paywall import add_auth

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
    
    # Ensure login button is always in the sidebar for unauthenticated users
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None and user_email != ""
    
    if not is_authenticated:
        # Only show login button without disrupting page functionality
        add_auth(
            required=False,  # Don't make login required
            login_button_text="Login to Study Legend",
            login_button_color="#FF6F00",  # Match theme color
            login_sidebar=True  # Always show in sidebar
        )
    
    # Check authentication once, ensuring no duplicate buttons
    if "auth_initialized" not in st.session_state:
        # First run of any page, initialize auth
        is_subscribed = add_auth(
            required=required,
            login_button_text="Login to Study Legend",
            login_button_color="#FF6F00"
        )
        st.session_state.user_subscribed = is_subscribed
        st.session_state.auth_initialized = True
    
    # Display subscription status in sidebar without showing duplicate buttons
    if display_subscription and "email" in st.session_state and user_email != "":
        with st.sidebar.expander("💳 Subscription Status", expanded=True):
            if st.session_state.get("user_subscribed", False):
                st.success("✅ Premium subscription active")
                if st.session_state.get("subscriptions"):
                    try:
                        subscription = st.session_state.subscriptions.data[0]
                        if subscription.get("current_period_end"):
                            import datetime
                            end_timestamp = subscription["current_period_end"]
                            end_date = datetime.datetime.fromtimestamp(end_timestamp)
                            days_remaining = (end_date - datetime.datetime.now()).days
                            st.info(f"⏱️ {days_remaining} days remaining")
                    except Exception as e:
                        pass
                
                # Add link to Account page
                st.markdown("[View account details](/7_👤_Account)", unsafe_allow_html=True)
            else:
                st.warning("❌ No active subscription")
                
                # Add link to Account page
                st.markdown("[View account details](/render_account)", unsafe_allow_html=True)
    
    # Create and run the navigation menu
    pg = setup_navigation()
    pg.run()
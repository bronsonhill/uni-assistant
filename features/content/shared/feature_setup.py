"""
Shared feature setup module for Study Legend.

This module provides common functionality for feature pages,
including authentication and subscription status display.
Navigation is handled centrally by Home.py.
"""
import streamlit as st
from st_paywall import add_auth

def setup_feature(display_subscription: bool = True, required: bool = False) -> None:
    """
    Set up a feature with standard configuration.
    
    This function:
    1. Initializes authentication
    2. Displays subscription status if requested
    
    Args:
        display_subscription: Whether to display subscription status
        required: Whether subscription is required for this page
    """
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
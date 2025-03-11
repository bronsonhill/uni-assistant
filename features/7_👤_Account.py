import streamlit as st
import sys
import os
from common_nav import setup_navigation

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from paywall import check_subscription, display_subscription_status, handle_oauth_login

# Set the page config (should be the same across all pages)
st.set_page_config(
    page_title="Study Legend AI", 
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Explicitly check for OAuth login first
handle_oauth_login()

# Check authentication once, ensuring no duplicate buttons
if "auth_initialized" not in st.session_state:
    # First run of any page, initialize auth
    is_subscribed, user_email = check_subscription(required=False)
    st.session_state.auth_initialized = True
else:
    # Auth already initialized, don't show login buttons again
    pass

# Display subscription status in sidebar without showing duplicate buttons
if "email" in st.session_state:
    display_subscription_status()

# Create and run the navigation menu
pg = setup_navigation()
pg.run()
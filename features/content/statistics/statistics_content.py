"""
Statistics content module.

This module provides statistics and analytics about the user's study content and progress.
"""
import streamlit as st
import sys
import os
from st_paywall import add_auth

# Add parent directory to path so we can import from parent modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import from Home and base content
import Home
from features.content.base_content import check_auth_for_action, show_preview_mode, get_user_email, init_data

# Import from statistics modules
from features.content.statistics.statistics_core import (
    get_user_statistics,
    get_content_statistics,
    get_practice_statistics
)
from features.content.statistics.statistics_ui import (
    display_overview_stats,
    display_content_stats,
    display_practice_stats
)

def run():
    """Main statistics page content - this gets run by the navigation system"""
    # Check if user is authenticated and subscribed using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    st.title("📊 Statistics")
    st.markdown("""
    View your study statistics and track your progress. Get insights into your content creation,
    practice performance, and overall engagement.
    """)

    # Initialize data if needed
    init_data(user_email)

    # Get statistics data
    user_stats = get_user_statistics(user_email)
    practice_stats = get_practice_statistics(user_email)
    content_stats = get_content_statistics(user_email)

    # Display statistics sections
    display_overview_stats(user_stats)
    display_practice_stats(practice_stats) 
    display_content_stats(content_stats)
"""
Settings content module.

This module integrates the Settings functionality components and manages the UI.
"""
import streamlit as st
import sys
import os

# Add parent directory to path so we can import from parent modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Import from settings modules
from features.content.settings.settings_core import init_settings_state
from features.content.settings.settings_ui import (
    display_score_settings,
    handle_settings_save
)

def run():
    """Main settings page content - this gets run by the navigation system"""
    st.title("⚙️ Application Settings")
    
    # Check if user is logged in using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None

    if not is_authenticated:
        st.warning("Please log in to manage your settings.")
        return

    # Initialize settings state if needed
    init_settings_state()

    # Display settings UI
    display_score_settings(user_email) 
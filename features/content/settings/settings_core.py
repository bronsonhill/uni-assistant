"""
Settings core module.

This module handles the core business logic and state management for settings.
"""
import streamlit as st
from typing import Dict, Optional

# Default values for settings
DEFAULT_DECAY_FACTOR = 0.1
DEFAULT_FORGETTING_DECAY_FACTOR = 0.05

def init_settings_state() -> None:
    """Initialize settings state variables if they don't exist"""
    if "settings_initialized" not in st.session_state:
        st.session_state.settings_initialized = True
        st.session_state.decay_factor = DEFAULT_DECAY_FACTOR
        st.session_state.forgetting_decay_factor = DEFAULT_FORGETTING_DECAY_FACTOR

def get_current_settings(user_email: str) -> Dict[str, float]:
    """Get current settings for the user"""
    try:
        from mongodb import get_user_score_settings
        current_settings = get_user_score_settings(user_email)
        return {
            "decay_factor": current_settings.get("decay_factor", DEFAULT_DECAY_FACTOR),
            "forgetting_decay_factor": current_settings.get("forgetting_decay_factor", DEFAULT_FORGETTING_DECAY_FACTOR)
        }
    except Exception as e:
        st.error(f"Error fetching current score settings: {e}")
        return {
            "decay_factor": DEFAULT_DECAY_FACTOR,
            "forgetting_decay_factor": DEFAULT_FORGETTING_DECAY_FACTOR
        }

def save_settings(user_email: str, new_settings: Dict[str, float]) -> bool:
    """Save new settings for the user"""
    try:
        from mongodb import update_user_score_settings
        return update_user_score_settings(user_email, new_settings)
    except Exception as e:
        st.error(f"An error occurred while saving settings: {e}")
        return False 
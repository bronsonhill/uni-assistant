"""
Settings feature page.

This page allows users to configure application settings and preferences.
"""
import streamlit as st
from typing import Dict
from features.content.shared.feature_setup import setup_feature

# Import directly from mongodb package
try:
    from mongodb import get_user_score_settings, update_user_score_settings
except ImportError as e:
    st.error(f"Failed to import MongoDB functions: {e}. Ensure the mongodb package is correctly installed and configured.")
    st.stop()

# Default values (can be imported from a shared config if preferred)
DEFAULT_DECAY_FACTOR = 0.1
DEFAULT_FORGETTING_DECAY_FACTOR = 0.05

def render():
    """Render the settings page content."""
    # Set up the page with standard configuration
    # This is a free feature that displays subscription status
    setup_feature(display_subscription=True, required=False)
    
    st.title("⚙️ Application Settings")
    
    # Check if user is logged in using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None

    if not is_authenticated:
        st.warning("Please log in to manage your settings.")
        return

    # --- Score Calculation Settings ---
    st.subheader("Score Calculation Settings")
    st.markdown("""
    Adjust the factors used to calculate your weighted score for questions.
    These settings affect how past performance and time since last practice influence your current score.
    """)

    # Get current settings for the logged-in user
    try:
        current_settings = get_user_score_settings(user_email)
        current_decay = current_settings.get("decay_factor", DEFAULT_DECAY_FACTOR)
        current_forgetting = current_settings.get("forgetting_decay_factor", DEFAULT_FORGETTING_DECAY_FACTOR)
    except Exception as e:
        st.error(f"Error fetching current score settings: {e}")
        # Fallback to defaults if fetch fails
        current_decay = DEFAULT_DECAY_FACTOR
        current_forgetting = DEFAULT_FORGETTING_DECAY_FACTOR

    # Use columns for layout
    col1, col2 = st.columns(2)

    with col1:
        new_decay = st.number_input(
            "Performance Decay Factor (0.0-1.0)",
            min_value=0.0, max_value=1.0,
            value=float(current_decay), # Ensure value is float
            step=0.01,
            format="%.2f",
            key="settings_decay_factor", # Add unique key
            help="Controls how quickly older scores lose influence. Higher value = faster decay. Default: 0.1"
        )

    with col2:
        new_forgetting = st.number_input(
            "Forgetting Decay Factor (0.0-1.0)",
            min_value=0.0, max_value=1.0,
            value=float(current_forgetting), # Ensure value is float
            step=0.01,
            format="%.2f",
            key="settings_forgetting_factor", # Add unique key
            help="Controls how quickly the score decreases over time since last practiced. Higher value = faster decay. Default: 0.05"
        )

    # Save button
    if st.button("💾 Save Score Settings", key="save_score_settings"):
        new_settings = {"decay_factor": new_decay, "forgetting_decay_factor": new_forgetting}
        try:
            success = update_user_score_settings(user_email, new_settings)
            if success:
                # Check if settings actually changed or just matched existing
                if new_decay == current_decay and new_forgetting == current_forgetting:
                    st.info("Settings are already up to date.")
                else:
                    st.success("Score settings saved successfully!")
            else:
                st.error("Failed to save score settings. User might not exist or database error.")
        except Exception as e:
            st.error(f"An error occurred while saving settings: {e}")

    st.markdown("---")
    # Add placeholders for future settings sections
    # st.subheader("Other Settings")
    # st.info("More settings coming soon!") 
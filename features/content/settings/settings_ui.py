"""
Settings UI module.

This module handles the display and interaction of settings components.
"""
import streamlit as st
from typing import Dict
from features.content.settings.settings_core import get_current_settings, save_settings

# Predefined options for memory settings
MEMORY_OPTIONS = {
    "You have poor memory and need to study a lot (0.12)": 0.12,
    "You have average memory and need to study moderately (0.07)": 0.07,
    "You have good memory and need to study moderately (0.03)": 0.03,
    "You are a Study Legend and can memorize things with ease (recommended 0.01)": 0.01,
    "Custom Value": None
}

# Predefined options for performance decay
PERFORMANCE_OPTIONS = {
    "Very Stable (0.05)": 0.05,
    "Stable (0.1)": 0.1,
    "Balanced (0.25)": 0.25,
    "Quick Decay (0.5)": 0.5,
    "Custom Value": None
}

def get_closest_option(value: float, options: Dict[str, float]) -> str:
    """Find the closest predefined option to the given value"""
    if value is None:
        return "Custom Value"
    
    # Remove the "Custom Value" option for comparison
    valid_options = {k: v for k, v in options.items() if v is not None}
    if not valid_options:
        return "Custom Value"
    
    # Find the closest option
    closest_key = min(valid_options.items(), key=lambda x: abs(x[1] - value))[0]
    return closest_key

def display_score_settings(user_email: str) -> None:
    """Display the score calculation settings section"""
    st.subheader("Score Calculation Settings")
    st.markdown("""
    Adjust the factors used to calculate your weighted score for questions.
    These settings affect how past performance and time since last practice influence your current score.
    """)

    # Get current settings
    current_settings = get_current_settings(user_email)
    
    # Use columns for layout
    col1, col2 = st.columns(2)

    with col2:
        st.markdown("#### Performance Decay Factor")
        st.markdown("""
        Controls how quickly older scores lose influence on your current score.
        - Lower values (e.g., 0.05) = scores remain stable longer
        - Higher values (e.g., 0.2) = scores decay more quickly
        """)
        
        # Find the closest predefined option for performance decay
        current_performance = get_closest_option(
            float(current_settings["decay_factor"]), 
            PERFORMANCE_OPTIONS
        )
        
        performance_choice = st.selectbox(
            "Select Performance Decay",
            options=list(PERFORMANCE_OPTIONS.keys()),
            key="performance_choice",
            index=list(PERFORMANCE_OPTIONS.keys()).index(current_performance),
            help="Choose a predefined setting or select Custom Value to input your own"
        )
        
        if PERFORMANCE_OPTIONS[performance_choice] is None:
            new_decay = st.number_input(
                "Custom Performance Decay Factor (0.0-1.0)",
                min_value=0.0, max_value=1.0,
                value=float(current_settings["decay_factor"]),
                step=0.01,
                format="%.2f",
                key="settings_decay_factor",
                help="Controls how quickly older scores lose influence. Higher value = faster decay."
            )
        else:
            new_decay = PERFORMANCE_OPTIONS[performance_choice]

    with col1:
        st.markdown("#### Forgetting Decay Factor")
        st.markdown("""
        Controls how quickly your score decreases over time since last practiced.
        - Lower values (e.g., 0.05) = your score decreases slowly
        - Higher values (e.g., 0.2) = your score decreases quickly
        """)
        
        # Find the closest predefined option for memory setting
        current_memory = get_closest_option(
            float(current_settings["forgetting_decay_factor"]), 
            MEMORY_OPTIONS
        )
        
        memory_choice = st.selectbox(
            "Select Memory Setting",
            options=list(MEMORY_OPTIONS.keys()),
            key="memory_choice",
            index=list(MEMORY_OPTIONS.keys()).index(current_memory),
            help="Choose a predefined setting or select Custom Value to input your own"
        )
        
        if MEMORY_OPTIONS[memory_choice] is None:
            new_forgetting = st.number_input(
                "Custom Forgetting Decay Factor (0.0-1.0)",
                min_value=0.0, max_value=1.0,
                value=float(current_settings["forgetting_decay_factor"]),
                step=0.01,
                format="%.2f",
                key="settings_forgetting_factor",
                help="Controls how quickly the score decreases over time since last practiced. Higher value = faster decay."
            )
        else:
            new_forgetting = MEMORY_OPTIONS[memory_choice]

    # Save button
    if st.button("💾 Save Score Settings", key="save_score_settings"):
        handle_settings_save(user_email, new_decay, new_forgetting, current_settings)

def handle_settings_save(user_email: str, new_decay: float, new_forgetting: float, current_settings: Dict[str, float]) -> None:
    """Handle saving of new settings"""
    new_settings = {
        "decay_factor": new_decay,
        "forgetting_decay_factor": new_forgetting
    }
    
    if save_settings(user_email, new_settings):
        # Check if settings actually changed or just matched existing
        if new_decay == current_settings["decay_factor"] and new_forgetting == current_settings["forgetting_decay_factor"]:
            st.info("Settings are already up to date.")
        else:
            st.success("Score settings saved successfully!")
    else:
        st.error("Failed to save score settings. User might not exist or database error.") 
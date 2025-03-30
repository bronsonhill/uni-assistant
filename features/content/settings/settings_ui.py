"""
Settings UI module.

This module handles the display and interaction of settings components.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from typing import Dict
from features.content.settings.settings_core import get_current_settings, save_settings

# Predefined options for memory settings
MEMORY_OPTIONS = {
    "You have poor memory and need to study a lot (0.12)": 0.12,
    "You have average memory and need to study moderately (0.07)": 0.07,
    "You have good memory and need to study moderately (0.03)": 0.03,
    "You are a Study Legend (recommended 0.01)": 0.01,
    "Custom Value": None
}

# Predefined options for performance decay
PERFORMANCE_OPTIONS = {
    "Very careful (0.05)": 0.05,
    "Somewhat careful (0.1)": 0.1,
    "Meh (0.25)": 0.25,
    "Careless (0.5)": 0.5,
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

def create_decay_visualization(decay_factor: float, forgetting_factor: float) -> None:
    """Create a visualization of the decay curves over 30 days"""
    days = np.arange(0, 31)
    
    # Calculate decay curves
    # Care Factor (weight) decays from 1 to 0
    care_factor_decay = np.exp(-decay_factor * days)
    # Big Brain Factor (score) decays from 5 to 0
    big_brain_decay = 5 * np.exp(-forgetting_factor * days)
    
    # Create the plot with secondary y-axis
    fig = go.Figure()
    
    # Add Care Factor curve (weight)
    fig.add_trace(go.Scatter(
        x=days,
        y=care_factor_decay,
        name='Care Factor (Weight)',
        line=dict(color='#1f77b4', width=2),
        hovertemplate='Day: %{x}<br>Weight: %{y:.2f}<extra></extra>'
    ))
    
    # Add Big Brain Factor curve (score)
    fig.add_trace(go.Scatter(
        x=days,
        y=big_brain_decay,
        name='Big Brain Factor (Score)',
        line=dict(color='#ff7f0e', width=2),
        yaxis='y2',
        hovertemplate='Day: %{x}<br>Score: %{y:.2f}/5<extra></extra>'
    ))
    
    # Update layout with secondary y-axis
    fig.update_layout(
        title='Score and Weight Decay Over Time',
        xaxis_title='Days Since Last Practice',
        yaxis=dict(
            title='Weight (0-1)',
            range=[0, 1],
            side='left',
            showgrid=True,
            gridcolor='lightgrey'
        ),
        yaxis2=dict(
            title='Score (0-5)',
            range=[0, 5],
            side='right',
            overlaying='y',
            showgrid=False
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.8
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

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
        st.markdown("#### Care Factor")
        st.markdown("""
        How confident do you want to be that you know the material?  
        - Lower values (e.g., 0.05) = a higher score is harder to achieve
        - Higher values (e.g., 0.2) = a higher score is easier to achieve
        """)
        
        # Find the closest predefined option for performance decay
        current_performance = get_closest_option(
            float(current_settings["decay_factor"]), 
            PERFORMANCE_OPTIONS
        )
        
        performance_choice = st.selectbox(
            "Select Care Factor",
            options=list(PERFORMANCE_OPTIONS.keys()),
            key="performance_choice",
            index=list(PERFORMANCE_OPTIONS.keys()).index(current_performance),
            help="Choose a predefined setting or select Custom Value to input your own"
        )
        
        if PERFORMANCE_OPTIONS[performance_choice] is None:
            new_decay = st.number_input(
                "Custom Care Factor (0.0-1.0)",
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
        st.markdown("#### Big Brain Factor")
        st.markdown("""
        How big is your brain? This controls how quickly your score decreases over time since last practiced, accounting for forgetting things over time.
        - Lower values (e.g., 0.05) = you have a big brain and can remember things for a long time
        - Higher values (e.g., 0.2) = your have a small brain and need to practice more often
        """)
        
        # Find the closest predefined option for memory setting
        current_memory = get_closest_option(
            float(current_settings["forgetting_decay_factor"]), 
            MEMORY_OPTIONS
        )
        
        memory_choice = st.selectbox(
            "Select Big Brain Factor",
            options=list(MEMORY_OPTIONS.keys()),
            key="memory_choice",
            index=list(MEMORY_OPTIONS.keys()).index(current_memory),
            help="Choose a predefined setting or select Custom Value to input your own"
        )
        
        if MEMORY_OPTIONS[memory_choice] is None:
            new_forgetting = st.number_input(
                "Custom Big Brain Factor (0.0-1.0)",
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
    
    # Add visualization section
    st.markdown("### Score Decay Visualization")
    st.markdown("""
    This graph shows how your scores will decay over time based on your current settings:
    - **Care Factor** (blue): How quickly older performance scores lose influence
    - **Big Brain Factor** (orange): How quickly your score decreases due to time since last practiced
    """)
    create_decay_visualization(new_decay, new_forgetting)

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
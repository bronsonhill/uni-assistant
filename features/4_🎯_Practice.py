"""
Practice feature page.

This page allows users to test their knowledge with their created questions.
Users can practice all questions or filter by subject and week.
"""
import sys
import os
import streamlit as st

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.content.shared.feature_setup import setup_feature

def render():
    """Render the practice page content."""
    # Set up the page with standard configuration
    # This is a free feature that displays subscription status
    setup_feature(display_subscription=True, required=False)
    
    st.title("🎯 Practice")
    # Add your practice page content here

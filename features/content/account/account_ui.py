"""
Account feature page.

This page provides account management functionality for users.
"""
import streamlit as st
from features.content.shared.feature_setup import setup_feature

def render():
    """Render the account page content."""
    # Set up the page with standard configuration
    # For account page, we display subscription status
    setup_feature(display_subscription=True, required=False)
    
    st.title("👤 Account")
    
    # Add your account page content here
    st.subheader("Account Settings")
    
    # Profile section
    with st.expander("Profile Information", expanded=True):
        name = st.text_input("Name", value="John Doe")
        email = st.text_input("Email", value="john@example.com", disabled=True)
        
        if st.button("Update Profile"):
            st.success("Profile updated successfully!")
    
    # Subscription section
    with st.expander("Subscription", expanded=True):
        st.write("Current Plan: Premium")
        st.write("Next billing date: April 15, 2024")
        
        if st.button("Manage Subscription"):
            st.info("Redirecting to subscription management...")
    
    # Preferences section
    with st.expander("Preferences"):
        theme = st.selectbox("Theme", ["Light", "Dark", "System"])
        notifications = st.checkbox("Enable email notifications", value=True)
        
        if st.button("Save Preferences"):
            st.success("Preferences saved successfully!") 
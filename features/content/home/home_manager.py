import streamlit as st
from typing import Optional
from .home_content import HomeContent, UserStatsDisplay, QuickActions

class HomeManager:
    def __init__(self, user_service, analytics_service):
        self.user_service = user_service
        self.analytics_service = analytics_service
        self.content = HomeContent(user_service, analytics_service)
        self.stats_display = UserStatsDisplay(analytics_service)
        self.quick_actions = QuickActions()

    def initialize(self) -> None:
        """Initialize the home page state and services."""
        if "user_email" not in st.session_state:
            st.session_state.user_email = self._get_user_email()

    def render_page(self) -> None:
        """Render the complete home page."""
        try:
            self.initialize()
            self.content.render()
        except Exception as e:
            st.error(f"Error rendering home page: {str(e)}")
            self._handle_error(e)

    def _get_user_email(self) -> Optional[str]:
        """Get the current user's email."""
        try:
            # Try to get email from session state
            if "user_email" in st.session_state:
                return st.session_state.user_email

            # Try to get email from authentication
            if hasattr(st, "user_email"):
                return st.user_email

            return None
        except Exception as e:
            st.error(f"Error getting user email: {str(e)}")
            return None

    def _handle_error(self, error: Exception) -> None:
        """Handle errors that occur during page rendering."""
        st.error("An error occurred while loading the home page.")
        if st.button("Try Again"):
            st.experimental_rerun() 
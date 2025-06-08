import logging
import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import math

class HomeContent:
    def __init__(self, user_service, analytics_service):
        self.user_service = user_service
        self.analytics_service = analytics_service

    def render(self) -> None:
        """Render the complete home page content."""
        self._render_header()
        self._render_user_stats()
        self._render_quick_actions()
        self._render_recent_activity()

    def _render_header(self) -> None:
        """Render the page header with user information."""
        st.title("Study Legend")
        
        email = st.session_state.get("email")
        logger = logging.getLogger(__name__)
        logger.info(f"Session email: {email}")  # Log session state using Python logger
        
        user = self.user_service.get_user_profile(email)
        if user:
            st.write(f"Welcome back, {user.get('name', 'User')}!")

    def _render_user_stats(self) -> None:
        """Render user statistics and progress."""
        email = st.session_state.get("email")
        if not email:
            return

        stats = self.analytics_service.get_user_statistics(email)
        if not stats:
            return

        st.subheader("Your Progress")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Questions", stats.get("total_questions", 0))
        with col2:
            st.metric("Average Score", f"{stats.get('average_score', 0):.1%}")
        with col3:
            st.metric("Active Subjects", len(stats.get("subject_stats", {})))

        # Display subject-wise progress
        st.subheader("Subject Progress")
        for subject, subject_stats in stats.get("subject_stats", {}).items():
            with st.expander(subject):
                st.progress(subject_stats.get("completion_rate", 0))
                st.write(f"Questions: {subject_stats.get('total_questions', 0)}")
                st.write(f"Average Score: {subject_stats.get('average_score', 0):.1%}")

    def _render_quick_actions(self) -> None:
        """Render quick action buttons for common tasks."""
        st.subheader("Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Add Question"):
                st.session_state.page = "add_question"
        with col2:
            if st.button("Start Practice"):
                st.session_state.page = "practice"
        with col3:
            if st.button("View Progress"):
                st.session_state.page = "progress"

    def _render_recent_activity(self) -> None:
        """Render recent user activity."""
        email = st.session_state.get("user_email")
        if not email:
            return

        st.subheader("Recent Activity")
        activity = self.analytics_service.get_recent_activity(email)
        
        if not activity:
            st.info("No recent activity to display.")
            return

        for item in activity:
            with st.container():
                st.write(f"**{item['type']}** - {item['timestamp']}")
                st.write(item['description'])
                st.divider()

class UserStatsDisplay:
    def __init__(self, analytics_service):
        self.analytics_service = analytics_service

    def render(self, email: str) -> None:
        """Render detailed user statistics."""
        stats = self.analytics_service.get_user_statistics(email)
        if not stats:
            return

        self._render_overview(stats)
        self._render_subject_stats(stats)
        self._render_progress_chart(stats)

    def _render_overview(self, stats: Dict) -> None:
        """Render overview statistics."""
        st.subheader("Overview")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Questions", stats.get("total_questions", 0))
        with col2:
            st.metric("Average Score", f"{stats.get('average_score', 0):.1%}")
        with col3:
            st.metric("Active Subjects", len(stats.get("subject_stats", {})))

    def _render_subject_stats(self, stats: Dict) -> None:
        """Render subject-specific statistics."""
        st.subheader("Subject Statistics")
        for subject, subject_stats in stats.get("subject_stats", {}).items():
            with st.expander(subject):
                st.progress(subject_stats.get("completion_rate", 0))
                st.write(f"Questions: {subject_stats.get('total_questions', 0)}")
                st.write(f"Average Score: {subject_stats.get('average_score', 0):.1%}")
                st.write(f"Last Practiced: {subject_stats.get('last_practiced', 'Never')}")

    def _render_progress_chart(self, stats: Dict) -> None:
        """Render progress chart."""
        st.subheader("Progress Over Time")
        weekly_progress = stats.get("weekly_progress", {})
        if weekly_progress:
            st.line_chart(weekly_progress)
        else:
            st.info("No progress data available yet.")

class QuickActions:
    def render(self) -> None:
        """Render quick action buttons."""
        st.subheader("Quick Actions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Add Question"):
                st.session_state.page = "add_question"
        with col2:
            if st.button("Start Practice"):
                st.session_state.page = "practice"
        with col3:
            if st.button("View Progress"):
                st.session_state.page = "progress" 
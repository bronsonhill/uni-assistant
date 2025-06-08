"""
Shared authentication components for the Study Legend application.
This module provides reusable authentication components and decorators.
"""
import streamlit as st
import functools
from typing import Optional, Callable, Any
from datetime import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

class AuthenticationManager:
    """Manages authentication state and operations."""
    
    def __init__(self, user_service):
        self.user_service = user_service
        self._current_user = None
        
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return 'email' in st.session_state and st.session_state.email is not None
        
    def get_current_user(self) -> Optional[dict]:
        """Get the current user's profile."""
        if not self.is_authenticated():
            return None
        return self.user_service.get_user_profile(st.session_state.email)
        
    def record_login(self, email: str) -> bool:
        """Record a user login."""
        try:
            is_new_login = self._is_new_login(email)
            if is_new_login:
                self.user_service.record_login(email)
                st.session_state.last_recorded_email = email
                
                # Show welcome message for first-time users
                user_data = self.user_service.get_user_profile(email)
                if user_data.get("login_count", 0) <= 1:
                    st.session_state.show_welcome = True
                    st.session_state.welcome_email = email
            return True
        except Exception as e:
            logger.error(f"Error recording login: {e}")
            return False
            
    def _is_new_login(self, email: str) -> bool:
        """Check if this is a new login session."""
        if "last_recorded_email" not in st.session_state:
            return True
        return st.session_state.get("last_recorded_email") != email

class SessionManager:
    """Manages user session state."""
    
    def __init__(self):
        self._session = {}
        
    def set_session(self, key: str, value: Any) -> None:
        """Set a session value."""
        st.session_state[key] = value
        
    def get_session(self, key: str) -> Any:
        """Get a session value."""
        return st.session_state.get(key)
        
    def clear_session(self) -> None:
        """Clear all session data."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]

def require_authentication(func: Callable) -> Callable:
    """
    Decorator to require authentication for a function.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that checks authentication
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("email"):
            show_login_prompt()
            return None
        return func(*args, **kwargs)
    return wrapper

def require_premium(func: Callable) -> Callable:
    """
    Decorator to require premium subscription for a function.
    
    Args:
        func: The function to decorate
        
    Returns:
        Decorated function that checks premium access
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("is_subscribed", False):
            show_upgrade_prompt()
            return None
        return func(*args, **kwargs)
    return wrapper

def show_login_prompt(sidebar: bool = False, force_rerun: bool = True) -> None:
    """Show the login prompt component.
    
    Args:
        sidebar: Whether to show the login in the sidebar
        force_rerun: Whether to force a rerun after authentication
    """
    logger.info("Entering show_login_prompt")
    # First check if user is already authenticated
    if 'email' in st.session_state and st.session_state.email is not None:
        logger.info("User already authenticated, returning")
        return
        
    logger.info("User not authenticated, showing login UI")
    st.warning("Please sign in to access this feature")
    # Use st-paywall's add_auth for authentication
    from st_paywall import add_auth
    logger.info("Calling st-paywall add_auth")
    add_auth(
        required=False,
        login_button_text="Sign in to Study Legend",
        login_button_color="#FF6F00",
        login_sidebar=sidebar
    )
    # Force a rerun to update the UI after authentication
    if force_rerun:
        logger.info("Forcing rerun after authentication")
        st.rerun()

def show_upgrade_prompt() -> None:
    """Show the premium upgrade prompt component."""
    st.info("This feature requires a premium subscription")
    if st.button("Upgrade Now"):
        # Redirect to upgrade page or show upgrade modal
        st.switch_page("pages/upgrade.py")

def show_welcome_message() -> None:
    """Show welcome message for new users."""
    if st.session_state.get("show_welcome", False):
        email = st.session_state.get("welcome_email", "")
        if email:
            st.success(f"Welcome to Study Legend, {email}! We're glad you're here.")
            st.session_state.show_welcome = False

class AuthComponents:
    """Collection of authentication UI components."""
    
    def __init__(self, user_service):
        """Initialize with user service dependency."""
        self.user_service = user_service
        logger.info("AuthComponents initialized")
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        logger.info("Checking authentication status")
        has_email = 'email' in st.session_state
        email_value = st.session_state.get("email")
        logger.info(f"Session has email key: {has_email}, email value: {email_value}")
        return has_email and email_value is not None
    
    def show_login_prompt(self) -> None:
        """Show the login prompt component."""
        logger.info("Showing login prompt")
        show_login_prompt(sidebar=True, force_rerun=True)
    
    def login_form(self) -> None:
        """Render the login form component."""
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                # Handle login logic
                pass
                
    def user_profile(self) -> None:
        """Render the user profile component."""
        user = st.session_state.get("email")
        if user:
            user_data = self.user_service.get_user_profile(user)
            st.write(f"Welcome, {user}")
            if st.button("Logout"):
                # Handle logout logic
                pass
                
    def subscription_status(self) -> None:
        """Render the subscription status component."""
        user = st.session_state.get("email")
        if user:
            is_subscribed = self.user_service.check_subscription_active(user)
            if is_subscribed:
                st.success("Premium Subscription Active")
            else:
                st.info("Free Account")
                if st.button("Upgrade to Premium"):
                    st.switch_page("pages/upgrade.py") 
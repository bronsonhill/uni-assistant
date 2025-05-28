"""
Authentication module for the Study Legend application.
This provides a centralized auth system using st-paywall's OAuth functionality.
"""
import streamlit as st
import os
from datetime import datetime
import users

# Import st-paywall for Google OAuth authentication
try:
    from st_paywall import add_auth
except ImportError:
    # Fallback if there's an issue with st_paywall
    def add_auth(required=False, login_button_text="Login", login_button_color="primary", login_sidebar=False):
        if "email" not in st.session_state:
            st.session_state.email = "test@example.com"  # Fallback to test user
        return True  # Always return subscribed in fallback mode

# Define constants
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
TEST_EMAIL = "test@example.com"  # For debug mode only

def require_auth(disable_for_debug=True, show_login=True, required=True):
    """
    Require authentication before accessing features.
    
    Args:
        disable_for_debug (bool): If True, will bypass auth in debug mode
        show_login (bool): If True, will show login UI 
        required (bool): If True, will halt execution if not authenticated
        
    Returns:
        str: The user's email if authenticated, or None if auth failed
    """
    if DEBUG_MODE and disable_for_debug:
        # In debug mode, use a test account
        email = TEST_EMAIL
        
        # Create test user if it doesn't exist
        if not users.get_user(TEST_EMAIL):
            users.record_login(TEST_EMAIL)
            
        st.session_state.email = email
        record_login_if_needed(email)
        return email

    # Use st-paywall's add_auth to authenticate (but don't require it)
    is_authenticated = add_auth(
        required=required,  # Don't require login to view
        login_button_text="Sign in to Study Legend",
        login_button_color="#FF6F00",  # Theme color
        login_sidebar=True,  # Use sidebar to not interrupt main content flow
    )
    
    # If authenticated, update session state
    if is_authenticated and 'email' in st.session_state:
        email = st.session_state.email
        record_login_if_needed(email)
        store_credentials_in_browser(email)
        return email
    
    # If login UI should be shown but not authenticated
    if show_login and not is_authenticated:
        # Don't redirect but show a login option in content area
        st.info("👋 **Welcome to Study Legend!** Sign in to get started.")
    
    return None

def check_feature_access(feature_name=None, require_auth=True):
    """
    Check if user can access a specific feature.
    
    Args:
        feature_name (str): Name of the feature (for display)
        require_auth (bool): Whether authentication is required
        
    Returns:
        bool: True if user can access the feature
    """
    if is_logged_in():
        return True
        
    if require_auth:
        message = f"Please sign in to use {feature_name or 'this feature'}."
        st.warning(message)
        return False
    
    return True

def record_login_if_needed(email):
    """
    Record login in our database if this is a new login.
    """
    # Check if this is a new login that needs to be recorded
    is_new_login = False
    if "last_recorded_email" not in st.session_state:
        is_new_login = True
    elif st.session_state.get("last_recorded_email") != email:
        is_new_login = True
    
    # Record login if this is a new login
    if is_new_login:
        try:
            # Try MongoDB first if enabled
            if users.USE_MONGODB:
                import mongodb
                mongodb.record_user_login(email)
                # Get user data for login count check
                user_data = mongodb.get_user(email)
            else:
                # Fall back to JSON storage
                user_data = users.record_login(email)
            
            # Store the email we just recorded to avoid duplicate records
            st.session_state.last_recorded_email = email
            
            # Show a welcome message if this is the first login for this user
            if user_data.get("login_count", 0) <= 1:
                st.session_state.show_welcome = True
                st.session_state.welcome_email = email
                
            return True
        except Exception as e:
            print(f"Error recording login: {e}")
            # Fall back to JSON storage if MongoDB fails
            user_data = users.record_login(email)
            st.session_state.last_recorded_email = email
            return True
            
    return False

def store_credentials_in_browser(email):
    """
    Store credentials in browser localStorage for persistent login.
    """
    if email:
        # Add JavaScript to store credentials locally
        email_js = email.replace('"', '\\"')
        st.markdown(f"""
        <script>
        // Store credentials in localStorage (more persistent than cookies)
        localStorage.setItem('study_legend_email', "{email_js}");
        localStorage.setItem('study_legend_auth', "authenticated");
        </script>
        """, unsafe_allow_html=True)
        
def check_subscription(user_email):
    """
    Check if the user has an active subscription.
    
    Args:
        user_email (str): User's email address
        
    Returns:
        bool: True if user has an active subscription
    """
    # Return true in debug mode
    if DEBUG_MODE:
        return True
        
    # First check st-paywall subscription
    st_paywall_subscribed = st.session_state.get('user_subscribed', False)
    
    # Then check our own database as well
    local_subscribed = False
    if user_email:
        local_subscribed = users.check_subscription_active(user_email)
        
    # If either system says they're subscribed, consider them subscribed
    is_subscribed = st_paywall_subscribed or local_subscribed
    
    # Update session state
    st.session_state.is_subscribed = is_subscribed
    
    return is_subscribed

def is_logged_in():
    """
    Check if user is currently logged in.
    
    Returns:
        bool: True if user is logged in
    """
    return 'email' in st.session_state and st.session_state.email is not None

def get_current_user():
    """
    Get the current user's email.
    
    Returns:
        str: Current user's email or None if not logged in
    """
    return st.session_state.get("email")

def show_welcome_message():
    """
    Show a welcome message for new users if needed.
    """
    if st.session_state.get("show_welcome", False):
        email = st.session_state.get("welcome_email", "")
        if email:
            st.success(f"Welcome to Study Legend, {email}! We're glad you're here.")
            # Clear the welcome flag so it doesn't show again
            st.session_state.show_welcome = False
    
def show_login_message(feature_name=None):
    """
    Show a message prompting user to login.
    
    Args:
        feature_name (str): Optional name of feature requiring login
    """
    if feature_name:
        st.info(f"Please sign in to use the **{feature_name}** feature.")
    else:
        st.info("Please sign in to use this feature.")

def require_premium(require_auth=True, require_premium=True):
    """
    Check if the user has premium access.
    
    Args:
        require_auth (bool): If True, will block access for unauthenticated users
        require_premium (bool): If True, will block access for non-premium users
        
    Returns:
        Tuple of (is_subscribed, user_email)
    """
    # First ensure the user is authenticated
    user_email = get_current_user()
    
    # If authentication required but not logged in
    if require_auth and not user_email:
        st.warning("Please sign in to continue.")
        # Show login button prominently
        add_auth(
            required=False,  # Don't redirect
            login_button_text="Sign in to Study Legend",
            login_button_color="#FF6F00",
            login_sidebar=False  # Show in main content for visibility
        )
        st.stop()
        
    # If we have a logged in user and premium is required
    if user_email and require_premium:
        is_subscribed = check_subscription(user_email)
        if not is_subscribed:
            st.warning("This feature requires a premium subscription.")
            # Show premium benefits
            st.markdown("### 🌟 Upgrade to Premium for these benefits:")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("✅ **Unlimited AI-generated questions**")
                st.markdown("✅ **Advanced question filtering**")
                st.markdown("✅ **Detailed progress analytics**")
            with col2:
                st.markdown("✅ **Priority support**")
                st.markdown("✅ **Assessment extraction from documents**")
                st.markdown("✅ **Export/import functionality**")
            st.stop()
        return is_subscribed, user_email
    
    # If no premium requirement or not logged in
    is_subscribed = False
    if user_email:
        is_subscribed = st.session_state.get('is_subscribed', False)
        
    return is_subscribed, user_email
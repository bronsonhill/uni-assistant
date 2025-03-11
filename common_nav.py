import streamlit as st

def render_home():
    """Render the home page content"""
    from Home import render_home_page
    render_home_page()

def render_practice():
    """Load and run the practice page"""
    from features.content import practice_content
    practice_content.run()

def render_add_ai():
    """Load and run the Add with AI page"""
    from features.content import add_ai_content
    add_ai_content.run()

def render_tutor():
    """Load and run the Subject Tutor page"""
    from features.content import tutor_content
    tutor_content.run()

def render_assessments():
    """Load and run the Assessments page"""
    from features.content import assessments_content
    assessments_content.run()

def render_manage():
    """Load and run the Manage Questions page"""
    from features.content import manage_content
    manage_content.run()

def render_add_manual():
    """Load and run the Add Manually page"""
    from features.content import add_manual_content
    add_manual_content.run()

def render_account():
    """Render the account page content"""
    from account import render_account_page
    render_account_page()

def setup_navigation():
    """
    Create and run navigation for Study Legend.
    This should be called from each page, followed by pg.run().
    
    Returns:
        pg: The navigation page object that should be run
    """
    # Use email session variable to determine login status
    is_logged_in = 'email' in st.session_state
    is_subscribed = st.session_state.get('is_subscribed', False)
    
    # Home page is always available
    home = st.Page(render_home, title="Home", icon="🏠", default=True)
    
    # Free features
    practice = st.Page(render_practice, title="Practice", icon="🎯")
    manage = st.Page(render_manage, title="Manage Questions", icon="📝")
    add_manual = st.Page(render_add_manual, title="Add Manually", icon="🆕")
    
    # Premium features
    add_ai = st.Page(render_add_ai, title="Add Cards with AI", icon="🤖")
    tutor = st.Page(render_tutor, title="Subject Tutor", icon="💬")
    assessments = st.Page(render_assessments, title="Assessments", icon="📅")
    
    # Account page
    account = st.Page(render_account, title="Account", icon="👤")
    
    # Create navigation structure based on login status
    if is_logged_in:
        if is_subscribed:
            # Full access for subscribed users
            navigation_structure = {
                "Main Features": [home, add_ai, practice, tutor, assessments],
                "Utilities": [manage, add_manual],
                "Account": [account]
            }
        else:
            # Restricted access for logged in but not subscribed users
            navigation_structure = {
                "Main Features": [home, practice],
                "Utilities": [manage, add_manual],
                "Premium Features": [add_ai, tutor, assessments],
                "Account": [account]
            }
    else:
        # Most basic structure for not logged in users
        navigation_structure = {
            "Main Features": [home, practice],
            "Utilities": [manage, add_manual],
            "Account": [account]
        }
    
    # Return the navigation page object - caller must call pg.run()
    return st.navigation(navigation_structure)
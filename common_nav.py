import streamlit as st

def render_home():
    """Render the home page content"""
    from Home import render_home_page
    render_home_page()

def render_practice():
    """Load and run the practice page"""
    from features.content.practice.practice_ui import render
    render()

def render_add_ai():
    """Load and run the Add with AI page"""
    from features.content.add_ai.add_ai_ui import render
    render()

def render_tutor():
    """Load and run the Subject Tutor page"""
    from features.content.tutor.tutor_ui import render
    render()

def render_assessments():
    """Load and run the Assessments page"""
    from features.content.assessments.assessments_ui import render
    render()

def render_manage():
    """Load and run the Manage Questions page"""
    from features.content.manage_questions.manage_questions_ui import render
    render()

def render_add_manual():
    """Load and run the Add Manually page"""
    from features.content.add_questions.add_questions_ui import render
    render()

def render_account():
    """Render the account page content"""
    from features.content.account.account_ui import render
    render()

def render_settings():
    """Load and run the Settings page"""
    from features.content.settings.settings_ui import render
    render()

def render_statistics():
    """Load and run the Statistics page"""
    from features.content.statistics.statistics_ui import render
    render()

def setup_navigation():
    """
    Create and run navigation for Study Legend.
    This should be called from each page, followed by pg.run().
    
    Returns:
        pg: The navigation page object that should be run
    """
    # Check login and subscription status using session state directly
    is_logged_in = st.session_state.get("email") is not None
    is_subscribed = st.session_state.get('user_subscribed', False)
    
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
    
    # Account and Settings pages
    account = st.Page(render_account, title="Account", icon="👤")
    settings = st.Page(render_settings, title="Settings", icon="⚙️")
    
    # Statistics page
    statistics = st.Page(render_statistics, title="Statistics", icon="📊")
    
    # Make all features visible in the navigation, regardless of login status
    # The individual features will handle authentication requirements themselves
    if is_subscribed:
        # Full access structure for subscribed users
        navigation_structure = {
            "Main Features": [home, add_ai, practice, tutor, assessments],
            "Utilities": [manage, add_manual, statistics],
            "Account & Settings": [account, settings]
        }
    else:
        # Structure with premium features marked separately
        navigation_structure = {
            "Main Features": [home, practice],
            "Utilities": [manage, add_manual, statistics],
            "Premium Features": [add_ai, tutor, assessments],
            "Account & Settings": [account, settings]
        }
    
    # Return the navigation page object - caller must call pg.run()
    return st.navigation(navigation_structure)
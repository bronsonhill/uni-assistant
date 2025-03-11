import streamlit as st
import os
from datetime import datetime
from paywall import check_subscription, show_premium_benefits, display_subscription_status
import users

def render_account_page():
    """Render the account page content"""
    st.title("👤 Account")
    
    # Force verification on account page to ensure subscription status is fresh
    # This helps ensure users always see accurate subscription details on this page
    is_subscribed, user_email = check_subscription(required=False, force_verify=True)
    
    # If user is not logged in, show login options
    if not user_email:
        st.markdown("### Login or Sign Up")
        st.info("Please log in or sign up to access your account and subscription details.")
        
        st.markdown("""
        #### Benefits of creating an account:
        - Save your progress and study history
        - Access the same questions across devices
        - Subscribe to premium features
        - Track your learning progress
        """)
        
        # Login button will be added by st_paywall in the sidebar
        st.markdown("👈 Use the login button in the sidebar to sign in.")
        
        return
    
    # User is logged in, show account info
    st.markdown(f"### Welcome, {user_email} 👋")
    
    # Get user data
    user_data = users.get_user(user_email)
    if not user_data:
        st.error("Error retrieving your account data. Please try again later.")
        return
    
    # Tab navigation for account sections
    tab1, tab2, tab3 = st.tabs(["Subscription", "Account Details", "Help"])
    
    with tab1:
        st.markdown("### Your Subscription")
        
        # Check subscription info - set skip_stripe=False since we want fresh data on the account page
        subscription_info = users.get_subscription_info(user_email, skip_stripe=False)
        
        if subscription_info and subscription_info["active"]:
            st.success("🌟 **Premium Subscription Active**")
            
            # Format the end date for display
            try:
                end_date = subscription_info.get("end_date", "Unknown")
                expiry_datetime = datetime.fromisoformat(end_date)
                formatted_date = expiry_datetime.strftime("%B %d, %Y")
                
                st.info(f"📅 Your subscription is active until **{formatted_date}**")
                st.info(f"⏱️ **{subscription_info['days_remaining']}** days remaining")
            except:
                st.info("Your subscription is active")
            
            st.markdown("#### Premium Features:")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("✅ **AI-generated questions**")
                st.markdown("✅ **Subject tutor access**")
                st.markdown("✅ **Assessments tracking**")
            
            with col2:
                st.markdown("✅ **Unlimited practice**")
                st.markdown("✅ **Advanced analytics**")
                st.markdown("✅ **Priority support**")
                
            # Manage subscription
            st.markdown("---")
            st.markdown("#### Manage Subscription")
            st.info("To manage your subscription or billing, please visit your payment provider account.")
            
        else:
            st.warning("❌ **No Active Subscription**")
            st.markdown("#### Upgrade to Premium to unlock all features:")
            
            # Show premium benefits
            show_premium_benefits()
            
            # Subscribe button will be shown by st_paywall
            
    with tab2:
        st.markdown("### Account Details")
        
        # Format dates for display
        created_date = user_data.get("created_at", "Unknown")
        last_login = user_data.get("last_login", "Unknown")
        
        try:
            created_datetime = datetime.fromisoformat(created_date)
            created_formatted = created_datetime.strftime("%B %d, %Y")
        except:
            created_formatted = created_date
            
        try:
            login_datetime = datetime.fromisoformat(last_login)
            login_formatted = login_datetime.strftime("%B %d, %Y at %H:%M")
        except:
            login_formatted = last_login
        
        # Account details
        st.markdown("#### Account Information")
        st.markdown(f"**Email:** {user_email}")
        st.markdown(f"**Account Created:** {created_formatted}")
        st.markdown(f"**Last Login:** {login_formatted}")
        st.markdown(f"**Total Logins:** {user_data.get('login_count', 0)}")
        
        # Show if login was just recorded in this session
        if st.session_state.get("last_recorded_email") == user_email:
            st.info("✅ Your login was recorded successfully.")
        
        # Account stats
        st.markdown("#### App Usage Stats")
        
        # Calculate stats from session state data if available
        total_questions = 0
        subject_count = 0
        all_weeks = set()
        
        if "data" in st.session_state:
            subject_count = len(st.session_state.data)
            
            for subject in st.session_state.data:
                for week in st.session_state.data[subject]:
                    if week != "vector_store_metadata":  # Skip metadata
                        all_weeks.add(week)
                        total_questions += len(st.session_state.data[subject][week])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Subjects", subject_count)
        with col3:
            st.metric("Weeks Covered", len(all_weeks))
            
        # Settings
        st.markdown("#### Settings")
        
        # Theme selector
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "System"],
            index=1,  # Default to dark
            help="Choose the theme for the application"
        )
        
        st.info("Theme settings will be saved in a future update.")
    
    with tab3:
        st.markdown("### Help & Support")
        
        st.markdown("""
        #### Frequently Asked Questions
        
        **Q: How do I use AI-generated questions?**  
        A: Navigate to "Add Cards with AI" in the sidebar, upload your course materials, and the AI will generate study questions for you.
        
        **Q: Can I export my questions?**  
        A: This feature is coming soon! You'll be able to export your questions to various formats.
        
        **Q: How do I cancel my subscription?**  
        A: You can cancel your subscription through your payment provider account. Your premium access will continue until the end of your billing period.
        
        **Q: Can I use this app offline?**  
        A: The app requires an internet connection to access the AI features. Basic question management works offline.
        
        #### Contact Support
        
        For additional help, please contact:
        - Email: support@studylegend.com
        - Twitter: @StudyLegendApp
        """)
        
        # Feedback form
        st.markdown("#### Share Your Feedback")
        with st.form("feedback_form"):
            feedback = st.text_area("We'd love to hear your thoughts on how we can improve Study Legend")
            submit_feedback = st.form_submit_button("Submit Feedback")
            
            if submit_feedback:
                st.success("Thank you for your feedback! We appreciate your input.")

def main():
    """Run the account page as a standalone page"""
    # Set page configuration
    st.set_page_config(
        page_title="Study Legend - Account", 
        page_icon="👤",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Render the account page
    render_account_page()

if __name__ == "__main__":
    main()
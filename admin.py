import streamlit as st
import users
from datetime import datetime, timedelta
import os
import time

# Set page configuration
st.set_page_config(
    page_title="Study Legend Admin",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Admin authentication
def check_admin_auth():
    # Get the admin credentials from environment variables or use defaults for development
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")
    
    # Check if already authenticated
    if st.session_state.get("admin_authenticated", False):
        return True
    
    # Show login form
    with st.form("admin_login"):
        st.markdown("### Admin Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        submit = st.form_submit_button("Login")
        
        if submit:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials")
                return False
    
    return False

# Function to display user management UI
def show_user_management():
    st.markdown("## User Management")
    
    # Get all users
    all_users = users.get_all_users()
    
    if not all_users:
        st.info("No users found in the database.")
        return
    
    # Convert to list for easier handling
    users_list = []
    for email, user_data in all_users.items():
        # Check if subscription is active (handles expiration)
        is_active = users.check_subscription_active(email)
        
        # Format dates for display
        created_at = user_data.get("created_at", "N/A")
        last_login = user_data.get("last_login", "N/A")
        subscription_end = user_data.get("subscription_end", "N/A")
        
        # Add to list
        users_list.append({
            "email": email,
            "subscription_active": "✅" if is_active else "❌",
            "created_at": created_at,
            "last_login": last_login,
            "login_count": user_data.get("login_count", 0),
            "subscription_end": subscription_end
        })
    
    # Sort by last login (most recent first)
    users_list.sort(key=lambda x: x.get("last_login", ""), reverse=True)
    
    # Search filter
    search_query = st.text_input("Search by email:", "")
    if search_query:
        users_list = [user for user in users_list if search_query.lower() in user["email"].lower()]
    
    # Filter options
    st.markdown("### Filters")
    col1, col2 = st.columns(2)
    with col1:
        show_active = st.checkbox("Active subscriptions", value=True)
    with col2:
        show_inactive = st.checkbox("Inactive subscriptions", value=True)
    
    # Apply filters
    filtered_users = []
    for user in users_list:
        is_active = user["subscription_active"] == "✅"
        if (is_active and show_active) or (not is_active and show_inactive):
            filtered_users.append(user)
    
    # Display users table
    st.markdown(f"### Users ({len(filtered_users)})")
    user_table = st.dataframe(
        filtered_users,
        column_config={
            "email": "Email",
            "subscription_active": "Active",
            "created_at": "Created",
            "last_login": "Last Login",
            "login_count": "Logins",
            "subscription_end": "Subscription End",
            "actions": st.column_config.Column(
                "Actions",
                width="small",
                help="Manage user subscription"
            )
        },
        hide_index=True,
        use_container_width=True
    )
    
    # User operations section
    st.markdown("### Manage User")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Activate Subscription")
        with st.form("activate_form"):
            user_email = st.text_input("User Email")
            duration = st.selectbox(
                "Duration", 
                options=[7, 30, 90, 180, 365], 
                format_func=lambda x: f"{x} days"
            )
            activate_submit = st.form_submit_button("Activate Subscription")
            
            if activate_submit and user_email:
                try:
                    user = users.activate_subscription(user_email, duration_days=duration)
                    st.success(f"Activated subscription for {user_email} for {duration} days")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error activating subscription: {str(e)}")
    
    with col2:
        st.markdown("#### Deactivate Subscription")
        with st.form("deactivate_form"):
            user_email_deactivate = st.text_input("User Email to Deactivate")
            deactivate_submit = st.form_submit_button("Deactivate Subscription")
            
            if deactivate_submit and user_email_deactivate:
                try:
                    user = users.deactivate_subscription(user_email_deactivate)
                    st.success(f"Deactivated subscription for {user_email_deactivate}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deactivating subscription: {str(e)}")

# Main admin interface
def main():
    st.markdown("# Study Legend Admin Panel")
    
    # Check admin authentication
    if not check_admin_auth():
        return
    
    # Show tabs for different admin functions
    tab1, tab2, tab3 = st.tabs(["User Management", "Settings", "Diagnostics"])
    
    with tab1:
        show_user_management()
    
    with tab2:
        st.markdown("## Application Settings")
        
        # Debug mode toggle
        debug_mode = os.environ.get("DEBUG_MODE", "false").lower() == "true"
        new_debug_mode = st.toggle("Debug Mode", value=debug_mode)
        
        if new_debug_mode != debug_mode:
            # In a real app, we would update an environment variable file
            # For this demo, just show a message
            st.info(f"Debug mode would be set to: {new_debug_mode}")
            st.info("In a production system, this would update the environment variables.")
        
        # Test email for debug mode
        test_email = os.environ.get("TEST_EMAIL", "test@example.com")
        new_test_email = st.text_input("Test Email (for Debug Mode)", value=test_email)
        
        if new_test_email != test_email:
            st.info(f"Test email would be set to: {new_test_email}")
            
    with tab3:
        st.markdown("## System Diagnostics")
        
        # Stripe API test section
        st.markdown("### Stripe API Connection Test")
        
        stripe_test_email = st.text_input("Email to check in Stripe", "test@example.com")
        
        if st.button("Test Stripe Connection"):
            with st.spinner("Testing Stripe API connection..."):
                # Show progress to indicate the test is running
                progress = st.progress(0)
                for i in range(100):
                    time.sleep(0.01)
                    progress.progress(i + 1)
                
                # Call our Stripe verification function
                try:
                    is_subscribed, end_date, subscription_data = users.verify_subscription_with_stripe(stripe_test_email)
                    
                    if is_subscribed:
                        st.success(f"✅ Stripe connection successful! Found active subscription until {end_date}")
                        
                        # Show subscription details in an expander
                        with st.expander("View Subscription Details"):
                            st.json(subscription_data)
                    else:
                        st.warning(f"⚠️ No active subscription found for {stripe_test_email}")
                        st.info("Possible reasons:")
                        st.markdown("1. User doesn't have an active subscription")
                        st.markdown("2. Stripe API key is incorrect or missing")
                        st.markdown("3. Network connectivity issues with Stripe API")
                        
                except Exception as e:
                    st.error(f"❌ ERROR testing Stripe connection: {str(e)}")
                    st.info("Check your Stripe API key configuration in .env or secrets.toml")
        
        # User data integrity check
        st.markdown("### User Data Integrity Check")
        
        if st.button("Check User Data Integrity"):
            with st.spinner("Checking user data..."):
                all_users = users.get_all_users()
                user_count = len(all_users)
                
                issues_found = 0
                issue_details = []
                
                for email, user_data in all_users.items():
                    # Check for required fields
                    missing_fields = []
                    for field in ["created_at", "last_updated", "subscription_status"]:
                        if field not in user_data:
                            missing_fields.append(field)
                    
                    if missing_fields:
                        issues_found += 1
                        issue_details.append(f"User {email} is missing fields: {', '.join(missing_fields)}")
                    
                    # Check if subscription data is consistent
                    if user_data.get("subscription_status", False) and not user_data.get("subscription_end"):
                        issues_found += 1
                        issue_details.append(f"User {email} has active subscription but no end date")
                
                if issues_found > 0:
                    st.warning(f"⚠️ Found {issues_found} issues in user data")
                    for issue in issue_details:
                        st.info(issue)
                else:
                    st.success(f"✅ All user data looks good! ({user_count} users checked)")
        
        # Database backup
        st.markdown("### Database Backup")
        
        if st.button("Create Backup of User Data"):
            with st.spinner("Creating backup..."):
                try:
                    backup_filename = f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    all_users = users.load_users()
                    
                    # In a real implementation, save to a separate file
                    # For this demo, just show what would be backed up
                    st.success(f"✅ Would create backup file: {backup_filename}")
                    with st.expander("Preview Backup Data"):
                        st.json(all_users)
                        
                except Exception as e:
                    st.error(f"❌ Error creating backup: {str(e)}")

if __name__ == "__main__":
    main()
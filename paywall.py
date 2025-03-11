import streamlit as st
try:
    from st_paywall import add_auth
except ImportError:
    # Fallback if there's an issue with st_paywall
    def add_auth(required=False, login_button_text="Login", login_button_color="primary", login_sidebar=False):
        if "email" not in st.session_state:
            st.session_state.email = "test@example.com"  # Fallback to test user
        return True  # Always return subscribed in fallback mode
        
import users
import os
from datetime import datetime

# Define constants
DEBUG_MODE = os.environ.get("DEBUG_MODE", "false").lower() == "true"
TEST_EMAIL = "test@example.com"  # For debug mode only

def handle_oauth_login():
    """
    Explicitly handle OAuth logins by checking if a new email is present
    in the session state but hasn't been recorded yet.
    
    This ensures logins are recorded even when the page isn't explicitly
    refreshed or when session state is maintained across refreshes.
    """
    if 'email' in st.session_state:
        user_email = st.session_state.email
        
        # Check if this is a new login that needs to be recorded
        is_new_login = False
        if "last_recorded_email" not in st.session_state:
            is_new_login = True
        elif st.session_state.get("last_recorded_email") != user_email:
            is_new_login = True
        
        # Record login if this is a new login
        if is_new_login:
            # Record the login in our database
            user_data = users.record_login(user_email)
            # Store the email we just recorded to avoid duplicate records
            st.session_state.last_recorded_email = user_email
            
            # Log the login for debugging
            print(f"User login explicitly recorded: {user_email} at {datetime.now().isoformat()}")
            
            # Show a welcome message if this is the first login for this user
            if user_data.get("login_count", 0) <= 1:
                st.session_state.show_welcome = True
                st.session_state.welcome_email = user_email
            
            return True
    
    return False

def check_subscription(required=True, force_verify=False):
    """
    Check if user is authenticated and has an active subscription.
    This function also handles recording user logins in the users.json database.
    
    Args:
        required (bool): If True, will redirect unauthenticated users to login.
                        If False, will allow access but display subscription info.
        force_verify (bool): If True, will verify with Stripe even if cached status exists.
                            Use this for pages where subscription status is critical.
    
    Returns:
        tuple: (is_subscribed, user_email)
            - is_subscribed (bool): True if user is subscribed
            - user_email (str or None): Email of the authenticated user or None
    """
    # First, explicitly handle any OAuth login that may have happened
    login_recorded = handle_oauth_login()
    
    # Check if we need to restore a session from a previous page load
    if 'email' not in st.session_state:
        try:
            # Add JavaScript to check for stored credentials and pass them back
            # This creates a two-way communication between client and server
            st.markdown("""
            <script>
            // Function to get cookies by name
            function getCookie(name) {
                const value = `; ${document.cookie}`;
                const parts = value.split(`; ${name}=`);
                if (parts.length === 2) return parts.pop().split(';').shift();
                return null;
            }
            
            // Check for stored credentials
            const storedEmail = localStorage.getItem('study_legend_email');
            const storedAuth = localStorage.getItem('study_legend_auth');
            
            // If credentials exist, pass them to Streamlit
            if (storedEmail && storedAuth) {
                // Use Streamlit's setComponentValue when available in this context
                // For now we'll use a URL parameter approach
                const queryString = window.location.search;
                const urlParams = new URLSearchParams(queryString);
                
                // Only add the parameter if it's not already there
                if (!urlParams.has('restore_session')) {
                    urlParams.set('restore_session', storedEmail);
                    
                    // Redirect to the same page with the parameter
                    if (window.location.pathname.endsWith('/Home')) {
                        window.location.href = window.location.pathname + '?' + urlParams.toString();
                    }
                }
            }
            </script>
            """, unsafe_allow_html=True)
            
            # Check URL parameters for restored session using the new API
            if 'restore_session' in st.query_params:
                email = st.query_params['restore_session']
                print(f"Restoring session for email: {email}")
                st.session_state.email = email
                st.session_state.auth_initialized = True
                
                # Record this login
                users.record_login(email)
                st.session_state.last_recorded_email = email
                
                # Clear the parameter (safely using new API)
                # Create a new dict without the restore_session parameter
                st.query_params.clear()
                
                # Force a reverification
                force_verify = True
        except Exception as e:
            print(f"Error attempting to restore session: {e}")
    
    # When user is successfully logged in, store credentials in browser
    if 'email' in st.session_state and st.session_state.get('email'):
        # Add JavaScript to store credentials locally
        email_js = st.session_state.email.replace('"', '\\"')
        st.markdown(f"""
        <script>
        // Store credentials in localStorage (more persistent than cookies)
        localStorage.setItem('study_legend_email', "{email_js}");
        localStorage.setItem('study_legend_auth', "authenticated");
        </script>
        """, unsafe_allow_html=True)
    
    # Check for cached subscription status - we'll use this to avoid unnecessary API calls
    subscription_cached = 'is_subscribed' in st.session_state and 'subscription_verified_at' in st.session_state
    
    # Cache check subscription results to prevent redundant calls in the same session
    cache_key = "check_subscription_result"
    if cache_key in st.session_state and not force_verify and not login_recorded:
        result = st.session_state[cache_key]
        return result
    
    # Determine if we need to reverify the subscription
    need_verification = (
        force_verify or                # Explicit force flag
        login_recorded or              # New login just recorded
        not subscription_cached or     # No cached status
        'email' not in st.session_state # No user logged in
    )
    
    # If we have a cached subscription status and don't need to verify,
    # just return the cached values to avoid unnecessary API calls
    if not need_verification and subscription_cached:
        is_subscribed = st.session_state.is_subscribed
        user_email = st.session_state.get('email')
        st.session_state[cache_key] = (is_subscribed, user_email)
        return is_subscribed, user_email
    
    try:
        # If in debug mode and test email is set, bypass authentication
        if DEBUG_MODE:
            is_subscribed = True
            user_email = TEST_EMAIL
            
            # Create test user if it doesn't exist
            if not users.get_user(TEST_EMAIL):
                users.activate_subscription(TEST_EMAIL, duration_days=365)
                
            st.session_state.email = user_email
            st.session_state.is_subscribed = is_subscribed
            
            # Record verification time
            from datetime import datetime
            st.session_state.subscription_verified_at = datetime.now().isoformat()
            
            return is_subscribed, user_email
        
        # Normal authentication flow
        # If required=True, this will redirect to login if user is not authenticated
        # If user is authenticated but not subscribed, it will show the payment page
        
        # Create a key for the session to ensure we're not creating multiple buttons
        if "auth_initialized" not in st.session_state:
            st.session_state.auth_initialized = True
            is_subscribed = add_auth(
                required=required,
                login_button_text="Login to Study Legend",
                login_button_color="#FF6F00",  # Match our theme color
                login_sidebar=True,  # Show login button in sidebar
            )
        else:
            # Use existing authentication
            is_subscribed = add_auth(
                required=required,
            )
        
        # If user is authenticated, their email will be available in session state
        if 'email' in st.session_state:
            user_email = st.session_state.email
            
            # Only verify with APIs if needed
            if need_verification:
                # Verify with Stripe first if the status changed or we need to validate
                stripe_verified, stripe_end_date, stripe_subscription = users.verify_subscription_with_stripe(user_email)
                
                # If Stripe confirms an active subscription, use that as the source of truth
                if stripe_verified:
                    # Update our local database with the subscription data from Stripe
                    users.activate_subscription(user_email, end_date=stripe_end_date)
                    print(f"Updated subscription from Stripe: active until {stripe_end_date}")
                    
                    # Ensure we set is_subscribed true regardless of what st_paywall reported
                    is_subscribed = True
                else:
                    # Stripe says no active subscription
                    # First check if we have local subscription override
                    local_subscription = users.check_subscription_active(user_email, skip_stripe=True)  # Skip Stripe here since we already checked
                    
                    if local_subscription:
                        # If our database says they should be subscribed (manual override),
                        # keep it active regardless of what Stripe or st_paywall says
                        print(f"Using local subscription override for {user_email}")
                        is_subscribed = True
                    else:
                        # If Stripe says no subscription and we have no override,
                        # check if st_paywall thinks they're subscribed
                        if is_subscribed:
                            # st_paywall thinks they're subscribed but Stripe says no
                            # This could be:
                            # 1. Stripe API error
                            # 2. Recent subscription that hasn't propagated to Stripe API yet
                            # 3. st_paywall bug
                            
                            print(f"st_paywall reports subscription for {user_email} but Stripe verification failed")
                            
                            # Try to use subscription info from session state as fallback
                            if hasattr(st.session_state, 'subscriptions') and st.session_state.subscriptions:
                                try:
                                    # Get the first subscription
                                    subscription = st.session_state.subscriptions.data[0]
                                    
                                    # Check if it has an end date
                                    if subscription.get('current_period_end'):
                                        import datetime
                                        
                                        # Calculate days from now until end date
                                        end_timestamp = subscription['current_period_end']
                                        end_date = datetime.datetime.fromtimestamp(end_timestamp)
                                        end_date_iso = end_date.isoformat()
                                        
                                        # Use st_paywall data as fallback, but warn about discrepancy
                                        users.activate_subscription(user_email, end_date=end_date_iso)
                                        print(f"WARNING: Using st_paywall data despite Stripe API discrepancy")
                                        print(f"Temporary subscription until {end_date_iso}")
                                        
                                        # Set session state for navigation
                                        is_subscribed = True
                                    else:
                                        # No usable date data anywhere
                                        print(f"No usable subscription end date found - using default 7 days")
                                        users.activate_subscription(user_email, duration_days=7)
                                        is_subscribed = True
                                except Exception as e:
                                    print(f"Error extracting st_paywall subscription data: {e}")
                                    # Give benefit of the doubt with a short subscription period
                                    # This will be corrected on next page load if Stripe API is available
                                    users.activate_subscription(user_email, duration_days=7)
                                    is_subscribed = True
                            else:
                                # st_paywall says subscribed but provides no data and Stripe says no
                                # Give benefit of the doubt with a very short subscription
                                print(f"Granting temporary 7-day subscription due to Stripe API discrepancy")
                                users.activate_subscription(user_email, duration_days=7)
                                is_subscribed = True
                        else:
                            # Both Stripe and st_paywall agree: no subscription
                            is_subscribed = False
                
                # Record verification time
                from datetime import datetime
                st.session_state.subscription_verified_at = datetime.now().isoformat()
            else:
                # Using cached value
                print(f"Using cached subscription status for {user_email}")
                is_subscribed = st.session_state.get('is_subscribed', False)
        else:
            user_email = None
            is_subscribed = False
        
        # Store subscription status in session state for the navigation system
        st.session_state.is_subscribed = is_subscribed
        
        # Cache the result
        st.session_state["check_subscription_result"] = (is_subscribed, user_email)
        
        # Relying on server-side session state for persistence
        # No need for additional cookie management
            
        return is_subscribed, user_email
        
    except Exception as e:
        print(f"Error with authentication or payment: {str(e)}")
        
        # If there's an exception, fall back to checking local database
        if 'email' in st.session_state:
            user_email = st.session_state.email
            local_subscription = users.check_subscription_active(user_email, skip_stripe=True)  # Skip Stripe to avoid potential infinite loop
            st.session_state.is_subscribed = local_subscription
            
            # Cache the result even in the error case
            st.session_state["check_subscription_result"] = (local_subscription, user_email)
            
            # Relying on server-side session state for persistence
            # No need for additional cookie management
            
            return local_subscription, user_email
        else:
            st.session_state.is_subscribed = False
            
            # Cache the negative result
            st.session_state["check_subscription_result"] = (False, None)
            
            return False, None

def show_premium_benefits():
    """Show the benefits of premium subscription to encourage sign-up"""
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
    
    st.markdown("---")

def display_subscription_status():
    """
    Display the user's subscription status in the sidebar.
    Should be called after check_subscription().
    
    Note: Does NOT add a subscribe button, as st_paywall already handles this
    """
    # Cache key for subscription info to avoid redundant calls
    cache_key = "sidebar_subscription_info"
    
    if 'email' in st.session_state:
        email = st.session_state.email
        
        # Check if we already have the subscription info in cache
        if cache_key in st.session_state:
            subscription_info = st.session_state[cache_key]
        else:
            # Get subscription info with skip_stripe=True to avoid redundant Stripe calls
            # since check_subscription() would have already verified with Stripe if needed
            subscription_info = users.get_subscription_info(email)
            st.session_state[cache_key] = subscription_info
        
        # Create a sidebar expander for account info
        with st.sidebar.expander("💳 Subscription Status", expanded=True):
            if subscription_info and subscription_info["active"]:
                st.success(f"✅ Premium subscription active")
                if subscription_info["days_remaining"] > 0:
                    st.info(f"⏱️ {subscription_info['days_remaining']} days remaining")
                
                # Add link to Account page
                st.markdown("[View account details](/7_👤_Account)", unsafe_allow_html=True)
            else:
                st.warning("❌ No active subscription")
                # We do NOT add a subscription button here, as st_paywall handles this
                
                # Add link to Account page
                st.markdown("[View account details](/7_👤_Account)", unsafe_allow_html=True)
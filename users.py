import json
import os
import time
import threading
from datetime import datetime, timedelta
import streamlit as st

# Path to the users database file
USERS_DB_PATH = "users.json"

# Flag to control whether to use MongoDB or JSON files
USE_MONGODB = True

# Global lock for file access
file_lock = threading.Lock()

def load_users():
    """
    Load users from the database (MongoDB or JSON file)
    
    Returns:
        dict: User data dictionary
    """
    # Check if users data is already cached in session state
    if "cached_users_data" in st.session_state:
        return st.session_state.cached_users_data
    
    # Try MongoDB first if enabled
    if USE_MONGODB:
        try:
            import mongodb
            users_dict = mongodb.load_users()
            data = {"users": users_dict}
            st.session_state.cached_users_data = data
            return data
        except Exception as e:
            print(f"Error loading users from MongoDB: {e}")
            # Fall back to JSON file if MongoDB fails
            pass
    
    # Load from JSON file as fallback
    try:
        with file_lock:  # Use lock to prevent concurrent access
            if os.path.exists(USERS_DB_PATH):
                try:
                    with open(USERS_DB_PATH, 'r') as f:
                        data = json.load(f)
                        print(f"Loaded {len(data.get('users', {}))} users from database")
                        # Cache the result in session state
                        st.session_state.cached_users_data = data
                        return data
                except json.JSONDecodeError:
                    print("Error reading users file. Creating a new one.")
                    data = {"users": {}}
                    st.session_state.cached_users_data = data
                    return data
            else:
                data = {"users": {}}
                st.session_state.cached_users_data = data
                return data
    except Exception as e:
        print(f"Error loading users: {e}")
        data = {"users": {}}
        st.session_state.cached_users_data = data
        return data

def save_users(users_data):
    """
    Save users to the database (MongoDB or JSON file)
    
    Args:
        users_data (dict): User data dictionary to save
    """
    # Update session state cache with the new data
    st.session_state.cached_users_data = users_data
    
    # Try MongoDB first if enabled
    if USE_MONGODB:
        try:
            import mongodb
            mongodb.save_users(users_data["users"])
            return
        except Exception as e:
            print(f"Error saving users to MongoDB: {e}")
            # Fall back to JSON file if MongoDB fails
            pass
    
    # Save to JSON file as fallback
    try:
        with file_lock:  # Use lock to prevent concurrent access
            with open(USERS_DB_PATH, 'w') as f:
                json.dump(users_data, f, indent=2)
    except Exception as e:
        print(f"Error saving users to JSON: {e}")

def get_user(email):
    """
    Get a user by email
    
    Args:
        email (str): The user's email
        
    Returns:
        dict: The user data or None if not found
    """
    # Try MongoDB first if enabled
    if USE_MONGODB:
        try:
            import mongodb
            user_data = mongodb.get_user(email)
            if user_data:
                return user_data
            # If user not found in MongoDB, fall back to JSON
        except Exception as e:
            print(f"Error getting user from MongoDB: {e}")
            # Fall back to JSON file if MongoDB fails
            pass
    
    # Get from JSON as fallback
    users_data = load_users()
    return users_data["users"].get(email)

def create_or_update_user(email, subscription_status=False, subscription_end=None):
    """
    Create a new user or update an existing one
    
    Args:
        email (str): User's email address
        subscription_status (bool): Whether user has an active subscription
        subscription_end (str): ISO format date when subscription ends
        
    Returns:
        dict: The updated user data
    """
    try:
        # Load current users
        users_data = load_users()
        
        # Prepare the update in memory
        current_time = datetime.now().isoformat()
        
        if email in users_data["users"]:
            # Update existing user
            user = users_data["users"][email]
            if subscription_status is not None:
                user["subscription_status"] = subscription_status
            if subscription_end is not None:
                user["subscription_end"] = subscription_end
            user["last_updated"] = current_time
        else:
            # Create new user
            users_data["users"][email] = {
                "email": email,
                "subscription_status": subscription_status,
                "subscription_end": subscription_end,
                "created_at": current_time,
                "last_updated": current_time,
                "login_count": 0
            }
        
        # Save to storage (MongoDB or JSON)
        save_users(users_data)
        
        # If using MongoDB, also update directly
        if USE_MONGODB:
            try:
                import mongodb
                # Create a user document
                user_doc = users_data["users"][email].copy()
                mongodb.add_user(email, user_doc)
            except Exception as e:
                # Log but continue if MongoDB update fails
                print(f"Error directly updating MongoDB user: {e}")
        
        return users_data["users"][email]
    except Exception as e:
        print(f"Error in create_or_update_user: {e}")
        # Return a minimal user object in case of errors
        return {"email": email, "error": str(e)}

def record_login(email):
    """
    Record a user login
    
    Args:
        email (str): User's email address
        
    Returns:
        dict: The updated user data
    """
    print(f"Recording login for {email}")
    
    try:
        # Load data
        users_data = load_users()
        
        # Prepare the update in memory
        current_time = datetime.now().isoformat()
        
        if email in users_data["users"]:
            print(f"Updating existing user {email}")
            user = users_data["users"][email]
            user["login_count"] = user.get("login_count", 0) + 1
            user["last_login"] = current_time
            user["last_updated"] = current_time
        else:
            print(f"Creating new user for {email}")
            # For new users, create the entry in memory
            users_data["users"][email] = {
                "email": email,
                "subscription_status": False,
                "subscription_end": None,
                "created_at": current_time,
                "last_updated": current_time,
                "login_count": 1,
                "last_login": current_time
            }
            user = users_data["users"][email]
        
        # Make a copy of the user data before saving
        user_copy = user.copy()
        
        # Save the updates to storage
        save_users(users_data)
        
        # If using MongoDB, also update directly
        if USE_MONGODB:
            try:
                import mongodb
                mongodb.update_user_field(email, "login_count", user["login_count"])
                mongodb.update_user_field(email, "last_login", current_time)
            except Exception as e:
                # Log but continue if MongoDB update fails
                print(f"Error directly updating MongoDB login: {e}")
        
        print(f"User login for {email} recorded successfully")
        
        return user_copy
    except Exception as e:
        print(f"Error recording login: {e}")
        # Return a minimal user object in case of errors
        return {"email": email, "login_count": 1, "error": str(e)}

def check_subscription_active(email, skip_stripe=False):
    """
    Check if a user's subscription is active
    
    Args:
        email (str): User's email address
        skip_stripe (bool): If True, skips Stripe verification and uses only local data
                          This is useful to avoid redundant API calls when Stripe was 
                          already checked elsewhere.
        
    Returns:
        bool: True if subscription is active, False otherwise
    """
    # Check if we have a cached verification result in session state
    cache_key = f"subscription_verified_{email}"
    
    if cache_key in st.session_state and skip_stripe:
        # Use cached result if we're allowed to skip Stripe and have a cached value
        return st.session_state[cache_key]
    
    # Check Stripe first unless explicitly told to skip
    if not skip_stripe:
        try:
            # Verify with Stripe directly
            stripe_verified, stripe_end_date, _ = verify_subscription_with_stripe(email)
            
            if stripe_verified:
                # Stripe says subscription is active - update our records
                # This keeps our database in sync with Stripe
                activate_subscription(email, end_date=stripe_end_date)
                
                # Cache the positive result
                st.session_state[cache_key] = True
                
                # Only log when actually verifying with Stripe
                print(f"Verified active subscription with Stripe for {email} until {stripe_end_date}")
                return True
        except Exception as e:
            # If Stripe verification fails, log it but continue to check local data
            print(f"Stripe verification failed for {email}: {e}")
    
    # If Stripe verification was skipped, failed, or returned False, check local data
    try:
        # Get the user
        user = get_user(email)
        
        if not user:
            st.session_state[cache_key] = False
            return False
        
        # If user doesn't have subscription status, they're not subscribed
        if not user.get("subscription_status", False):
            st.session_state[cache_key] = False
            return False
        
        # Check if subscription has expired
        end_date = user.get("subscription_end")
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
                if end_datetime < datetime.now():
                    # Subscription has expired
                    deactivate_subscription(email)
                    
                    # Cache the negative result
                    st.session_state[cache_key] = False
                    return False
            except (ValueError, TypeError) as e:
                # Invalid date format, assume not subscribed
                print(f"Invalid date format in subscription: {e}")
                st.session_state[cache_key] = False
                return False
        
        # Cache the positive result
        st.session_state[cache_key] = True
        return True
    except Exception as e:
        # If anything goes wrong, err on the side of caution
        print(f"Error checking subscription: {e}")
        st.session_state[cache_key] = False
        return False

def activate_subscription(email, duration_days=30, end_date=None):
    """
    Activate a subscription for a user
    
    Args:
        email (str): User's email address
        duration_days (int): Number of days the subscription is valid for
        end_date (str, optional): ISO format date when subscription ends. If provided, overrides duration_days.
        
    Returns:
        dict: The updated user data
    """
    if end_date is None:
        end_date = (datetime.now() + timedelta(days=duration_days)).isoformat()
    
    return create_or_update_user(
        email, 
        subscription_status=True,
        subscription_end=end_date
    )
    
def verify_subscription_with_stripe(email):
    """
    Directly verify a subscription status with Stripe API
    This serves as a backup verification method when st_paywall reports issues
    
    Args:
        email (str): User's email address
        
    Returns:
        tuple: (is_subscribed, subscription_end_date, subscription_data)
    """
    # Check for cached result first
    cache_key = f"stripe_verification_{email}"
    if cache_key in st.session_state:
        # Return the cached result if we have one
        cached_result = st.session_state[cache_key]
        return cached_result
    
    try:
        # Check if stripe module is available
        import stripe
        import os
        
        # Get API key from environment or secrets
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            try:
                stripe_api_key = st.secrets.get("stripe_api_key")
            except:
                print("Could not get Stripe API key")
                result = (False, None, None)
                st.session_state[cache_key] = result
                return result
        
        if not stripe_api_key:
            print("No Stripe API key available")
            result = (False, None, None)
            st.session_state[cache_key] = result
            return result
            
        # Set API key
        stripe.api_key = stripe_api_key
        
        # Look up customer by email
        customers = stripe.Customer.list(email=email)
        if not customers.data:
            result = (False, None, None)
            st.session_state[cache_key] = result
            return result
            
        # Get first customer
        customer = customers.data[0]
        
        # Get subscriptions
        subscriptions = stripe.Subscription.list(customer=customer["id"])
        if not subscriptions.data:
            result = (False, None, None)
            st.session_state[cache_key] = result
            return result
            
        # Check for active subscriptions
        active_subscriptions = [s for s in subscriptions.data if s.status == "active"]
        if not active_subscriptions:
            result = (False, None, None)
            st.session_state[cache_key] = result
            return result
            
        # Get the subscription with the furthest end date
        subscription = max(active_subscriptions, key=lambda s: s.current_period_end)
        
        # Convert timestamp to datetime
        import datetime
        end_date = datetime.datetime.fromtimestamp(subscription.current_period_end)
        end_date_iso = end_date.isoformat()
        
        print(f"Verified active Stripe subscription for {email} ending on {end_date_iso}")
        result = (True, end_date_iso, subscription)
        st.session_state[cache_key] = result
        return result
        
    except Exception as e:
        print(f"Error verifying Stripe subscription: {e}")
        result = (False, None, None)
        st.session_state[cache_key] = result
        return result

def deactivate_subscription(email):
    """
    Deactivate a user's subscription
    
    Args:
        email (str): User's email address
        
    Returns:
        dict: The updated user data
    """
    return create_or_update_user(
        email, 
        subscription_status=False,
        subscription_end=None
    )

def get_all_users():
    """
    Get all users in the database
    
    Returns:
        dict: Dictionary of all users
    """
    users_data = load_users()
    return users_data["users"]

def get_subscription_info(email, skip_stripe=True):
    """
    Get formatted subscription information for a user
    
    Args:
        email (str): User's email address
        skip_stripe (bool): If True, skips Stripe verification and uses only local data
                        This is useful to avoid redundant API calls when Stripe was
                        already checked elsewhere.
        
    Returns:
        dict: Subscription information or None if user not found
    """
    # Check for cached info
    cache_key = f"subscription_info_{email}"
    
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    user = get_user(email)
    if not user:
        st.session_state[cache_key] = None
        return None
    
    # Use skip_stripe=True by default to avoid redundant Stripe calls
    # since the check is usually done earlier in the app flow
    is_active = check_subscription_active(email, skip_stripe=skip_stripe)
    end_date = user.get("subscription_end")
    
    if not end_date or not is_active:
        result = {
            "active": False,
            "end_date": None,
            "days_remaining": 0
        }
        st.session_state[cache_key] = result
        return result
    
    try:
        end_datetime = datetime.fromisoformat(end_date)
        days_remaining = (end_datetime - datetime.now()).days
        result = {
            "active": is_active,
            "end_date": end_date,
            "days_remaining": max(0, days_remaining)
        }
        st.session_state[cache_key] = result
        return result
    except (ValueError, TypeError):
        result = {
            "active": False,
            "end_date": None,
            "days_remaining": 0
        }
        st.session_state[cache_key] = result
        return result
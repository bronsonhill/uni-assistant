"""
Test script to verify that users.json can be updated
"""
import users
from datetime import datetime

def test_add_user():
    """Test adding a new user to the database"""
    print("Testing adding a new user...")
    
    # Generate a unique test email with current timestamp
    test_email = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
    print(f"Test email: {test_email}")
    
    # Attempt to add the user
    user_data = users.create_or_update_user(
        email=test_email,
        subscription_status=False,
        subscription_end=None
    )
    
    print(f"User added: {user_data}")
    
    # Verify the user was added
    all_users = users.get_all_users()
    print(f"Total users: {len(all_users)}")
    
    # Verify the user exists in the database
    if test_email in all_users:
        print("✅ User was successfully added to the database")
    else:
        print("❌ Failed to add user to the database")
        
    print("\nCurrent users in database:")
    for email in all_users:
        print(f"- {email}")
    
def test_record_login():
    """Test recording a login for an existing user"""
    print("\nTesting recording a login...")
    
    # Use an existing user
    test_email = "free@example.com"
    
    # Get current login count
    user_before = users.get_user(test_email)
    login_count_before = user_before.get("login_count", 0) if user_before else 0
    print(f"Login count before: {login_count_before}")
    
    # Record a login
    user_after = users.record_login(test_email)
    login_count_after = user_after.get("login_count", 0)
    print(f"Login count after: {login_count_after}")
    
    # Verify login count increased
    if login_count_after > login_count_before:
        print("✅ Login count successfully incremented")
    else:
        print("❌ Failed to increment login count")

if __name__ == "__main__":
    # Run tests
    test_add_user()
    test_record_login()
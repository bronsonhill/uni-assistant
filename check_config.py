import os
import glob
import re
import sys
import pathlib
import streamlit as st

def check_feature_files():
    """Check and fix page config in feature files"""
    # Path to features directory
    features_dir = "./features"
    
    # Get all Python files in the features directory
    feature_files = glob.glob(os.path.join(features_dir, "*.py"))
    
    # Process each file
    for file_path in feature_files:
        print(f"Checking {file_path}...")
        
        # Read the file content
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for commented page_config
        if re.search(r'# st\.set_page_config', content):
            print(f"  Found commented page_config in {file_path}")
            # Uncomment the page_config section
            content = re.sub(
                r'# Set the page config.*?\n# st\.set_page_config\(\n#\s+(.*?)\n#\s+(.*?)\n#\s+(.*?)\n#\s+(.*?)\n# \)',
                r'# Set the page config (should be the same across all pages)\nst.set_page_config(\n    \1\n    \2\n    \3\n    \4\n)',
                content, flags=re.DOTALL
            )
            
            # Write the updated content back to the file
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"  Fixed page_config in {file_path}")
    
    print("All feature files checked!")

def test_stripe_connection():
    """Test direct connection to Stripe API"""
    try:
        # Add parent directory to path for imports
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        import users
        
        # Test email to check - this should be a real user email
        test_email = "test@example.com"
        
        print(f"\n==== Testing Stripe API connection for {test_email} ====\n")
        
        # Test direct verification
        is_subscribed, end_date, subscription_data = users.verify_subscription_with_stripe(test_email)
        
        if is_subscribed:
            print(f"✅ SUCCESS: Found active subscription until {end_date}")
            print(f"Subscription details: {subscription_data}")
        else:
            print(f"❌ No active subscription found for {test_email}")
            print("Possible reasons:")
            print("1. User doesn't have an active subscription")
            print("2. Stripe API key is incorrect or missing")
            print("3. Network connectivity issues with Stripe API")
        
        print("\n==== End of Stripe API test ====\n")
        
    except Exception as e:
        print(f"❌ ERROR testing Stripe connection: {e}")

def check_secrets_config():
    """Check if Streamlit secrets.toml exists and has required keys"""
    print("\n==== Checking Streamlit secrets configuration ====\n")
    
    # Check if .streamlit directory exists
    streamlit_dir = pathlib.Path(".streamlit")
    if not streamlit_dir.exists():
        print("❌ .streamlit directory not found. Creating it...")
        streamlit_dir.mkdir(exist_ok=True)
        print("✅ Created .streamlit directory")
    
    # Check if secrets.toml exists
    secrets_file = streamlit_dir / "secrets.toml"
    example_file = pathlib.Path("example_secrets.toml")
    
    if not secrets_file.exists():
        print("❌ .streamlit/secrets.toml not found")
        
        if example_file.exists():
            print("ℹ️ example_secrets.toml found. You can copy this file to .streamlit/secrets.toml")
            print("   Run: cp example_secrets.toml .streamlit/secrets.toml")
            print("   Then edit the file to add your actual API keys")
        else:
            print("ℹ️ Creating an example_secrets.toml file for you...")
            with open(example_file, "w") as f:
                f.write("""# Example Streamlit secrets.toml file
# Copy this file to .streamlit/secrets.toml and fill in your actual API keys

# OpenAI API key for generating questions and managing vector stores
OPENAI_API_KEY = "your-openai-api-key-here"

# Admin credentials for admin features
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "your-secure-password-here"

# Optional: Stripe API keys if using Stripe for payments
# STRIPE_SECRET_KEY = "your-stripe-secret-key"
# STRIPE_PUBLISHABLE_KEY = "your-stripe-publishable-key"

# Note: Never commit your actual secrets.toml file to version control
# This example file is safe to commit as it doesn't contain real credentials
""")
            print("✅ Created example_secrets.toml file")
            print("   Run: cp example_secrets.toml .streamlit/secrets.toml")
            print("   Then edit the file to add your actual API keys")
    else:
        print("✅ .streamlit/secrets.toml found")
        
        # Try to check if required keys are present
        try:
            # This will only work when running in Streamlit
            if hasattr(st, 'secrets'):
                if "OPENAI_API_KEY" not in st.secrets:
                    print("⚠️ OPENAI_API_KEY not found in secrets.toml")
                else:
                    print("✅ OPENAI_API_KEY found in secrets.toml")
            else:
                print("ℹ️ Cannot verify secrets content when not running in Streamlit")
                print("   Please ensure your secrets.toml file contains at least OPENAI_API_KEY")
        except Exception as e:
            print(f"ℹ️ Cannot verify secrets content: {e}")
    
    # Check environment variables as fallback
    if os.getenv("OPENAI_API_KEY"):
        print("ℹ️ OPENAI_API_KEY also found in environment variables (will be used as fallback)")
    
    print("\n==== End of secrets configuration check ====\n")

if __name__ == "__main__":
    # Check which operation to run
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-stripe":
            test_stripe_connection()
        elif sys.argv[1] == "--check-secrets":
            check_secrets_config()
        else:
            print(f"Unknown argument: {sys.argv[1]}")
            print("Available commands:")
            print("  --test-stripe   : Test Stripe API connection")
            print("  --check-secrets : Check Streamlit secrets configuration")
    else:
        # Run all checks
        check_feature_files()
        check_secrets_config()

"""
Account feature page.

This page provides account management functionality for users.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_setup import setup_feature_page

# Set up the page with standard configuration
# For account page, we display subscription status
setup_feature_page(display_subscription=True, required=False)
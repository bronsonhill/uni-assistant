"""
Add Queue Cards with AI feature page.

This page allows users to upload course materials and generate study cards using AI.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_setup import setup_feature_page

# Set up the page with standard configuration
# For this premium feature, we display subscription status but don't require it
setup_feature_page(display_subscription=True, required=False)

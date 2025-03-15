"""
Add Questions Manually feature page.

This page allows users to create new study questions by manually inputting question and answer pairs.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_setup import setup_feature_page

# Set up the page with standard configuration
# This is a free feature that displays subscription status
setup_feature_page(display_subscription=True, required=False)

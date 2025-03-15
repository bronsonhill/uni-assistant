"""
Subject Tutor feature page.

This page provides a chat interface to connect users with an AI study buddy that knows their course materials.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_setup import setup_feature_page

# Set up the page with standard configuration
# This is a premium feature where we don't need to display subscription status in the feature file
# (it's handled in the content file)
setup_feature_page(display_subscription=False, required=False)

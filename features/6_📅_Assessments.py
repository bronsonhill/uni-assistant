"""
Assessments feature page.

This page helps users track exams, assignments, and quizzes with due dates.
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_setup import setup_feature_page

# Set up the page with standard configuration
# This is a premium feature where subscription status is handled in the content file
setup_feature_page(display_subscription=False, required=False)

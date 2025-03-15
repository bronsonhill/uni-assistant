import streamlit as st
import sys
import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import common modules
from mongodb import assessments
import users

# Import st-paywall directly instead of custom paywall module
try:
    from st_paywall import add_auth
except ImportError:
    # Fallback if there's an issue with st_paywall
    def add_auth(required=False, login_button_text="Login", login_button_color="primary", login_sidebar=False):
        if "email" not in st.session_state:
            st.session_state.email = "test@example.com"  # Fallback to test user
        return True  # Always return subscribed in fallback mode

# Premium feature helper functions
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

def run():
    """Main assessments page content"""
    # Check subscription status - required for this premium feature
    # Use st-paywall's add_auth directly instead of check_subscription
    is_subscribed = add_auth(required=True)
    user_email = st.session_state.get("email")
    
    # If user is not subscribed, the add_auth function will redirect them
    # The code below will only execute for subscribed users
    
    st.title("📅 Assessments")
    st.write("Track your upcoming assessments and prioritize your study time.")
    
    if not user_email:
        st.warning("Please log in to use this feature.")
        return
    
    # Session state initialization
    if "assessments" not in st.session_state:
        st.session_state.assessments = []
    
    # Load assessments from MongoDB
    st.session_state.assessments = assessments.get_user_assessments(user_email)
    
    # Set up tabs for different views
    tab_upcoming, tab_past, tab_add = st.tabs(["Upcoming", "Past", "Add New"])
    
    with tab_upcoming:
        display_upcoming_assessments()
    
    with tab_past:
        display_past_assessments()
    
    with tab_add:
        add_assessment_form(user_email)

def display_upcoming_assessments():
    """Display a list of upcoming assessments"""
    st.header("Upcoming Assessments")
    
    # Filter for upcoming assessments (due date >= today)
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    upcoming = [a for a in st.session_state.assessments 
               if a.get("due_date") and datetime.fromisoformat(a["due_date"]) >= today]
    
    if not upcoming:
        st.info("No upcoming assessments. Add some to keep track of your study priorities.")
    else:
        # Sort by due date (closest first)
        upcoming.sort(key=lambda x: datetime.fromisoformat(x["due_date"]))
        
        # Display each assessment
        for i, assessment in enumerate(upcoming):
            with st.container(border=True):
                cols = st.columns([3, 1, 1])
                
                with cols[0]:
                    # Title with subject
                    st.subheader(f"{assessment['title']}")
                    st.caption(f"Subject: {assessment.get('subject', 'Not specified')}")
                    
                    # Description
                    if assessment.get("description"):
                        st.write(assessment["description"])
                    
                    # Due date with days remaining
                    due_date = datetime.fromisoformat(assessment["due_date"])
                    days_remaining = (due_date - datetime.now(timezone.utc)).days + 1
                    
                    if days_remaining <= 0:
                        st.error(f"**Due today!** {format_date(assessment['due_date'])}")
                    elif days_remaining <= 3:
                        st.warning(f"**Due soon:** {format_date(assessment['due_date'])} ({days_remaining} days remaining)")
                    else:
                        st.info(f"**Due:** {format_date(assessment['due_date'])} ({days_remaining} days remaining)")
                
                with cols[1]:
                    st.write("") # Spacing
                    st.write("") # Spacing
                    
                    # Mark as complete button
                    if st.button("Mark Complete", key=f"complete_{i}"):
                        assessment["completed"] = True
                        assessment["completion_date"] = datetime.now(timezone.utc).isoformat()
                        assessments.update_assessment(assessment["_id"], assessment)
                        st.session_state.assessments = assessments.get_user_assessments(st.session_state.get("email", ""))
                        st.rerun()
                
                with cols[2]:
                    st.write("") # Spacing
                    st.write("") # Spacing
                    
                    # Delete button
                    if st.button("Delete", key=f"delete_{i}", type="secondary"):
                        assessments.delete_assessment(assessment["_id"])
                        st.session_state.assessments = assessments.get_user_assessments(st.session_state.get("email", ""))
                        st.rerun()

def display_past_assessments():
    """Display a list of past (completed) assessments"""
    st.header("Past Assessments")
    
    # Filter for past or completed assessments
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    past = [a for a in st.session_state.assessments if 
           (a.get("completed") == True) or 
           (a.get("due_date") and datetime.fromisoformat(a["due_date"]) < today)]
    
    if not past:
        st.info("No past assessments.")
    else:
        # Sort by completion date (most recent first)
        past.sort(key=lambda x: x.get("completion_date") or x.get("due_date") or "", reverse=True)
        
        # Display each assessment
        for i, assessment in enumerate(past):
            with st.expander(assessment["title"]):
                cols = st.columns([3, 1])
                
                with cols[0]:
                    # Details
                    st.write(f"**Subject:** {assessment.get('subject', 'Not specified')}")
                    if assessment.get("description"):
                        st.write(f"**Description:** {assessment['description']}")
                    st.write(f"**Due date:** {format_date(assessment['due_date'])}")
                    
                    # Completion details if available
                    if assessment.get("completed"):
                        completion_text = "Completed"
                        if assessment.get("completion_date"):
                            completion_text += f" on {format_date(assessment['completion_date'])}"
                        st.success(completion_text)
                    else:
                        st.error("Overdue (not completed)")
                
                with cols[1]:
                    # Delete button
                    if st.button("Delete", key=f"delete_past_{i}", type="secondary"):
                        assessments.delete_assessment(assessment["_id"])
                        st.session_state.assessments = assessments.get_user_assessments(st.session_state.get("email", ""))
                        st.rerun()

def add_assessment_form(user_email: str):
    """Form to add a new assessment"""
    st.header("Add New Assessment")
    
    with st.form("new_assessment", clear_on_submit=True):
        title = st.text_input("Assessment Title", placeholder="Midterm Exam")
        subject = st.text_input("Subject", placeholder="Mathematics")
        description = st.text_area("Description (Optional)", placeholder="Covers chapters 1-5")
        due_date = st.date_input("Due Date")
        
        submitted = st.form_submit_button("Add Assessment")
        
        if submitted:
            # Convert date to ISO format with UTC timezone
            due_datetime = datetime.combine(due_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            # Create assessment data
            assessment_data = {
                "user_email": user_email,
                "title": title,
                "subject": subject,
                "description": description,
                "due_date": due_datetime.isoformat(),
                "completed": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Validate data
            if not title:
                st.error("Please enter an assessment title.")
            elif not subject:
                st.error("Please enter a subject.")
            else:
                # Save to database
                assessments.add_assessment(assessment_data)
                st.success(f"Added assessment: {title}")
                st.session_state.assessments = assessments.get_user_assessments(user_email)
                st.rerun()

def format_date(date_str: str) -> str:
    """Format a date string for display"""
    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return "Not specified"
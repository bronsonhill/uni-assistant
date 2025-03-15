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
from features.content.base_content import require_premium, format_date, get_user_email, show_preview_mode

def show_premium_benefits():
    """Show the benefits of premium subscription to encourage sign-up"""
    st.markdown("### 🌟 Upgrade to Premium for these benefits:")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("✅ **Track all your upcoming assessments**")
        st.markdown("✅ **Get automatic deadline reminders**")
        st.markdown("✅ **Prioritize study time effectively**")
    
    with col2:
        st.markdown("✅ **Mark assessments as complete**")
        st.markdown("✅ **Review past assessment history**")
        st.markdown("✅ **Get AI-powered study recommendations**")
    
    st.markdown("---")

def show_demo_content():
    """Display demo content for users in preview mode"""
    # Display sample upcoming assessments
    st.subheader("Preview: Upcoming Assessments")
    
    # Add subject selector
    selected_subject = st.selectbox(
        "Select Subject",
        options=["Computer Science", "Biology", "Law"],
        index=2,  # Default to Law
        key="demo_assessment_subject"
    )
    
    # Show assessments based on selected subject
    if selected_subject == "Computer Science":
        # Computer Science assessments
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Data Structures Final Exam")
                st.caption("Subject: Computer Science")
                st.write("Covers trees, graphs, hash tables, and algorithm complexity analysis")
                st.warning("**Due soon:** May 12, 2023 (3 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="cs_complete_1", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="cs_delete_1", disabled=True)
        
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Software Engineering Project")
                st.caption("Subject: Computer Science")
                st.write("Group project to build a full-stack web application with documentation")
                st.info("**Due:** June 5, 2023 (25 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="cs_complete_2", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="cs_delete_2", disabled=True)
        
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Database Systems Quiz")
                st.caption("Subject: Computer Science")
                st.write("Quiz on SQL optimization, normalization, and transaction processing")
                st.info("**Due:** May 25, 2023 (15 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="cs_complete_3", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="cs_delete_3", disabled=True)
                
        # Show demo add assessment form for CS
        st.subheader("Preview: Add New Assessment")
        
        with st.form("demo_cs_assessment", clear_on_submit=False):
            st.text_input("Assessment Title", value="Machine Learning Project", key="cs_title", disabled=True)
            st.text_input("Subject", value="Computer Science", key="cs_subject", disabled=True)
            st.text_area("Description (Optional)", value="Implement and train a neural network for image classification", key="cs_desc", disabled=True)
            st.date_input("Due Date", key="cs_date", disabled=True)
            st.form_submit_button("Add Assessment", disabled=True)
            
    elif selected_subject == "Biology":
        # Biology assessments
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Cellular Biology Midterm")
                st.caption("Subject: Biology")
                st.write("Covers cell structure, organelles, membrane transport, and cellular respiration")
                st.warning("**Due soon:** May 10, 2023 (1 day remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="bio_complete_1", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="bio_delete_1", disabled=True)
        
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Genetics Lab Report")
                st.caption("Subject: Biology")
                st.write("Analysis of Drosophila melanogaster crossing experiments and gene mapping")
                st.info("**Due:** May 30, 2023 (20 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="bio_complete_2", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="bio_delete_2", disabled=True)
        
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Ecosystem Analysis Project")
                st.caption("Subject: Biology")
                st.write("Field work and report on local ecosystem biodiversity and interactions")
                st.info("**Due:** June 15, 2023 (35 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="bio_complete_3", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="bio_delete_3", disabled=True)
                
        # Show demo add assessment form for Biology
        st.subheader("Preview: Add New Assessment")
        
        with st.form("demo_bio_assessment", clear_on_submit=False):
            st.text_input("Assessment Title", value="Molecular Biology Final Exam", key="bio_title", disabled=True)
            st.text_input("Subject", value="Biology", key="bio_subject", disabled=True)
            st.text_area("Description (Optional)", value="Comprehensive exam covering DNA replication, transcription, and translation", key="bio_desc", disabled=True)
            st.date_input("Due Date", key="bio_date", disabled=True)
            st.form_submit_button("Add Assessment", disabled=True)
    
    else:  # Law assessments (original content)
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Constitutional Law Exam")
                st.caption("Subject: Law")
                st.write("Covers judicial review, federalism, separation of powers, and civil liberties")
                st.warning("**Due soon:** May 15, 2023 (3 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="law_complete_1", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="law_delete_1", disabled=True)
        
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Legal Brief Submission")
                st.caption("Subject: Law")
                st.write("3000-word legal brief on a landmark Supreme Court case")
                st.info("**Due:** June 2, 2023 (21 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="law_complete_2", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="law_delete_2", disabled=True)
        
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            
            with cols[0]:
                st.subheader("Moot Court Competition")
                st.caption("Subject: Law")
                st.write("Prepare oral arguments for mock appellate case on intellectual property")
                st.info("**Due:** June 15, 2023 (34 days remaining)")
            
            with cols[1]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Mark Complete", key="law_complete_3", disabled=True)
            
            with cols[2]:
                st.write("") # Spacing
                st.write("") # Spacing
                st.button("Delete", key="law_delete_3", disabled=True)
        
        # Show demo add assessment form for Law
        st.subheader("Preview: Add New Assessment")
        
        with st.form("demo_law_assessment", clear_on_submit=False):
            st.text_input("Assessment Title", value="Criminal Law Final Exam", key="law_title", disabled=True)
            st.text_input("Subject", value="Law", key="law_subject", disabled=True)
            st.text_area("Description (Optional)", value="Covers criminal liability, defenses, and sentencing guidelines", key="law_desc", disabled=True)
            st.date_input("Due Date", key="law_date", disabled=True)
            st.form_submit_button("Add Assessment", disabled=True)

def run():
    """Main assessments page content"""
    st.title("📅 Assessments")
    st.write("Track your upcoming assessments and prioritize your study time.")
    
    # Check if user is authenticated and subscribed using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    # Handle different access scenarios
    if not is_authenticated:
        # Show preview mode for unauthenticated users
        show_preview_mode(
            "Assessment Tracker",
            """
            Keep track of all your upcoming assessments in one place.
            Get reminders for due dates, mark assessments as complete,
            and organize your study time effectively.
            
            Never miss a deadline again with this powerful tool.
            """
        )
        
        # Show demo content for unauthenticated users
        show_demo_content()
        return
    
    if not is_subscribed:
        # Show premium feature notice for authenticated but non-subscribed users
        st.markdown("""
        Track your upcoming assessments, get deadline reminders, and prioritize your study time
        effectively with this powerful assessment tracker.
        """)
        
        st.warning("This is a premium feature that requires a subscription.")
        show_premium_benefits()
        
        # Show demo content for non-subscribed users
        show_demo_content()
        
        # Add prominent upgrade button
        st.button("Upgrade to Premium", type="primary", disabled=True)
        return
    
    # If we get here, user is authenticated and subscribed - proceed with full functionality
    
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
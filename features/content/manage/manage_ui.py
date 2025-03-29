"""
UI components for manage module.

This module provides UI elements and display functions for the Manage Questions feature.
"""
import streamlit as st
import hashlib
import pandas as pd
import altair as alt
import datetime
from typing import Dict, List, Any, Optional

# Import core functionality
from features.content.manage.manage_core import (
    get_score_emoji,
    get_metrics_for_questions,
    handle_delete_question,
    get_subject_choices,
    get_week_choices,
    get_questions_for_subject_week
)

# Import from Home
from Home import (
    update_question, 
    save_data, 
    calculate_weighted_score,
)

# Import score setting functions directly from mongodb package
from mongodb import (
    get_user_score_settings
)

def display_metrics(questions: List[Dict], user_email: str):
    """Display metrics and visualizations for a set of questions, using user settings."""
    # Get user's score calculation settings
    score_settings = get_user_score_settings(user_email)
    decay_factor = score_settings.get("decay_factor")
    forgetting_decay_factor = score_settings.get("forgetting_decay_factor")

    # Pass factors to get_metrics_for_questions
    metrics = get_metrics_for_questions(questions, decay_factor, forgetting_decay_factor)
    
    # Check if we have scores to display
    if metrics["score_count"] > 0:
        # Create metrics row
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            avg_score = metrics["avg_score"]
            emoji = get_score_emoji(avg_score)
            st.metric("Average Score", f"{emoji} {avg_score:.1f}/5")
        
        with metrics_col2:
            # Count questions in each category
            good_count = metrics["good_count"]
            medium_count = metrics["medium_count"]
            low_count = metrics["low_count"]
            # Use markdown with smaller custom styling instead of st.metric
            st.markdown(
                f"""
                <div style='text-align: center'>
                <p style='font-size: 0.9rem; font-weight: 600; margin-bottom: 0px'>Knowledge Level</p>
                <p style='font-size: 1.0rem; font-weight: 500'>🟢 {good_count} | 🟠 {medium_count} | 🔴 {low_count}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        
        with metrics_col3:
            # Calculate percent of questions with good scores
            mastery_percent = metrics["mastery_percent"]
            st.metric("Mastery Level", f"{mastery_percent:.0f}%")
    else:
        st.info("No scores available yet. Practice with these questions to see metrics.")

def create_score_histogram(scores):
    """Create a histogram visualization of scores"""
    # Convert scores to a DataFrame for the histogram
    score_df = pd.DataFrame({'score': scores})
    
    # Create the histogram
    histogram = alt.Chart(score_df).mark_bar().encode(
        alt.X('score:Q', bin=alt.Bin(maxbins=5, extent=[0, 5]), title='Score'),
        alt.Y('count()', title='Number of Questions'),
        alt.Color('score:Q', scale=alt.Scale(scheme='redyellowgreen', domain=[0, 5]), title='Score'),
        tooltip=['count()', alt.Tooltip('score:Q', title='Score Range')]
    ).properties(
        title='Score Distribution',
        width='container',
        height=200
    )
    
    st.altair_chart(histogram, use_container_width=True)

def display_question(index, question, subject, week, user_email):
    """Display a single question, using user score settings."""
    # Create unique hash for this question
    question_hash = hashlib.md5(f"{subject}_{week}_{index}_{question['question'][:20]}".encode()).hexdigest()[:8]
    
    # Get user's score calculation settings
    score_settings = get_user_score_settings(user_email)
    decay_factor = score_settings.get("decay_factor")
    forgetting_decay_factor = score_settings.get("forgetting_decay_factor")

    with st.container(border=True):
        # Get score info
        scores = question.get("scores", [])
        last_practiced = question.get("last_practiced")
        # Calculate score using user factors
        weighted_score = calculate_weighted_score(
            scores, 
            last_practiced=last_practiced, 
            decay_factor=decay_factor, 
            forgetting_decay_factor=forgetting_decay_factor
        )
        score_display = f"{get_score_emoji(weighted_score)} {weighted_score:.1f}/5" if weighted_score is not None else "⚪ 0/5"
        
        col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
        
        with col1:
            st.markdown(f"**Q{index+1}: {question['question']}**")
        
        with col2:
            st.markdown(f"Score: **{score_display}**")
        
        with col3:
            # Use unique hash in the key
            if st.button("Edit", key=f"edit_{question_hash}", use_container_width=True):
                st.session_state.editing = True
                st.session_state.edit_subject = subject
                st.session_state.edit_week = week
                st.session_state.edit_idx = index
                st.rerun()
        
        with col4:
            # Use unique hash in the key
            if st.button("Delete", key=f"delete_{question_hash}", use_container_width=True):
                st.session_state.data = handle_delete_question(
                    st.session_state.data, subject, week, index, user_email
                )
                st.success("Question deleted!")
                st.rerun()
        
        # Pass user factors to details display
        with st.expander(f"View details for Q{index+1}"):
            display_question_details(question, decay_factor, forgetting_decay_factor)

def display_question_details(question, decay_factor, forgetting_decay_factor):
    """Display details, using provided score factors."""
    # Question content
    st.write("**Question:**")
    st.write(question["question"])
    
    # Expected answer
    st.write("**Expected Answer:**")
    st.write(question["answer"] if question["answer"] else "No answer provided")
    
    # Score history
    scores = question.get("scores", [])
    last_practiced = question.get("last_practiced")
    # Calculate score using provided factors
    weighted_score = calculate_weighted_score(
        scores, 
        last_practiced=last_practiced, 
        decay_factor=decay_factor, 
        forgetting_decay_factor=forgetting_decay_factor
    )
    
    # Display score history header and current score
    st.write("**Score History:**")
    if weighted_score is not None:
        emoji = get_score_emoji(weighted_score)
        st.metric("Current Score", f"{emoji} {weighted_score:.1f}/5")
    else:
        st.metric("Current Score", "⚪ 0/5")
    
    # Show past answers if available
    if scores and any("user_answer" in s for s in scores):
        st.write("**Past Answers:**")
        for idx, score_entry in enumerate(reversed(scores)):
            if "user_answer" in score_entry:
                display_past_answer(idx, score_entry)

def display_past_answer(index, score_entry):
    """Display a past answer with its score and timestamp"""
    user_answer = score_entry["user_answer"]
    # Format timestamp
    timestamp = score_entry["timestamp"]
    date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    
    # Display score and answer with timestamp
    score = score_entry['score']
    emoji = get_score_emoji(score)
    
    st.markdown(f"**Attempt {index+1}** {emoji} (Score: {score:.1f}/5) - {date_str}")
    st.markdown(f"*{user_answer}*")
    st.markdown("---")

def display_questions(user_email, is_subscribed):
    """
    Display the list of questions with filtering options.
    """
    # --- Remove Settings Button and Dialog Logic --- 
    # if "show_score_settings" not in st.session_state:
    #     st.session_state.show_score_settings = False
    # settings_col, filter_col1, filter_col2 = st.columns([1, 4, 4])
    # with settings_col:
    #     if st.button("⚙️", help="Score Calculation Settings"):
    #         st.session_state.show_score_settings = not st.session_state.show_score_settings
    #         st.rerun()
    # if st.session_state.show_score_settings:
    #     display_score_settings_dialog(user_email)
    #     st.markdown("---")

    # --- Keep Existing Filter Logic (adjust columns) --- 
    filter_col1, filter_col2 = st.columns(2) # Use 2 columns for filters now
    with filter_col1:
        # Select subject (use original key)
        subject_choices = get_subject_choices(st.session_state.data)
        if not subject_choices:
             st.info("No subjects found. Add questions first.")
             return # Exit if no subjects
        subject_to_view = st.selectbox("Select Subject", subject_choices, key="view_subject")
    
    if subject_to_view:
        with filter_col2:
            # Select week (use original key)
            week_options = get_week_choices(st.session_state.data, subject_to_view)
            if not week_options:
                st.info(f"No weeks found for {subject_to_view}. Add questions first.")
                return
            week_to_view = st.selectbox("Select Week", week_options, key="view_week")
        
        if week_to_view:
            # --- Existing Question Display --- 
            questions = get_questions_for_subject_week(st.session_state.data, subject_to_view, week_to_view)
            
            st.subheader(f"Questions for {subject_to_view} - Week {week_to_view}")
            
            # Calculate and display metrics (still needs user factors)
            display_metrics(questions, user_email)
            
            # Display questions (still needs user factors)
            for i, q in enumerate(questions):
                display_question(i, q, subject_to_view, week_to_view, user_email)

def handle_edit_form():
    """Handle the edit question form"""
    st.subheader("Edit Question")
    
    with st.form("edit_question_form"):
        # Get the current data for the question being edited
        week_str = st.session_state.edit_week
        question_idx = st.session_state.edit_idx
        subject = st.session_state.edit_subject
        current_question = st.session_state.data[subject][week_str][question_idx]
        
        # Show which question is being edited
        st.markdown(f"**Editing:** Subject: **{subject}**, Week: **{week_str}**")
        
        # Edit fields
        edited_question = st.text_area("Question", value=current_question["question"], height=100)
        edited_answer = st.text_area("Expected Answer", value=current_question["answer"], height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("Save Changes", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        
        if submit and edited_question:
            # Get user email directly from session state
            user_email = st.session_state.get("email")
            st.session_state.data = update_question(
                st.session_state.data, subject, int(week_str), question_idx, 
                edited_question, edited_answer, email=user_email
            )
            save_data(st.session_state.data, email=user_email)
            st.session_state.editing = False
            st.success("Question updated successfully!")
            st.rerun()
        
        if cancel:
            st.session_state.editing = False
            st.rerun() 
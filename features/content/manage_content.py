"""
Manage Questions content module.

This module provides the content for the Manage Questions page.
"""
import streamlit as st
import hashlib
import numpy as np
import pandas as pd
import altair as alt
import datetime
from . import base_content

# Import specific functions needed from Home
from Home import save_data, delete_question, update_question, calculate_weighted_score

def run():
    """Main manage questions page content - this gets run by the navigation system"""
    # Initialize data in session state
    user_email = base_content.get_user_email()
    base_content.init_data(email=user_email)
    
    # Initialize editing state if needed
    if "editing" not in st.session_state:
        st.session_state.editing = False
    if "edit_subject" not in st.session_state:
        st.session_state.edit_subject = ""
    if "edit_week" not in st.session_state:
        st.session_state.edit_week = ""
    if "edit_idx" not in st.session_state:
        st.session_state.edit_idx = -1
    
    st.title("📝 Manage Questions")
    st.markdown("""
    View, edit, and delete your existing questions on this page. 
    Questions are organized by subject and week number.
    
    Each question now shows its current score and includes a history of your past answers.
    """)
    
    # Edit question form
    if st.session_state.editing:
        _handle_edit_form(user_email)
    
    # Display existing questions
    elif not st.session_state.data:
        st.info("No questions added yet. Use the 'Add Questions' page to create some.")
    else:
        _display_questions(user_email)

def _handle_edit_form(user_email):
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

def _display_questions(user_email):
    """Display the list of questions with filtering options"""
    # Select subject
    subject_to_view = st.selectbox("Select Subject", list(st.session_state.data.keys()), key="view_subject")
    
    if subject_to_view:
        # Select week
        week_options = list(st.session_state.data[subject_to_view].keys())
        # Filter out metadata entries that aren't weeks
        week_options = [w for w in week_options if w != "vector_store_metadata" and w.isdigit()]
        
        if not week_options:
            st.info(f"No weeks found for {subject_to_view}. Add questions for this subject first.")
            return
            
        week_to_view = st.selectbox("Select Week", sorted(week_options, key=int), key="view_week")
        
        if week_to_view:
            questions = st.session_state.data[subject_to_view][week_to_view]
            
            st.subheader(f"Questions for {subject_to_view} - Week {week_to_view}")
            
            # Calculate and display metrics for these questions
            _display_metrics(questions)
            
            # Display questions with delete and edit buttons
            for i, q in enumerate(questions):
                _display_question(i, q, subject_to_view, week_to_view, user_email)

def _display_metrics(questions):
    """Display metrics and visualizations for a set of questions"""
    # Collect all weighted scores for questions
    all_scores = []
    for q in questions:
        scores = q.get("scores", [])
        weighted_score = calculate_weighted_score(scores)
        if weighted_score is not None:
            all_scores.append(weighted_score)
    
    # Calculate and display metrics
    st.write(f"Found {len(questions)} questions")
    
    # Create metrics row
    if all_scores:
        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
        
        with metrics_col1:
            avg_score = np.mean(all_scores)
            emoji = _get_score_emoji(avg_score)
            st.metric("Average Score", f"{emoji} {avg_score:.1f}/5")
        
        with metrics_col2:
            # Count questions in each category
            good_count = sum(1 for s in all_scores if s >= 4)
            medium_count = sum(1 for s in all_scores if 2.5 <= s < 4)
            low_count = sum(1 for s in all_scores if s < 2.5)
            st.metric("Knowledge Level", f"🟢 {good_count} | 🟠 {medium_count} | 🔴 {low_count}")
            
        with metrics_col3:
            # Calculate percent of questions with good scores
            if len(all_scores) > 0:
                mastery_percent = (good_count / len(all_scores)) * 100
                st.metric("Mastery Level", f"{mastery_percent:.0f}%")
        
        # Create histogram of scores
        with st.expander("Score Distribution", expanded=True):
            _create_score_histogram(all_scores)

def _create_score_histogram(scores):
    """Create a histogram visualization of scores"""
    # Create a DataFrame for the histogram
    score_df = pd.DataFrame({'score': scores})
    
    # Create the histogram
    histogram = alt.Chart(score_df).mark_bar().encode(
        alt.X('score:Q', bin=alt.Bin(maxbins=10), title='Score'),
        alt.Y('count()', title='Number of Questions'),
        alt.Color('score:Q', scale=alt.Scale(scheme='redyellowgreen'), title='Score'),
        tooltip=['count()', alt.Tooltip('score:Q', title='Score Range')]
    ).properties(
        title='Score Distribution',
        width='container',
        height=200
    )
    
    st.altair_chart(histogram, use_container_width=True)

def _display_question(index, question, subject, week, user_email):
    """Display a single question with its details and actions"""
    # Create unique hash for this question
    question_hash = hashlib.md5(f"{subject}_{week}_{index}_{question['question'][:20]}".encode()).hexdigest()[:8]
    
    with st.container(border=True):
        # Get score info
        scores = question.get("scores", [])
        weighted_score = calculate_weighted_score(scores)
        score_display = f"{_get_score_emoji(weighted_score)} {weighted_score:.1f}/5" if weighted_score is not None else "⚪ 0/5"
        
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
                st.session_state.data = delete_question(
                    st.session_state.data, subject, int(week), index, email=user_email
                )
                save_data(st.session_state.data, email=user_email)
                st.success("Question deleted!")
                st.rerun()
        
        # Add details expander below all columns
        with st.expander(f"View details for Q{index+1}"):
            _display_question_details(question)

def _display_question_details(question):
    """Display details for a question including answer and score history"""
    # Question content
    st.write("**Question:**")
    st.write(question["question"])
    
    # Expected answer
    st.write("**Expected Answer:**")
    st.write(question["answer"] if question["answer"] else "No answer provided")
    
    # Score history
    scores = question.get("scores", [])
    weighted_score = calculate_weighted_score(scores)
    
    # Display score history header and current score
    st.write("**Score History:**")
    if weighted_score is not None:
        emoji = _get_score_emoji(weighted_score)
        st.metric("Current Score", f"{emoji} {weighted_score:.1f}/5")
    else:
        st.metric("Current Score", "⚪ 0/5")
    
    # Show past answers if available
    if scores and any("user_answer" in s for s in scores):
        st.write("**Past Answers:**")
        for idx, score_entry in enumerate(reversed(scores)):
            if "user_answer" in score_entry:
                _display_past_answer(idx, score_entry)

def _display_past_answer(index, score_entry):
    """Display a past answer with its score and timestamp"""
    user_answer = score_entry["user_answer"]
    # Format timestamp
    timestamp = score_entry["timestamp"]
    date_str = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")
    
    # Display score and answer with timestamp
    score = score_entry['score']
    emoji = _get_score_emoji(score)
    
    st.markdown(f"**Attempt {index+1}** {emoji} (Score: {score:.1f}/5) - {date_str}")
    st.markdown(f"*{user_answer}*")
    st.markdown("---")

def _get_score_emoji(score):
    """Get an appropriate emoji for a score value"""
    if score is None:
        return "⚪"
    elif score >= 4:
        return "🟢"  # Green for good scores
    elif score >= 2.5:
        return "🟠"  # Orange for medium scores
    else:
        return "🔴"  # Red for low scores
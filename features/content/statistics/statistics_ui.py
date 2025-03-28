"""
UI components for statistics module.

This module handles the display and visualization of statistics.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import altair as alt
from features.content.statistics.statistics_core import get_last_30_days_attempts, get_score_distribution

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
        height=350
    )
    
    return histogram

def display_overview_stats(stats: Dict[str, Any]) -> None:
    """Display overview statistics section."""
    st.header("Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Total Content",
            stats["total_content"],
            help="Total number of questions and content items"
        )
    
    with col2:
        st.metric(
            "Current Streak",
            f"{stats['streak_days']} days",
            help="Consecutive days of practice"
        )
    
    with col3:
        st.metric(
            "Average Score",
            f"{stats['average_practice_score']:.1f}/5",
            help="Average score across all practice sessions"
        )

def display_content_stats(stats: Dict[str, Any]) -> None:
    """Display content statistics section."""
    st.header("Content Analysis")
    
    # Display total questions
    st.metric("Total Questions", stats["total_questions"])
    
    # Display recent additions
    if stats["recent_additions"]:
        st.subheader("Recent Additions")
        for item in stats["recent_additions"]:
            st.text(f"• {item['subject']} - Week {item['week']}: {item['question']}")
    
    # Display questions by subject at the bottom
    if stats["questions_by_subject"]:
        st.subheader("Questions by Subject")
        fig = px.pie(
            values=list(stats["questions_by_subject"].values()),
            names=list(stats["questions_by_subject"].keys()),
            title="Content Distribution by Subject"
        )
        st.plotly_chart(fig, use_container_width=True)

def display_practice_stats(stats: Dict[str, Any]) -> None:
    """Display practice statistics section."""
    st.header("Practice Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Questions Attempted",
            stats["total_questions_attempted"],
            help="Total number of questions attempted"
        )
    
    with col2:
        st.metric(
            "Correct Answers",
            stats["correct_answers"],
            help="Total number of correct answers"
        )
    
    # Display practice attempts over last 30 days
    if stats["practice_history"]:
        recent_attempts = get_last_30_days_attempts(stats["practice_history"])
        if recent_attempts:
            st.subheader("Practice Activity (Last 30 Days)")
            
            # Group attempts by date
            attempts_by_date = {}
            for attempt in recent_attempts:
                date = datetime.fromtimestamp(attempt["date"]).date()
                attempts_by_date[date] = attempts_by_date.get(date, 0) + 1
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=list(attempts_by_date.keys()),
                y=list(attempts_by_date.values()),
                name="Daily Attempts"
            ))
            fig.update_layout(
                title="Daily Practice Attempts",
                xaxis_title="Date",
                yaxis_title="Number of Attempts",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Display score distribution
    if stats["practice_history"]:
        st.subheader("Score Distribution")
        scores = get_score_distribution(stats["practice_history"])
        histogram = create_score_histogram(scores)
        st.altair_chart(histogram, use_container_width=True)
    
    # Display subject performance with threshold selection
    if stats["subject_performance"]:
        st.subheader("Subject Performance")
        
        # Add threshold selection with info
        col1, col2 = st.columns([1, 4])
        with col1:
            threshold = st.selectbox(
                "Success Threshold",
                options=[3.0, 3.5, 4.0, 4.5],
                index=1,  # Default to 3.5
                help="The minimum score (out of 5) required to consider an attempt successful. "
                     "Higher thresholds mean more strict success criteria."
            )
        
        # Calculate success rates with selected threshold
        subject_stats = []
        for subject, perf in stats["subject_performance"].items():
            if perf["attempts"] > 0:
                # Get all scores for this subject
                subject_scores = [
                    attempt["score"] 
                    for attempt in stats["practice_history"] 
                    if attempt["subject"] == subject
                ]
                correct_answers = sum(1 for score in subject_scores if score >= threshold)
                success_rate = (correct_answers / perf["attempts"]) * 100
                subject_stats.append({
                    "subject": subject,
                    "success_rate": success_rate,
                    "attempts": perf["attempts"]
                })
        
        if subject_stats:
            # Sort by success rate
            subject_stats.sort(key=lambda x: x["success_rate"], reverse=True)
            
            # Create bar chart
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=[s["subject"] for s in subject_stats],
                y=[s["success_rate"] for s in subject_stats],
                text=[f"{s['success_rate']:.1f}% ({s['attempts']} attempts)" for s in subject_stats],
                textposition='auto',
                name="Success Rate"
            ))
            fig.update_layout(
                title=f"Success Rate by Subject (Threshold: {threshold}/5)",
                xaxis_title="Subject",
                yaxis_title="Success Rate (%)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
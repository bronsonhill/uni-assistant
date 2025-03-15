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

def show_demo_content():
    """Display demo content for users in preview mode"""
    st.title("📝 Manage Questions")
    
    # Show preview description
    base_content.show_preview_mode(
        "Question Manager",
        """
        View, edit, and delete your existing questions on this page.
        Questions are organized by subject and week number.
        
        Each question shows its current score and includes a history of your past answers.
        """
    )
    
    # Create the subject/week selection for demo
    st.subheader("Demo: Question Management")
    
    # Create dropdown for subject, defaulting to Computer Science
    subject_to_view = st.selectbox(
        "Select Subject",
        ["Computer Science", "Biology", "Law"], 
        index=1,  # Default to Biology
        key="demo_view_subject", 
        disabled=False
    )
    
    # Create dropdown for week, defaulting to Week 1
    week_to_view = st.selectbox(
        "Select Week",
        ["1", "2", "3"],
        index=0, 
        key="demo_view_week",
        disabled=False
    )
    
    # Show a mock metrics section
    st.subheader(f"Questions for {subject_to_view} - Week {week_to_view}")
    
    # Display mock metrics
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    
    with metrics_col1:
        st.metric("Average Score", "🟠 3.5/5")
    
    with metrics_col2:
        st.metric("Knowledge Level", "🟢 2 | 🟠 1 | 🔴 0")
        
    with metrics_col3:
        st.metric("Mastery Level", "67%")
    
    # Show mock histogram
    with st.expander("Score Distribution", expanded=True):
        # Sample data for the histogram
        scores = [3.2, 3.5, 4.0]
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
    
    # Select questions based on the subject
    if subject_to_view == "Computer Science":
        # Computer Science questions
        _display_demo_question(
            0,
            {
                "question": "Explain the difference between stack and heap memory allocation.",
                "answer": "Stack memory allocation is used for static memory allocation where variables are allocated and deallocated in a last-in-first-out order, typically for local variables and function calls. It's faster but limited in size. Heap memory allocation is used for dynamic memory allocation at runtime, managed by the programmer or garbage collector. It's slower but allows for larger and variable-sized data structures with lifetimes not tied to specific scopes.",
                "scores": [
                    {"score": 4.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Stack memory is for static allocation (function calls, local variables) and follows LIFO order, while heap is for dynamic allocation with manual management and longer lifetimes."}
                ]
            },
            "cs_q1"
        )
        
        _display_demo_question(
            1,
            {
                "question": "What is object-oriented programming and what are its key principles?",
                "answer": "Object-oriented programming (OOP) is a programming paradigm based on the concept of objects that contain data and code. It organizes software design around data, or objects, rather than functions and logic. Key principles include encapsulation (hiding internal states), inheritance (parent-child class relationships), polymorphism (different implementations of the same interface), and abstraction (simplifying complex systems).",
                "scores": [
                    {"score": 3.5, "timestamp": "2023-11-15T14:30:00", "user_answer": "OOP is programming with objects that have data and methods. The main principles are encapsulation, inheritance, polymorphism, and abstraction."}
                ]
            },
            "cs_q2"
        )
        
        _display_demo_question(
            2,
            {
                "question": "Describe the time complexity of common sorting algorithms and their trade-offs.",
                "answer": "Bubble Sort: O(n²) average and worst case, simple but inefficient. Selection Sort: O(n²) in all cases, minimal memory usage. Insertion Sort: O(n²) average and worst, but O(n) for nearly sorted data. Merge Sort: O(n log n) in all cases, stable but requires O(n) extra space. Quick Sort: O(n log n) average, O(n²) worst case, in-place but unstable. Heap Sort: O(n log n) in all cases, in-place but slower than quicksort in practice.",
                "scores": [
                    {"score": 3.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Bubble, selection, insertion sorts are O(n²). Merge and quick sorts are O(n log n) but merge sort needs extra space while quicksort can degrade to O(n²)."}
                ]
            },
            "cs_q3"
        )
    elif subject_to_view == "Biology":
        # Biology questions (same as original)
        _display_demo_question(
            0,
            {
                "question": "Explain the difference between mitosis and meiosis in cell division.",
                "answer": "Mitosis is cell division that results in two identical daughter cells with the same chromosome count as the parent cell, used for growth and repair. Meiosis produces four genetically diverse cells with half the chromosomes, used for sexual reproduction.",
                "scores": [
                    {"score": 4.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Mitosis creates two identical cells with same chromosome count, while meiosis creates four cells with half the chromosomes and genetic diversity."}
                ]
            },
            "bio_q1"
        )
        
        _display_demo_question(
            1,
            {
                "question": "Describe the structure and function of chloroplasts in plant cells.",
                "answer": "Chloroplasts are organelles in plant cells with a double membrane, stroma, and thylakoids arranged in grana. They contain chlorophyll and perform photosynthesis, converting light energy to chemical energy (ATP and NADPH) and fixing carbon into glucose.",
                "scores": [
                    {"score": 3.5, "timestamp": "2023-11-15T14:30:00", "user_answer": "Chloroplasts are plant organelles with double membranes that contain chlorophyll and carry out photosynthesis to convert light energy into chemical energy."}
                ]
            },
            "bio_q2"
        )
        
        _display_demo_question(
            2,
            {
                "question": "What are the main components of the cell membrane and how does its structure relate to its function?",
                "answer": "The cell membrane consists of a phospholipid bilayer with embedded proteins, cholesterol, and glycoproteins/glycolipids. This structure creates selective permeability, allowing the membrane to control what enters and exits the cell while maintaining fluidity and enabling functions like cell signaling.",
                "scores": [
                    {"score": 3.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Cell membranes are made of phospholipid bilayers with proteins. The structure allows selective permeability and helps control what moves in and out of the cell."}
                ]
            },
            "bio_q3"
        )
    else:  # Law
        # Law questions
        _display_demo_question(
            0,
            {
                "question": "Explain the difference between common law and civil law legal systems.",
                "answer": "Common law systems are based on precedent and judge-made law, where prior court decisions bind future cases, prominent in the UK and former colonies. Civil law systems are codified, relying primarily on comprehensive written codes and statutes, dominant in continental Europe, Latin America, and parts of Asia and Africa. Common law is more flexible and judge-centered, while civil law is more structured and legislation-centered.",
                "scores": [
                    {"score": 4.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Common law is based on precedent (judge-made law) while civil law is based on comprehensive written codes and statutes."}
                ]
            },
            "law_q1"
        )
        
        _display_demo_question(
            1,
            {
                "question": "What is the doctrine of precedent (stare decisis) and why is it important in common law systems?",
                "answer": "The doctrine of precedent (stare decisis) is the principle that courts should follow prior decisions when ruling on similar cases. It's vital in common law systems because it ensures consistency and predictability in the law, promotes equality by treating similar cases alike, provides efficiency in legal reasoning, creates stability in the legal system, and allows for gradual, organic development of law through distinguishing cases and occasional overruling.",
                "scores": [
                    {"score": 3.5, "timestamp": "2023-11-15T14:30:00", "user_answer": "Stare decisis means courts follow previous decisions. It's important because it creates consistency, predictability, and equality in how cases are decided."}
                ]
            },
            "law_q2"
        )
        
        _display_demo_question(
            2,
            {
                "question": "Describe the key elements necessary to form a legally binding contract.",
                "answer": "A legally binding contract requires offer (a clear proposal), acceptance (unequivocal agreement to the offer), consideration (something of value exchanged), intention to create legal relations (parties intend to be legally bound), capacity (parties must be legally able to enter contracts), and legality (the purpose must be legal). Some contracts also require specific formalities like writing or witnessing.",
                "scores": [
                    {"score": 3.0, "timestamp": "2023-11-15T14:30:00", "user_answer": "Contract formation needs an offer, acceptance, consideration, intention to create legal relations, legal capacity, and a lawful purpose."}
                ]
            },
            "law_q3"
        )

def _display_demo_question(index, question, key_prefix):
    """Display a demo question with its details and actions"""
    with st.container(border=True):
        # Get score info
        scores = question.get("scores", [])
        weighted_score = calculate_weighted_score(scores) if scores else 3.5
        score_display = f"{_get_score_emoji(weighted_score)} {weighted_score:.1f}/5" if weighted_score is not None else "⚪ 0/5"
        
        col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
        
        with col1:
            st.markdown(f"**Q{index+1}: {question['question']}**")
        
        with col2:
            st.markdown(f"Score: **{score_display}**")
        
        with col3:
            st.button("Edit", key=f"demo_edit_{key_prefix}", use_container_width=True, disabled=True)
        
        with col4:
            st.button("Delete", key=f"demo_delete_{key_prefix}", use_container_width=True, disabled=True)
        
        # Add details expander below all columns
        with st.expander(f"View details for Q{index+1}"):
            # Question content
            st.write("**Question:**")
            st.write(question["question"])
            
            # Expected answer
            st.write("**Expected Answer:**")
            st.write(question["answer"] if question["answer"] else "No answer provided")
            
            # Score history
            st.write("**Score History:**")
            emoji = _get_score_emoji(weighted_score)
            st.metric("Current Score", f"{emoji} {weighted_score:.1f}/5")
            
            # Show past answers if available
            if scores:
                st.write("**Past Answers:**")
                for idx, score_entry in enumerate(reversed(scores)):
                    # Display a past answer with its score and timestamp
                    user_answer = score_entry["user_answer"]
                    score = score_entry["score"]
                    timestamp = score_entry.get("timestamp", "2023-11-15T14:30:00")
                    
                    # Parse and format the timestamp
                    try:
                        dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%b %d, %Y at %I:%M %p")
                    except (ValueError, AttributeError):
                        formatted_date = "Unknown date"
                    
                    # Display the answer
                    with st.container(border=True):
                        st.markdown(f"**Attempt {idx+1}** - {formatted_date}")
                        st.markdown(f"Score: **{_get_score_emoji(score)} {score}/5**")
                        st.markdown(f"Your answer: {user_answer}")

def _handle_edit_form():
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

def _display_questions():
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
                _display_question(i, q, subject_to_view, week_to_view)

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

def _display_question(index, question, subject, week):
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
                # Get email from session state directly
                user_email = st.session_state.get("email")
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

def run():
    """Main manage questions page content - this gets run by the navigation system"""
    # Check if user is logged in and subscribed using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None  # User is authenticated if email exists
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    # Show demo content for unauthenticated users
    if not is_authenticated:
        show_demo_content()
        return
    
    # Initialize data in session state for authenticated users
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
        _handle_edit_form()
    
    # Display existing questions or show demo content for authenticated but unsubscribed users
    elif not st.session_state.data:
        if is_subscribed:
            st.info("No questions added yet. Use the 'Add Questions' page to create some.")
        else:
            # For authenticated but unsubscribed users with no data, show demo content
            st.info("No questions added yet. Here's a preview of what the question management looks like:")
            show_demo_content()
    else:
        _display_questions()
        
        # Show premium preview for authenticated but unsubscribed users with existing data
        if is_authenticated and not is_subscribed:
            st.markdown("---")
            st.subheader("Premium Features Preview")
            st.markdown("""
            With a premium subscription, you'll get access to additional features:
            
            - Advanced analytics on your learning progress
            - AI-powered study recommendations
            - Enhanced question organization and tagging
            - Study schedule optimization
            """)
            
            # Add upgrade button
            st.button("Upgrade to Premium", type="primary", disabled=True)
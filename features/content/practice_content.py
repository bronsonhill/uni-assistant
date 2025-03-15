import streamlit as st
import sys
import os
import random
import time
from datetime import datetime
from typing import Optional, Dict, List, Any, Tuple, Callable
from functools import wraps

# Add parent directory to path so we can import from Home.py and ai_feedback.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import functions from Home.py
import Home
from ai_feedback import evaluate_answer, chat_about_question
from mongodb.queue_cards import save_ai_feedback, update_single_question_score
from features.content.base_content import check_auth_for_action, show_preview_mode, get_user_email

# No longer importing auth, using session state directly instead

# Use functions from Home module
load_data = Home.load_data
save_data = Home.save_data
update_question_score = Home.update_question_score
calculate_weighted_score = Home.calculate_weighted_score

# Constants
KNOWLEDGE_LEVEL_OPTIONS = {
    0: "0 - 🆕 New questions only",
    1: "1 - 🟥 New + struggling questions",
    2: "2 - 🟧 Questions needing improvement",
    3: "3 - 🟨 Questions with moderate knowledge",
    4: "4 - 🟩 Questions with good knowledge",
    5: "5 - ⬜ All questions"
}

SCORE_EMOJI_MAP = {
    1: "🔴",
    2: "🟠",
    3: "🟠",
    4: "🟢",
    5: "🟢"
}

def get_score_emoji(score: int) -> str:
    """Return the appropriate emoji for a given score"""
    if score >= 4:
        return "🟢"
    elif score >= 2:
        return "🟠"
    else:
        return "🔴"

# Cache the loading of data with TTL of 10 minutes to balance freshness with performance
@st.cache_data(ttl=600)
def cached_load_data(user_email):
    """Cached version of load_data to reduce repeated disk/database access"""
    return load_data(user_email)

# Cache the vector store ID lookups
@st.cache_data(ttl=1800)  # 30 minutes TTL
def get_cached_vector_store_id(subject: str, week: str, data):
    """Get vector store ID for the current subject and week if it exists"""
    if (subject in data and 
        "vector_store_metadata" in data[subject] and 
        week in data[subject]["vector_store_metadata"]):
        return data[subject]["vector_store_metadata"][week].get("id")
    return None

def is_metadata_key(key: str) -> bool:
    """Check if a key is a metadata key (not a week)"""
    return key == "vector_store_metadata" or not key.isdigit()

def filter_weeks(data: Dict, subject: str) -> List[str]:
    """Get a list of week keys for a subject, filtering out metadata"""
    return [w for w in data[subject].keys() if not is_metadata_key(w)]

def collect_all_weeks(data: Dict) -> List[str]:
    """Collect all week numbers across all subjects"""
    all_weeks = set()
    for subject in data.keys():
        weeks = filter_weeks(data, subject)
        all_weeks.update(weeks)
    return sorted(list(all_weeks), key=int) if all_weeks else []

def build_question_item(subject: str, week: str, q_idx: int, q_data: Dict) -> Dict:
    """Create a standardized question item for the queue"""
    weighted_score = None
    if "scores" in q_data and q_data["scores"]:
        weighted_score = calculate_weighted_score(q_data["scores"])
    
    return {
        "subject": subject,
        "week": week,
        "question_idx": q_idx,
        "question": q_data["question"],
        "answer": q_data["answer"],
        "weighted_score": weighted_score,
        "last_practiced": q_data.get("last_practiced", None)
    }

def should_include_question(q_data: Dict, min_score: int) -> bool:
    """Determine if a question should be included based on score threshold"""
    if "scores" not in q_data or not q_data["scores"]:
        return True  # Include questions with no scores
    
    weighted_score = calculate_weighted_score(q_data["scores"])
    return weighted_score <= min_score

def filter_questions_by_subject_week(data: Dict, subject: str, week: str, min_score: int) -> List[Dict]:
    """Filter questions for a specific subject and week"""
    questions = []
    for i, q in enumerate(data[subject][week]):
        if should_include_question(q, min_score):
            questions.append(build_question_item(subject, week, i, q))
    return questions

# Cache the filtered question queue to avoid rebuilding it frequently
@st.cache_data(ttl=300)  # 5 minutes TTL
def build_cached_queue(data, selected_subject, selected_week, practice_order, min_score):
    """Build a cached queue of questions based on selected filters and score threshold"""
    questions_queue = []
    all_subjects = list(data.keys())
    all_weeks = collect_all_weeks(data)
    
    # Build queue based on filters
    if selected_subject == "All" and selected_week == "All":
        # All subjects, all weeks
        for subject in all_subjects:
            for week in filter_weeks(data, subject):
                questions_queue.extend(filter_questions_by_subject_week(data, subject, week, min_score))
    elif selected_subject == "All":
        # All subjects, specific week
        for subject in all_subjects:
            if selected_week in data[subject]:
                questions_queue.extend(filter_questions_by_subject_week(data, subject, selected_week, min_score))
    elif selected_week == "All":
        # Specific subject, all weeks
        for week in filter_weeks(data, selected_subject):
            questions_queue.extend(filter_questions_by_subject_week(data, selected_subject, week, min_score))
    else:
        # Specific subject, specific week
        questions_queue.extend(filter_questions_by_subject_week(data, selected_subject, selected_week, min_score))
    
    # Apply order modes
    if practice_order == "Random":
        # Use a deterministic random seed based on the current date
        random_seed = hash(datetime.now().strftime("%Y-%m-%d"))
        random.Random(random_seed).shuffle(questions_queue)
    elif practice_order == "Needs Practice":
        # Sort by weighted score (lowest first) and then by last practiced time (oldest first)
        questions_queue.sort(key=lambda x: (
            5 if x["weighted_score"] is None else x["weighted_score"],  # None scores get highest value
            0 if x["last_practiced"] is None else -x["last_practiced"]   # None last_practiced get highest priority
        ))
    
    return questions_queue, all_subjects, all_weeks

# Cache AI feedback responses to avoid repeated API calls
@st.cache_data(ttl=1800)  # 30 minutes TTL
def cached_evaluate_answer(question, user_answer, expected_answer):
    """Cache the AI evaluation of user answers"""
    # Use a placeholder for the stream handler since it can't be cached
    return evaluate_answer(question, user_answer, expected_answer, stream_handler=None)

def save_score_with_answer(data: Dict, question_item: Dict, score: int, user_answer: str, user_email: str) -> Dict:
    """Save user's score and answer with improved error handling"""
    try:
        # Try with user_answer parameter (new format)
        data = update_question_score(
            data,
            question_item["subject"],
            question_item["week"],
            question_item["question_idx"],
            score,
            user_answer,  # Include user's answer
            user_email  # Include user's email
        )
    except TypeError:
        # Fall back to old format without user_answer
        data = update_question_score(
            data,
            question_item["subject"],
            question_item["week"],
            question_item["question_idx"],
            score,
            None,  # No user answer
            user_email  # Include user's email
        )
    
    return data

def save_ai_feedback(data: Dict, question_item: Dict, feedback_data: Dict) -> Dict:
    """Save AI feedback to the most recent score entry"""
    subject = question_item["subject"]
    week = question_item["week"]
    idx = question_item["question_idx"]
    
    if (subject in data and 
        week in data[subject] and 
        idx < len(data[subject][week]) and
        "scores" in data[subject][week][idx] and
        data[subject][week][idx]["scores"]):
        
        # Get the most recent score entry
        latest_score = data[subject][week][idx]["scores"][-1]
        
        # Add feedback data
        latest_score["ai_feedback"] = {
            "feedback": feedback_data.get("feedback", ""),
            "hint": feedback_data.get("hint", "")
        }
    
    return data

def reset_question_state():
    """Reset the state for navigating to a new question"""
    st.session_state.show_answer = False
    st.session_state.feedback = None
    st.session_state.rating_submitted = False
    st.session_state.chat_messages = []

def reset_practice():
    """Reset the entire practice session"""
    st.session_state.practice_active = False
    st.session_state.current_question_idx = 0
    st.session_state.questions_queue = []
    reset_question_state()

def start_practice():
    """Start a new practice session"""
    st.session_state.practice_active = True
    st.session_state.current_question_idx = 0
    reset_question_state()

def display_self_rating_buttons(current_q: Dict, user_answer: str, user_email: str):
    """Display self-rating buttons and handle rating submission"""
    # Check if rating has already been submitted for this question
    if st.session_state.rating_submitted:
        st.success("Rating submitted! Continue to the next question or try another.")
    else:
        rating_cols = st.columns(5)
        for i in range(5):
            rating_value = i + 1  # Creates scores: 1, 2, 3, 4, 5
            with rating_cols[i]:
                rating_emoji = get_score_emoji(rating_value)
                btn_label = f"{rating_emoji} {rating_value}"
                if st.button(btn_label, key=f"self_rate_{rating_value}", use_container_width=True, help=f"Rate your answer as {rating_value}/5"):
                    # Save the self-rated score and user answer
                    if "question_idx" in current_q:
                        st.session_state.data = save_score_with_answer(
                            st.session_state.data,
                            current_q,
                            rating_value,
                            user_answer,
                            user_email
                        )
                        save_data(st.session_state.data, user_email)
                        st.session_state.rating_submitted = True
                        st.success(f"Saved self-rating: {rating_value}/5")
                        st.rerun()

def display_ai_feedback(feedback_data: Dict):
    """Display AI feedback for a question"""
    st.markdown("---")
    st.markdown("### AI Feedback:")
    
    score = feedback_data.get("score", 0)
    feedback = feedback_data.get("feedback", "No feedback available.")
    hint = feedback_data.get("hint")
    
    # Score with emoji indicator
    score_emoji = get_score_emoji(score)
    st.markdown(f"**Score:** {score_emoji} {score}/5")
    
    # Feedback
    st.markdown(f"**Feedback:** {feedback}")
    
    # Hint (if available and score < 4)
    if hint:
        st.markdown(f"**Hint:** {hint}")

def display_chat_interface(current_q: Dict, user_answer: str, feedback: Dict):
    """Display and handle chat interface for question interaction"""
    # Get the vector store ID if available
    vector_store_id = None
    if current_q["subject"] and current_q["week"]:
        vector_store_id = get_cached_vector_store_id(current_q["subject"], current_q["week"], st.session_state.data)
    
    # Create a container for the chat messages area
    chat_message_container = st.container()
    
    # Create a unique key for chat input based on question
    chat_input_key = f"chat_input_{current_q['subject']}_{current_q['week']}_{current_q['question_idx']}"
    
    # First define the chat input (this will appear at the bottom of the UI)
    user_message = st.chat_input("Ask a question about this concept...", key=chat_input_key)
    
    # Then display all messages in the container
    with chat_message_container:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        # Process new message if one was entered
        if user_message:
            # Add user message to chat history
            st.session_state.chat_messages.append({"role": "user", "content": user_message})
            
            # Display user message immediately
            with st.chat_message("user"):
                st.write(user_message)
            
            # Get and display AI response with streaming
            with st.chat_message("assistant"):
                # Create a placeholder for the streaming response
                message_placeholder = st.empty()
                full_response = ""
                
                # Define the stream handler function
                def stream_handler(content):
                    nonlocal full_response
                    full_response += content
                    # Update the placeholder with the accumulated response
                    message_placeholder.markdown(full_response + "▌")
                
                # Call the chat function with the stream handler
                ai_response = chat_about_question(
                    question=current_q["question"],
                    expected_answer=current_q["answer"],
                    user_answer=user_answer,
                    feedback=feedback,
                    subject=current_q["subject"],
                    week=current_q["week"],
                    vector_store_id=vector_store_id,
                    chat_messages=st.session_state.chat_messages,
                    stream_handler=stream_handler
                )
                
                # Update the final response without the cursor
                message_placeholder.markdown(full_response)
            
            # Add AI response to chat history
            st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
            
            # Rerun to reset the input field and update the UI
            st.rerun()

def display_score_history(current_q: Dict):
    """Display score history for a question"""
    if "question_idx" not in current_q:
        return
        
    subject = current_q["subject"]
    week = current_q["week"]
    idx = current_q["question_idx"]
    
    if subject in st.session_state.data and week in st.session_state.data[subject] and idx < len(st.session_state.data[subject][week]):
        question_data = st.session_state.data[subject][week][idx]
        scores = question_data.get("scores", [])
        
        if scores:
            st.markdown("### Score History")
            
            # Create a tabbed interface for score history
            tabs = st.tabs([f"Attempt {i+1}" for i in range(min(5, len(scores)))])
            
            # Show the most recent 5 attempts (or fewer if there are less)
            for i, tab in enumerate(tabs):
                if i < len(scores):
                    score_entry = scores[-(i+1)]  # Get from end of list for most recent first
                    score = score_entry["score"]
                    timestamp = datetime.fromtimestamp(score_entry["timestamp"]).strftime("%Y-%m-%d %H:%M")
                    score_emoji = get_score_emoji(score)
                    
                    with tab:
                        # Display score and timestamp in tab
                        st.markdown(f"**Score:** {score_emoji} {score}/5 - {timestamp}")
                        
                        # Display the user's answer if available
                        if "user_answer" in score_entry and score_entry["user_answer"]:
                            st.markdown("**Your answer:**")
                            st.markdown(score_entry["user_answer"])
                        
                        # Display AI feedback if available
                        if "ai_feedback" in score_entry:
                            st.markdown("---")
                            st.markdown("**AI Feedback:**")
                            st.markdown(score_entry["ai_feedback"].get("feedback", "No feedback provided"))
                            
                            if "hint" in score_entry["ai_feedback"] and score_entry["ai_feedback"]["hint"]:
                                st.markdown(f"**Hint:** {score_entry['ai_feedback']['hint']}")

def display_knowledge_level_selector():
    """Display and handle the knowledge level filter selector"""
    st.markdown("##### Filter by Knowledge Level")
    st.caption("Practice questions based on how well you know them:")
    
    # Create a selectbox with the descriptive options
    selected_level = st.selectbox(
        "Maximum knowledge level to practice:",
        options=list(KNOWLEDGE_LEVEL_OPTIONS.keys()),
        format_func=lambda x: KNOWLEDGE_LEVEL_OPTIONS[x],
        index=st.session_state.min_score_threshold,
        help="Only practice questions you've scored at or below this level. Lower values help you focus on material you need to improve on."
    )
    
    # Update the session state with the selected value
    st.session_state.min_score_threshold = selected_level
    
    # Show additional explanation for the selected level
    level_explanations = {
        0: "You'll practice questions you've never seen before. Perfect for getting started with new material.",
        1: "You'll practice new questions and ones you're struggling with (rated 0-1). Great for exam preparation.",
        2: "You'll practice questions needing improvement (rated 0-2). Good for focusing on challenging material.",
        3: "You'll practice questions with moderate knowledge (rated 0-3). Balanced practice for better retention.",
        4: "You'll practice questions with good knowledge (rated 0-4). Useful for comprehensive review.",
        5: "You'll practice all questions regardless of your knowledge level. Best for full review sessions."
    }
    
    st.info(level_explanations[selected_level])

def display_practice_navigation(current_idx: int, queue_length: int):
    """Display practice navigation buttons and handle navigation logic"""
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        button_row1 = st.columns([1, 1])
        with button_row1[0]:
            if st.button("Show Answer", use_container_width=True):
                st.session_state.show_answer = True
                st.rerun()
        
        ai_feedback_col = button_row1[1]
    
    with col2:
        prev_disabled = current_idx == 0
        if st.button("Previous", disabled=prev_disabled, use_container_width=True):
            st.session_state.current_question_idx -= 1
            reset_question_state()
            st.rerun()
    
    with col3:
        next_disabled = current_idx == queue_length - 1
        if st.button("Next", disabled=next_disabled, use_container_width=True):
            st.session_state.current_question_idx += 1
            reset_question_state()
            st.rerun()
    
    with col4:
        # Button for random jump
        if queue_length > 1:
            if st.button("Random Question", use_container_width=True):
                new_idx = current_idx
                while new_idx == current_idx:
                    new_idx = random.randint(0, queue_length - 1)
                st.session_state.current_question_idx = new_idx
                reset_question_state()
                st.rerun()
    
    # Return the column for AI feedback button
    return ai_feedback_col

def init_session_state():
    """Initialize practice-specific session state variables"""
    if "practice_active" not in st.session_state:
        st.session_state.practice_active = False
    if "current_question_idx" not in st.session_state:
        st.session_state.current_question_idx = 0
    if "questions_queue" not in st.session_state:
        st.session_state.questions_queue = []
    if "show_answer" not in st.session_state:
        st.session_state.show_answer = False
    if "practice_subject" not in st.session_state:
        st.session_state.practice_subject = "All"
    if "practice_week" not in st.session_state:
        st.session_state.practice_week = "All"
    if "practice_order" not in st.session_state:
        st.session_state.practice_order = "Sequential"
    if "feedback" not in st.session_state:
        st.session_state.feedback = None
    if "enable_ai_feedback" not in st.session_state:
        st.session_state.enable_ai_feedback = True
    if "min_score_threshold" not in st.session_state:
        st.session_state.min_score_threshold = 0  # Default to show all questions
    if "self_rate_score" not in st.session_state:
        st.session_state.self_rate_score = 0  # For self-rated scores
    if "rating_submitted" not in st.session_state:
        st.session_state.rating_submitted = False  # Track if a rating has been submitted for the current question
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []  # Store chat messages

def display_setup_screen(is_authenticated):
    """Display practice setup options"""
    st.subheader("Practice Setup")
    
    # Get unique subjects and weeks
    subjects = sorted(list(st.session_state.data.keys()))
    
    # Default values
    default_subject = subjects[0] if subjects else ""
    default_weeks = []
    if default_subject in st.session_state.data:
        default_weeks = [w for w in st.session_state.data[default_subject].keys() 
                         if w != "vector_store_metadata" and w.isdigit()]
    
    # Allow user to select subject
    subject = st.selectbox("Select subject", subjects, key="practice_subject")
    
    # Get available weeks for the selected subject
    available_weeks = []
    if subject in st.session_state.data:
        available_weeks = [w for w in st.session_state.data[subject].keys() 
                           if w != "vector_store_metadata" and w.isdigit()]
    
    # Allow user to select weeks
    selected_weeks = st.multiselect(
        "Select weeks (leave empty for all)",
        options=available_weeks,
        default=[],
        key="practice_weeks"
    )
    
    # If no weeks selected, use all available weeks
    if not selected_weeks:
        selected_weeks = available_weeks
    
    # Practice mode
    col1, col2 = st.columns(2)
    with col1:
        practice_mode = st.radio(
            "Practice mode",
            ["Sequential", "Random"],
            index=1,
            key="practice_mode",
            horizontal=True
        )
    
    with col2:
        questions_per_session = st.slider(
            "Questions per session",
            min_value=1,
            max_value=20,
            value=5,
            key="practice_count"
        )
    
    # Start practice button
    start_button = st.button("Start Practice", type="primary", use_container_width=True)
    
    if start_button:
        if not is_authenticated:
            # User needs to be authenticated to start practice
            st.warning("Please sign in to start practicing.")
            st.markdown("""
            <div class="element-container st-paywall-container">
                <div class="st-paywall">
                    <a href="/?auth=login" target="_self" class="st-paywall-login-button" style="background-color: #FF6F00;">
                        Sign in to Study Legend
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            return
            
        # Prepare queue of questions
        queue = []
        for week in selected_weeks:
            if subject in st.session_state.data and week in st.session_state.data[subject]:
                questions_list = st.session_state.data[subject][week]
                
                for i, q in enumerate(questions_list):
                    # Only add questions that have questions
                    if "question" in q and q["question"]:
                        queue.append({
                            "subject": subject,
                            "week": week,
                            "index": i,
                            "data": q
                        })
        
        # Shuffle if random mode
        if practice_mode == "Random":
            random.shuffle(queue)
        
        # Limit to requested number
        queue = queue[:questions_per_session]
        
        if not queue:
            st.warning("No questions available with the selected filters.")
            return
        
        # Initialize practice
        st.session_state.questions_queue = queue
        st.session_state.current_question_idx = 0
        st.session_state.practice_active = True
        st.session_state.show_answer = False
        st.session_state.answer_submitted = False
        st.session_state.answer_text = ""
        st.session_state.feedback = None
        st.session_state.chat_messages = []
        
        # Force refresh
        st.rerun()

def build_queue():
    """Build queue using the cached function with current session state"""
    return build_cached_queue(
        st.session_state.data,
        st.session_state.practice_subject,
        st.session_state.practice_week,
        st.session_state.practice_order,
        st.session_state.min_score_threshold
    )

def get_feedback_stream_handler(placeholder):
    """Create a stream handler function for feedback updates"""
    def feedback_stream_handler(content):
        if "evaluating" in content.lower():
            placeholder.markdown("Evaluating your response...")
        elif "analyzing" in content.lower():
            placeholder.markdown("Analyzing key concepts...")
        elif "comparing" in content.lower():
            placeholder.markdown("Comparing with expected answer...")
        elif "finalizing" in content.lower():
            placeholder.markdown("Finalizing feedback...")
    return feedback_stream_handler

def process_ai_feedback(current_q: Dict, user_answer: str, user_email: str):
    """Request and process AI feedback on user answer"""
    # Create a placeholder for streaming status updates
    feedback_placeholder = st.empty()
    feedback_placeholder.markdown("Analyzing your answer...")
    
    # Get the AI feedback with streaming updates
    stream_handler = get_feedback_stream_handler(feedback_placeholder)
    feedback = evaluate_answer(
        current_q["question"],
        user_answer,
        current_q["answer"],
        stream_handler=stream_handler
    )
    
    # Clear the placeholder when done
    feedback_placeholder.empty()
    
    # Save the score, user answer, and AI feedback
    if "question_idx" in current_q and feedback.get("score") is not None:
        score = feedback.get("score")
        
        # Update the score and feedback in a single operation
        # This will update directly in MongoDB without rewriting the entire database
        st.session_state.data = update_single_question_score(
            st.session_state.data,
            current_q["subject"],
            current_q["week"],
            current_q["question_idx"],
            score,
            user_answer,
            feedback,  # Pass the feedback data directly
            user_email
        )
        
        # Update session state
        st.session_state.rating_submitted = True
        st.session_state.show_answer = True
        st.session_state.feedback = feedback
    
    return feedback

def display_practice_question(question_data, is_authenticated, user_email):
    """Display the current practice question"""
    # Question container
    with st.container(border=True):
        st.markdown(f"**Subject:** {question_data['subject']} - Week {question_data['week']}")
        st.markdown(f"### Q: {question_data['question']}")
        
        # Remember this question key for tracking
        question_key = (
            question_data["subject"],
            question_data["week"],
            question_data["idx"]
        )
        
        # User answer section
        user_answer = st.text_area(
            "Your answer:",
            value=st.session_state.user_answer,
            height=100,
            key=f"answer_input_{st.session_state.current_question_idx}"
        )
        
        # Save the user's answer to session state
        st.session_state.user_answer = user_answer
        
        # Answer and continue row
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Submit answer and get feedback
            if st.button("Check Answer", use_container_width=True):
                if not is_authenticated:
                    st.warning("Please sign in to check your answer.")
                    st.markdown("""
                    <div class="element-container st-paywall-container">
                        <div class="st-paywall">
                            <a href="/?auth=login" target="_self" class="st-paywall-login-button" style="background-color: #FF6F00;">
                                Sign in to Study Legend
                            </a>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    return
                    
                if not user_answer.strip():
                    st.warning("Please enter an answer first.")
                    return
                
                st.session_state.show_answer = True
                
                # Generate AI feedback
                with st.spinner("Analyzing your answer..."):
                    try:
                        feedback_result = evaluate_answer(
                            question_data["question"],
                            question_data["answer"],
                            user_answer
                        )
                        
                        # Store feedback in session state
                        st.session_state.feedback = feedback_result
                        
                        # Clear chat messages when new feedback is generated
                        st.session_state.chat_messages = []
                        
                        # Save feedback to MongoDB if user is logged in
                        if user_email:
                            try:
                                save_ai_feedback(
                                    user_email,
                                    question_data["subject"],
                                    question_data["week"],
                                    question_data["idx"],
                                    question_data["question"],
                                    question_data["answer"],
                                    user_answer,
                                    feedback_result
                                )
                            except Exception as e:
                                # Log but don't block if feedback saving fails
                                print(f"Error saving feedback: {str(e)}")
                    except Exception as e:
                        st.error(f"Error generating feedback: {str(e)}")
                        st.session_state.feedback = {
                            "score": 0,
                            "explanation": "Could not generate feedback. Please try again."
                        }
                
                # Rerun to show feedback
                st.rerun()
                
        with col2:
            # Show answer button or next question button
            if st.session_state.show_answer:
                if st.button("Next Question →", use_container_width=True):
                    # Move to the next question
                    go_to_next_question()
                    st.rerun()
            else:
                if st.button("Show Answer", use_container_width=True):
                    if not is_authenticated:
                        st.warning("Please sign in to view answers.")
                        st.markdown("""
                        <div class="element-container st-paywall-container">
                            <div class="st-paywall">
                                <a href="/?auth=login" target="_self" class="st-paywall-login-button" style="background-color: #FF6F00;">
                                    Sign in to Study Legend
                                </a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        return
                    
                    st.session_state.show_answer = True
                    st.rerun()
        
        # Display answer and feedback if show_answer is True
        if st.session_state.show_answer:
            # Display answer
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown(question_data["answer"])
            
            # Display AI feedback if available
            if st.session_state.feedback:
                st.markdown("---")
                st.markdown("### AI Feedback:")
                
                feedback = st.session_state.feedback
                score = feedback.get("score", 0)
                explanation = feedback.get("explanation", "No explanation provided.")
                
                # Create a score color based on the score
                if score >= 8:
                    score_color = "green"
                elif score >= 5:
                    score_color = "orange"
                else:
                    score_color = "red"
                
                # Display score
                st.markdown(f"**Score:** <span style='color:{score_color};font-size:18px;'>{score}/10</span>", unsafe_allow_html=True)
                
                # Display explanation
                st.markdown(f"**Feedback:** {explanation}")
                
                # Only show self-rating if authenticated
                if is_authenticated:
                    # Self-rating section
                    st.markdown("### How would you rate your answer?")
                    self_rating = st.slider(
                        "Your self-assessment (0-10)",
                        min_value=0,
                        max_value=10,
                        value=score,
                        step=1,
                        key=f"self_rating_{st.session_state.current_question_idx}"
                    )
                    
                    # Save the rating
                    if question_key not in st.session_state.question_ratings:
                        st.session_state.question_ratings[question_key] = self_rating
                    
                    # Save button
                    if st.button("Save Rating"):
                        # Require authentication to save ratings
                        if not user_email:
                            st.warning("You must be logged in to save ratings.")
                            return
                            
                        # Update the score in both data structures
                        st.session_state.data = update_question_score(
                            st.session_state.data,
                            question_data["subject"],
                            question_data["week"],
                            question_data["idx"],
                            self_rating,
                            user_answer,
                            user_email
                        )
                        
                        # Update in MongoDB directly as well
                        try:
                            update_single_question_score(
                                user_email,
                                question_data["subject"],
                                question_data["week"],
                                question_data["idx"],
                                self_rating,
                                user_answer
                            )
                        except Exception as e:
                            # Log but continue if direct MongoDB update fails
                            print(f"Error updating score in MongoDB: {str(e)}")
                        
                        # Also update in session state
                        st.session_state.question_ratings[question_key] = self_rating
                        
                        # Show confirmation
                        st.success("Rating saved!")
                    
                    # Chat with AI about the question
                    st.markdown("---")
                    st.markdown("### Chat with AI about this question")
                    
                    # Display previous chat messages
                    for message in st.session_state.chat_messages:
                        role = message["role"]
                        content = message["content"]
                        
                        if role == "user":
                            st.chat_message("user").write(content)
                        else:
                            st.chat_message("assistant").write(content)
                    
                    # Chat input
                    chat_input = st.chat_input("Ask a question about this topic...")
                    if chat_input:
                        # Add user message to chat history
                        st.session_state.chat_messages.append({
                            "role": "user",
                            "content": chat_input
                        })
                        
                        # Display user message
                        st.chat_message("user").write(chat_input)
                        
                        # Get AI response
                        with st.spinner("AI is thinking..."):
                            try:
                                ai_response = chat_about_question(
                                    question_data["question"],
                                    question_data["answer"],
                                    user_answer,
                                    chat_input,
                                    question_data.get("subject", ""),
                                    question_data.get("week", "")
                                )
                                
                                # Add AI response to chat history
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": ai_response
                                })
                                
                                # Display AI response
                                st.chat_message("assistant").write(ai_response)
                            except Exception as e:
                                st.error(f"Error generating response: {str(e)}")
                    
                else:
                    # Show login prompt for chat functionality
                    st.info("Sign in to rate your answers and chat with AI about this question.")

def go_to_next_question():
    """Move to the next question in the queue"""
    # Reset answer-related state
    st.session_state.show_answer = False
    st.session_state.user_answer = ""
    st.session_state.feedback = None
    st.session_state.chat_messages = []
    
    # Move to next question
    st.session_state.current_question_idx += 1
    
    # Check if we've reached the end
    if st.session_state.current_question_idx >= len(st.session_state.questions_queue):
        # Practice session completed
        reset_practice()
        
        # Show completion message
        st.balloons()
        st.success("Practice session completed!")
        st.rerun()

def reset_practice():
    """Reset the practice session"""
    st.session_state.practice_active = False
    st.session_state.questions_queue = []
    st.session_state.current_question_idx = 0
    st.session_state.show_answer = False
    st.session_state.user_answer = ""
    st.session_state.feedback = None
    st.session_state.chat_messages = []
    
    # Save the data with updated scores
    user_email = get_user_email()
    if user_email and st.session_state.question_ratings:
        try:
            save_data(st.session_state.data, user_email)
        except Exception as e:
            # Log but continue if save fails
            print(f"Error saving data: {str(e)}")
    
    # Clear the question ratings
    st.session_state.question_ratings = {}

def show_demo_content():
    """Show demo content for users in preview mode"""
    # Add subject selector
    selected_subject = st.selectbox(
        "Select Subject for Demo",
        ["Computer Science", "Biology", "Law"],
        index=0,  # Default to Computer Science
        key="practice_demo_subject"
    )
    
    # Display a sample practice question based on selected subject
    with st.container(border=True):
        if selected_subject == "Computer Science":
            st.markdown("**Subject:** Computer Science - Week 3")
            st.markdown("### Q: Explain the difference between stack and heap memory allocation.")
            
            # Sample answer input
            st.text_area(
                "Your answer:",
                value="Stack memory is used for static memory allocation and is managed automatically by the compiler. It stores local variables and function call data. Heap memory is used for dynamic memory allocation controlled by the programmer, storing objects with longer lifetimes.",
                height=150,
                key="demo_cs_answer_input",
                disabled=True
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Demo check answer button
                st.button("Check Answer", key="cs_check", use_container_width=True, disabled=True)
            
            with col2:
                # Demo show answer button
                st.button("Show Answer", key="cs_show", use_container_width=True, disabled=True)
            
            # Sample answer and feedback
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown("""
            Stack memory allocation is used for static memory allocation where variables are allocated and 
            deallocated in a last-in-first-out order, typically for local variables and function calls. 
            It's faster but limited in size.
            
            Heap memory allocation is used for dynamic memory allocation at runtime, managed by the programmer 
            (in languages like C/C++) or garbage collector. It's slower but allows for larger and variable-sized 
            data structures with lifetimes not tied to specific scopes.
            """)
            
            # Sample feedback preview
            st.markdown("---")
            st.markdown("### AI Feedback:")
            st.markdown("**Score:** <span style='color:green;font-size:18px;'>8/10</span>", unsafe_allow_html=True)
            st.markdown("""
            **Feedback:** Good answer! You've correctly identified the key differences between stack and heap memory:
            
            ✅ You mentioned stack is for static allocation and heap for dynamic allocation
            ✅ You explained that stack is managed automatically while heap is controlled by the programmer
            ✅ You noted that stack typically stores local variables
            
            To improve your answer, you could add:
            - The LIFO (Last-In-First-Out) structure of stack memory
            - Speed differences (stack is generally faster)
            - Size limitations (stack is more limited)
            - Memory fragmentation concerns with heap memory
            """)
    
            # Sample chat example
            st.markdown("---")
            st.markdown("### Chat with AI about this question")
            
            # Sample conversation
            with st.chat_message("user"):
                st.write("Can you explain what causes stack overflow errors?")
                
            with st.chat_message("assistant"):
                st.write("""
                Stack overflow errors occur when a program attempts to use more memory space in the stack than has been allocated. Here's why they happen:
    
                1. **Limited Stack Size**: The stack has a fixed, predetermined size set by the operating system or compiler.
    
                2. **Common Causes**:
                   - Infinite recursion (a function that keeps calling itself without a proper base case)
                   - Very deep recursion (even with a base case, if the depth is too great)
                   - Allocating large data structures on the stack
                   - Extensive function call chains that exceed stack capacity
    
                3. **Example**:
                ```python
                def infinite_recursion():
                    # No base case to stop recursion
                    print("Recursive call")
                    infinite_recursion()
                    
                infinite_recursion()  # Will eventually cause stack overflow
                ```
    
                4. **Prevention**:
                   - Use iteration instead of recursion when possible
                   - Implement proper base cases for recursive functions
                   - Allocate large objects on the heap instead of the stack
                   - Increase stack size if needed (platform-specific)
                   - Use tail recursion optimization when available
    
                Stack overflows are particularly common in languages without automatic garbage collection like C and C++.
                """)
                
            with st.chat_message("user"):
                st.write("What about memory leaks with heap allocation?")
            
        elif selected_subject == "Biology":
            st.markdown("**Subject:** Biology - Week 2")
            st.markdown("### Q: Explain the process of photosynthesis and its importance for life on Earth.")
            
            # Sample answer input
            st.text_area(
                "Your answer:",
                value="Photosynthesis is the process by which plants, algae, and some bacteria convert light energy into chemical energy. They use sunlight, water, and carbon dioxide to produce glucose and oxygen. This process is vital for life as it produces oxygen for animals to breathe and creates the energy source for most food chains.",
                height=150,
                key="demo_bio_answer_input",
                disabled=True
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Demo check answer button
                st.button("Check Answer", key="bio_check", use_container_width=True, disabled=True)
            
            with col2:
                # Demo show answer button
                st.button("Show Answer", key="bio_show", use_container_width=True, disabled=True)
            
            # Sample answer and feedback
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown("""
            Photosynthesis is the biochemical process by which photoautotrophs (plants, algae, and some bacteria) convert light energy from the sun into chemical energy stored in glucose molecules. The process uses carbon dioxide and water, releasing oxygen as a byproduct.
            
            The overall equation is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂
            
            The process occurs in two main stages:
            1. Light-dependent reactions (in the thylakoid membrane): Capture light energy, split water molecules, and produce ATP and NADPH.
            2. Calvin cycle (light-independent reactions): Uses ATP and NADPH to fix carbon dioxide into glucose.
            
            Photosynthesis is crucial for life on Earth because:
            - It produces oxygen required for aerobic respiration in most organisms
            - It forms the base of most food chains, converting solar energy into chemical energy
            - It removes carbon dioxide from the atmosphere, affecting climate regulation
            - It has shaped Earth's atmosphere, enabling the evolution of complex life forms
            """)
            
            # Sample feedback preview
            st.markdown("---")
            st.markdown("### AI Feedback:")
            st.markdown("**Score:** <span style='color:orange;font-size:18px;'>7/10</span>", unsafe_allow_html=True)
            st.markdown("""
            **Feedback:** Good start! You've captured the basic concept of photosynthesis:
            
            ✅ You correctly identified it as a process that converts light energy to chemical energy
            ✅ You mentioned the inputs (sunlight, water, CO₂) and outputs (glucose, oxygen)
            ✅ You noted its importance for producing oxygen and supporting food chains
            
            To improve your answer, consider adding:
            - The specific equation for photosynthesis (6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂)
            - The two stages of photosynthesis (light-dependent reactions and Calvin cycle)
            - Where photosynthesis occurs in plants (chloroplasts, specifically thylakoids)
            - The role of chlorophyll in capturing light energy
            - More detailed ecological importance (carbon fixation, climate regulation)
            """)
    
            # Sample chat example
            st.markdown("---")
            st.markdown("### Chat with AI about this question")
            
            # Sample conversation
            with st.chat_message("user"):
                st.write("What's the difference between C3, C4, and CAM photosynthesis?")
                
            with st.chat_message("assistant"):
                st.write("""
                C3, C4, and CAM photosynthesis are different adaptations that plants have evolved to fix carbon efficiently in various environments:
    
                **C3 Photosynthesis:**
                - The most common type (~85% of plants)
                - Named because the first product of carbon fixation is a 3-carbon molecule (3-phosphoglycerate)
                - Carbon fixation occurs directly via the Calvin cycle using the enzyme RuBisCO
                - Works best in moderate temperatures and humid conditions
                - Examples: rice, wheat, soybeans, trees
                - Less efficient in hot/dry conditions due to photorespiration
    
                **C4 Photosynthesis:**
                - Evolved as an adaptation to hot, dry environments
                - Named because the first product is a 4-carbon molecule (oxaloacetate)
                - Uses spatial separation: carbon fixation occurs in mesophyll cells, then the 4-carbon molecules are transported to bundle sheath cells for the Calvin cycle
                - Minimizes photorespiration by concentrating CO₂ around RuBisCO
                - More efficient in hot/sunny conditions but requires more energy
                - Examples: corn, sugarcane, sorghum
    
                **CAM Photosynthesis (Crassulacean Acid Metabolism):**
                - Adaptation to extremely arid conditions
                - Uses temporal separation: stomata open at night to collect CO₂, which is stored as malate; during the day, stomata close to conserve water while malate releases CO₂ for the Calvin cycle
                - Highly water-efficient but less energy-efficient overall
                - Examples: cacti, pineapples, agaves, many succulents
    
                These different photosynthetic pathways represent evolutionary adaptations to different environmental conditions, primarily balancing water conservation against photosynthetic efficiency.
                """)
                
            with st.chat_message("user"):
                st.write("Why does photorespiration happen in C3 plants?")
            
        else:  # Law
            st.markdown("**Subject:** Law - Week 4")
            st.markdown("### Q: Explain the concept of precedent in common law legal systems and its importance.")
            
            # Sample answer input
            st.text_area(
                "Your answer:",
                value="Precedent in common law refers to the principle that courts should follow previous decisions from similar cases. It provides consistency, predictability, and stability in the legal system. Precedent is binding when it comes from a higher court but can sometimes be overturned if deemed necessary.",
                height=150,
                key="demo_law_answer_input",
                disabled=True
            )
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Demo check answer button
                st.button("Check Answer", key="law_check", use_container_width=True, disabled=True)
            
            with col2:
                # Demo show answer button
                st.button("Show Answer", key="law_show", use_container_width=True, disabled=True)
            
            # Sample answer and feedback
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown("""
            Precedent (stare decisis) is a fundamental principle in common law systems whereby judges are bound to follow previous decisions of courts of the same or higher level when ruling on cases with similar facts and legal issues.
            
            Key aspects of precedent include:
            
            1. Binding vs. Persuasive Precedent
               - Binding precedent must be followed by lower courts
               - Persuasive precedent from other jurisdictions may inform but not bind decisions
            
            2. Ratio Decidendi vs. Obiter Dicta
               - Ratio decidendi: The binding legal principle essential to the decision
               - Obiter dicta: Supplementary remarks that aren't binding
            
            3. Distinguishing and Overruling
               - Courts may distinguish cases based on different facts
               - Higher courts may overrule previous decisions in limited circumstances
            
            Precedent is crucial because it:
            - Ensures consistency and predictability in legal outcomes
            - Promotes equality by treating similar cases alike
            - Provides efficiency in judicial decision-making
            - Creates stability while allowing for incremental legal development
            - Balances rigidity with flexibility through distinguishing and occasional overruling
            
            This doctrine is a defining characteristic of common law systems (UK, US, Canada, Australia) compared to civil law systems that rely primarily on codified statutes.
            """)
            
            # Sample feedback preview
            st.markdown("---")
            st.markdown("### AI Feedback:")
            st.markdown("**Score:** <span style='color:orange;font-size:18px;'>6/10</span>", unsafe_allow_html=True)
            st.markdown("""
            **Feedback:** Your answer provides a basic understanding of precedent:
            
            ✅ You correctly identified precedent as following previous decisions
            ✅ You mentioned its importance for consistency and predictability
            ✅ You noted the binding nature from higher courts and possibility of overturning
            
            To improve your answer, consider adding:
            - The Latin term "stare decisis" ("to stand by decisions")
            - The distinction between ratio decidendi (binding part) and obiter dicta (non-binding)
            - More on how courts can "distinguish" cases without overturning precedent
            - The hierarchy of courts and how it affects binding precedent
            - The balance between legal stability and evolution of law
            - Comparison with civil law systems that rely less on precedent
            """)
    
            # Sample chat example
            st.markdown("---")
            st.markdown("### Chat with AI about this question")
            
            # Sample conversation
            with st.chat_message("user"):
                st.write("What are the circumstances when precedent can be overturned?")
                
            with st.chat_message("assistant"):
                st.write("""
                Precedent can be overturned in several specific circumstances, though courts generally approach this with caution:
    
                **1. By Higher Courts:**
                - Superior courts can overturn precedents set by lower courts
                - For example, the Supreme Court can overturn decisions from Courts of Appeal
    
                **2. By the Same Court:**
                Some courts (especially supreme courts) can overturn their own precedents when:
                - The precedent is clearly wrong or deeply flawed in reasoning
                - The precedent has become unworkable in practice
                - Social, technological, or legal developments have made it obsolete
                - The precedent conflicts with fundamental principles of justice
                - There's been significant change in public policy considerations
    
                **3. Notable Examples:**
                - *Brown v. Board of Education* (1954) overturned *Plessy v. Ferguson* (1896), rejecting "separate but equal" doctrine
                - *Lawrence v. Texas* (2003) overturned *Bowers v. Hardwick* (1986) regarding same-sex relationships
    
                **4. Considerations When Overturning:**
                Courts typically consider:
                - Reliance: Whether people have structured their affairs based on the precedent
                - Stability: The importance of predictability in the legal system
                - Legitimacy: How overturning might affect public perception of the judiciary
                - Evolution: The need for law to adapt to changing societal conditions
    
                **5. Distinguishing vs. Overturning:**
                - Courts often prefer to "distinguish" cases (finding relevant differences) rather than overturn precedent outright
                - This allows more incremental development of law while maintaining respect for precedent
    
                The power to overturn precedent is exercised sparingly and typically accompanied by thorough justification to maintain the integrity of the legal system.
                """)
                
            with st.chat_message("user"):
                st.write("How does the concept of precedent differ between the UK and US legal systems?")
        
        # Disabled chat input to show it's a demo
        st.chat_input("Ask a question about this topic...", disabled=True)
        
        # Show login/subscription prompt
        st.markdown("---")
        st.info("Sign in or upgrade to premium to practice with your own flashcards and get AI feedback on your answers.")

def run():
    """Main practice page content - this gets run by the navigation system"""
    # Check if user is authenticated and subscribed using session state directly
    user_email = st.session_state.get("email")
    is_authenticated = user_email is not None
    is_subscribed = st.session_state.get("user_subscribed", False)
    
    st.title("🎯 Practice with AI")
    st.markdown("""
    Test your knowledge with the questions you've created. You can practice all questions 
    or filter by subject and week. Choose between sequential or random order.
    """)

    # Check for unauthenticated users first to show demo content
    if not is_authenticated:
        # Show preview mode for unauthenticated users
        show_preview_mode(
            "Practice",
            """
            This feature allows you to practice with your flashcards using AI feedback.
            
            - Choose questions by subject and week
            - Test yourself in sequential or random order
            - Get instant AI feedback on your answers
            - Track your progress over time
            """
        )
        
        # Show demo/preview content
        show_demo_content()
        return

    # Load data if not already in session state (only for authenticated users)
    if "data" not in st.session_state:
        st.session_state.data = load_data(user_email)
    
    # Initialize practice-specific session state
    init_session_state()

    # Practice setup screen
    if not st.session_state.practice_active:
        if not st.session_state.data:
            st.warning("No questions available. Add some questions first!")
            st.link_button("Go to Add Cards with AI", "/render_add_ai")
        else:
            display_setup_screen(is_authenticated)
    
    # Practice in progress
    else:
        # Top control bar
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.subheader(f"Question {st.session_state.current_question_idx + 1} of {len(st.session_state.questions_queue)}")
        
        with col2:
            st.write("")  # Spacing
            if st.button("Reset Practice", use_container_width=True):
                reset_practice()
                st.rerun()
        
        with col3:
            st.write("")  # Spacing
            if st.button("End Practice", use_container_width=True, type="primary"):
                reset_practice()
                st.rerun()
        
        # Current question
        if st.session_state.current_question_idx < len(st.session_state.questions_queue):
            current_q = st.session_state.questions_queue[st.session_state.current_question_idx]
            display_practice_question(current_q, is_authenticated, user_email)
    
    # For authenticated but non-subscribed users - show premium benefits
    if is_authenticated and not is_subscribed:
        # Show premium benefits
        st.markdown("### 🌟 Upgrade to Premium for these benefits:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("✅ **Advanced AI feedback on your answers**")
            st.markdown("✅ **Chat with AI about any question**")
            st.markdown("✅ **Detailed progress analytics**")
        
        with col2:
            st.markdown("✅ **Personalized learning recommendations**")
            st.markdown("✅ **Unlimited practice sessions**")
            st.markdown("✅ **Priority support**")

        # Show premium feature notice
        st.warning("Get AI feedback and chat features with a premium subscription.")
        
        # Add upgrade button
        st.button("Upgrade to Premium", type="primary", disabled=True)
        
        # Show demo content for authenticated but non-subscribed users
        st.markdown("---")
        st.subheader("Preview Premium Features")
        st.markdown("Here's a preview of the premium features you'll get with a subscription:")
        
        # Show demo content
        show_demo_content()

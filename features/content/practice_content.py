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

# Use functions from Home module
load_data = Home.load_data
save_data = Home.save_data
update_question_score = Home.update_question_score
calculate_weighted_score = Home.calculate_weighted_score
get_user_email = Home.get_user_email

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

def display_setup_screen(is_subscribed: bool):
    """Display the practice setup screen"""
    st.subheader("Practice Setup")
    
    all_subjects = list(st.session_state.data.keys())
    
    # Create a two-row layout for better organization
    row1_col1, row1_col2 = st.columns(2)
    
    # First row: Subject and Week selectors
    with row1_col1:
        st.session_state.practice_subject = st.selectbox(
            "Subject", 
            ["All"] + all_subjects,
            index=0
        )
        
        display_knowledge_level_selector()
    
    with row1_col2:
        available_weeks = ["All"]
        if st.session_state.practice_subject != "All":
            # Only show weeks for the selected subject (filter out metadata)
            subject_weeks = filter_weeks(st.session_state.data, st.session_state.practice_subject)
            available_weeks += sorted(subject_weeks, key=int)
        else:
            # Show all weeks across all subjects
            all_weeks = collect_all_weeks(st.session_state.data)
            available_weeks += all_weeks
                
        st.session_state.practice_week = st.selectbox(
            "Week", 
            available_weeks,
            index=0
        )
        
        st.session_state.practice_order = st.radio(
            "Question Order", 
            ["Sequential", "Random", "Needs Practice"]
        )
        
        if is_subscribed:
            st.session_state.enable_ai_feedback = st.checkbox(
                "Enable AI Feedback",
                value=st.session_state.enable_ai_feedback,
                help="When enabled, AI will evaluate your answers and provide feedback"
            )
            
            # Add an expander with more info about AI feedback
            with st.expander("How AI Feedback works"):
                st.markdown("""
                ### AI Feedback Feature
                
                When enabled, the AI will:
                
                - Compare your answer with the expected answer
                - Identify key concepts you covered correctly
                - Point out any missing or incorrect information
                - Suggest improvements to your answer
                - Provide a score from 0-5 based on your answer quality
                
                This feedback helps you understand your strengths and weaknesses better than self-assessment alone. The AI considers the context of the question and evaluates your conceptual understanding, not just keyword matching.
                
                Note: AI feedback requires an internet connection and may take a few seconds to generate.
                """)
        else:
            # Disabled checkbox for non-premium users
            st.session_state.enable_ai_feedback = False
            st.checkbox(
                "Enable AI Feedback (Premium feature)",
                value=False,
                disabled=True,
                help="AI feedback is a premium feature. Please upgrade to access this feature."
            )
            st.info("🔒 AI feedback requires a premium subscription. Upgrade to receive detailed AI analysis of your answers.")
    
    questions_queue, _, _ = build_queue()
    
    if questions_queue:
        st.success(f"Found {len(questions_queue)} questions matching your criteria")
        
        # Add an explanation of how question selection works
        with st.expander("How does the knowledge level filter work?"):
            st.markdown("""
            ### Understanding Knowledge Levels
            
            The knowledge level filter helps you focus on questions you need to practice most based on your previous performance:
            
            | Level | Description | When to Use |
            |-------|-------------|------------|
            | **0** | New questions only | When starting a new topic |
            | **1** | Includes questions you're struggling with (0-1) | Before important tests |
            | **2** | Includes questions needing improvement (0-2) | For targeted review |
            | **3** | Includes questions with moderate mastery (0-3) | For regular study sessions |
            | **4** | Includes questions you know well (0-4) | For comprehensive review |
            | **5** | All questions | For complete subject review |
            
            #### How It Works
            
            1. Each time you answer a question, you rate your knowledge (0-5)
            2. The system calculates a weighted average of your scores
            3. Recent scores count more than older ones
            4. Questions are filtered based on their weighted average
            
            This spaced repetition approach helps you focus on material you need to practice most, making your study time more efficient.
            """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Practice", use_container_width=True, type="primary"):
                st.session_state.questions_queue = questions_queue
                start_practice()
                st.rerun()
        
        with col2:
            if st.button("Reset Filters", use_container_width=True):
                st.session_state.practice_subject = "All"
                st.session_state.practice_week = "All"
                st.session_state.practice_order = "Sequential"
                st.rerun()
    else:
        st.warning("No questions found with the selected filters. Try different selections.")

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

def display_practice_question(current_q: Dict, is_subscribed: bool, user_email: str):
    """Display a practice question and handle user interactions"""
    with st.container(border=True):
        st.write(f"**Subject:** {current_q['subject']}, **Week:** {current_q['week']}")
        
        # Question display
        st.markdown("### Question:")
        st.markdown(f"**{current_q['question']}**")
        
        # Answer section
        st.markdown("### Your Answer:")
        user_answer = st.text_area("Type your answer here (optional)", key=f"user_answer_{st.session_state.current_question_idx}", height=100)
        
        # Create navigation buttons and get the column for AI feedback button
        ai_feedback_column = display_practice_navigation(
            st.session_state.current_question_idx, 
            len(st.session_state.questions_queue)
        )
        
        # Add AI feedback button in the returned column
        with ai_feedback_column:
            # Only show the AI feedback button if user has premium access
            if is_subscribed:
                if st.session_state.enable_ai_feedback and st.button("Get AI Feedback", use_container_width=True):
                    if not user_answer.strip():
                        st.error("Please provide an answer to evaluate.")
                    else:
                        process_ai_feedback(current_q, user_answer, user_email)
                        st.rerun()
            else:
                # Disabled button for non-premium users
                st.button("Get AI Feedback (Premium)", use_container_width=True, disabled=True, help="AI feedback requires a premium subscription")
                st.info("🔒 AI feedback is a premium feature.")
        
        # Self-rating section - only show if AI feedback is not enabled
        if not (is_subscribed and st.session_state.enable_ai_feedback):
            st.markdown("---")
            st.markdown("### Rate Your Answer:")
            display_self_rating_buttons(current_q, user_answer, user_email)
        
        # Display AI feedback if available
        if st.session_state.feedback:
            display_ai_feedback(st.session_state.feedback)
            
            # Initialize the chat if needed
            if st.session_state.feedback and is_subscribed and st.session_state.enable_ai_feedback:
                display_chat_interface(current_q, user_answer, st.session_state.feedback)
        
        # Display expected answer if requested
        if st.session_state.show_answer:
            st.markdown("---")
            st.markdown("### Expected Answer:")
            if current_q["answer"]:
                st.markdown(current_q["answer"])
            else:
                st.info("No expected answer was provided for this question.")
        
        # Display question's score history
        display_score_history(current_q)

def run():
    """Main practice page content - this gets run by the navigation system"""
    # Check subscription status but don't require it
    from paywall import check_subscription
    is_subscribed, user_email = check_subscription(required=False)

    st.title("🎯 Practice with AI")
    st.markdown("""
    Test your knowledge with the questions you've created. You can practice all questions 
    or filter by subject and week. Choose between sequential or random order.
    """)
    
    # Get the most reliable user email
    user_email = get_user_email() or user_email
    
    # Make sure we have the user's email in all the right places
    if user_email:
        st.session_state.user_email = user_email
    
    # Load data if not already in session state
    if "data" not in st.session_state:
        st.session_state.data = cached_load_data(user_email)
    
    # Initialize practice-specific session state
    init_session_state()
    
    # Practice setup screen
    if not st.session_state.practice_active:
        if not st.session_state.data:
            st.warning("No questions available. Add some questions first!")
            st.link_button("Go to Add Cards with AI", "/render_add_ai")
        else:
            display_setup_screen(is_subscribed)
    
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
            display_practice_question(current_q, is_subscribed, user_email)

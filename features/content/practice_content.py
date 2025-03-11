import streamlit as st
import sys
import os
import random
import time
from datetime import datetime
from typing import Optional

# Add parent directory to path so we can import from Home.py and ai_feedback.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import functions from Home.py
import Home
from ai_feedback import evaluate_answer, chat_about_question

# Use functions from Home module
load_data = Home.load_data
save_data = Home.save_data
update_question_score = Home.update_question_score
calculate_weighted_score = Home.calculate_weighted_score
get_user_email = Home.get_user_email

def run():
    """Main practice page content - this gets run by the navigation system"""
    # Check subscription status but don't require it
    from paywall import check_subscription
    is_subscribed, user_email = check_subscription(required=False)

    st.title("🎯 Practice Mode")
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
        st.session_state.data = load_data(user_email)
    
    # Initialize practice-specific session state
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
    
    # Helper functions
    def reset_practice():
        st.session_state.practice_active = False
        st.session_state.current_question_idx = 0
        st.session_state.questions_queue = []
        st.session_state.show_answer = False
        st.session_state.feedback = None
        st.session_state.chat_messages = []
    
    def start_practice():
        st.session_state.practice_active = True
        st.session_state.current_question_idx = 0
        st.session_state.show_answer = False
        st.session_state.rating_submitted = False
        st.session_state.chat_messages = []
        
    def get_vector_store_id(subject: str, week: str) -> Optional[str]:
        """Get vector store ID for the current subject and week if it exists"""
        if (subject in st.session_state.data and 
            "vector_store_metadata" in st.session_state.data[subject] and 
            week in st.session_state.data[subject]["vector_store_metadata"]):
            return st.session_state.data[subject]["vector_store_metadata"][week].get("id")
        return None
        
    def build_queue():
        """Build a queue of questions based on selected filters and score threshold"""
        questions_queue = []
        all_subjects = list(st.session_state.data.keys())
        
        selected_subject = st.session_state.practice_subject
        selected_week = st.session_state.practice_week
        min_score = st.session_state.min_score_threshold
        
        # Collect all weeks across subjects
        all_weeks = set()
        for subject in all_subjects:
            # Filter out metadata keys
            weeks = [w for w in st.session_state.data[subject].keys() 
                   if w != "vector_store_metadata" and w.isdigit()]
            all_weeks.update(weeks)
        
        # Build queue based on filters
        if selected_subject == "All" and selected_week == "All":
            for subject in all_subjects:
                for week in st.session_state.data[subject]:
                    # Skip metadata keys
                    if week == "vector_store_metadata" or not week.isdigit():
                        continue
                    for i, q in enumerate(st.session_state.data[subject][week]):
                        # Calculate weighted score if there are scores available
                        weighted_score = None
                        if "scores" in q and q["scores"]:
                            weighted_score = calculate_weighted_score(q["scores"])
                        
                        # Only add question if it meets the threshold or has no score yet
                        if weighted_score is None or weighted_score <= min_score:
                            questions_queue.append({
                                "subject": subject,
                                "week": week,
                                "question_idx": i,
                                "question": q["question"],
                                "answer": q["answer"],
                                "weighted_score": weighted_score,
                                "last_practiced": q.get("last_practiced", None)
                            })
        elif selected_subject == "All":
            for subject in all_subjects:
                if selected_week in st.session_state.data[subject]:
                    for i, q in enumerate(st.session_state.data[subject][selected_week]):
                        weighted_score = None
                        if "scores" in q and q["scores"]:
                            weighted_score = calculate_weighted_score(q["scores"])
                        
                        if weighted_score is None or weighted_score <= min_score:
                            questions_queue.append({
                                "subject": subject,
                                "week": selected_week,
                                "question_idx": i,
                                "question": q["question"],
                                "answer": q["answer"],
                                "weighted_score": weighted_score,
                                "last_practiced": q.get("last_practiced", None)
                            })
        elif selected_week == "All":
            for week in st.session_state.data[selected_subject]:
                # Skip metadata keys
                if week == "vector_store_metadata" or not week.isdigit():
                    continue
                for i, q in enumerate(st.session_state.data[selected_subject][week]):
                    weighted_score = None
                    if "scores" in q and q["scores"]:
                        weighted_score = calculate_weighted_score(q["scores"])
                    
                    if weighted_score is None or weighted_score <= min_score:
                        questions_queue.append({
                            "subject": selected_subject,
                            "week": week,
                            "question_idx": i,
                            "question": q["question"],
                            "answer": q["answer"],
                            "weighted_score": weighted_score,
                            "last_practiced": q.get("last_practiced", None)
                        })
        else:
            for i, q in enumerate(st.session_state.data[selected_subject][selected_week]):
                weighted_score = None
                if "scores" in q and q["scores"]:
                    weighted_score = calculate_weighted_score(q["scores"])
                
                if weighted_score is None or weighted_score <= min_score:
                    questions_queue.append({
                        "subject": selected_subject,
                        "week": selected_week,
                        "question_idx": i,
                        "question": q["question"],
                        "answer": q["answer"],
                        "weighted_score": weighted_score,
                        "last_practiced": q.get("last_practiced", None)
                    })
        
        # Apply order modes
        if st.session_state.practice_order == "Random":
            random.shuffle(questions_queue)
        elif st.session_state.practice_order == "Needs Practice":
            # Sort by weighted score (lowest first) and then by last practiced time (oldest first)
            questions_queue.sort(key=lambda x: (
                5 if x["weighted_score"] is None else x["weighted_score"],  # None scores get highest value
                0 if x["last_practiced"] is None else -x["last_practiced"]   # None last_practiced get highest priority
            ))
        
        return questions_queue, all_subjects, all_weeks
    
    # Practice setup screen
    if not st.session_state.practice_active:
        if not st.session_state.data:
            st.warning("No questions available. Add some questions first!")
            st.link_button("Go to Add Cards with AI", "/render_add_ai")
        else:
            st.subheader("Practice Setup")
            
            all_subjects = list(st.session_state.data.keys())
            all_weeks = set()
            for subject in all_subjects:
                # Filter out metadata keys
                weeks = [w for w in st.session_state.data[subject].keys() 
                       if w != "vector_store_metadata" and w.isdigit()]
                all_weeks.update(weeks)
            
            # Create a two-row layout for better organization
            row1_col1, row1_col2 = st.columns(2)
            
            # First row: Subject and Week selectors
            with row1_col1:
                st.session_state.practice_subject = st.selectbox(
                    "Subject", 
                    ["All"] + all_subjects,
                    index=0
                )
                
                # Create a more descriptive filter for knowledge level
                st.markdown("##### Filter by Knowledge Level")
                st.caption("Practice questions based on how well you know them:")
                
                # Create the options for the dropdown with descriptive labels
                knowledge_level_options = {
                    0: "0 - 🆕 New questions only",
                    1: "1 - 🟥 New + struggling questions",
                    2: "2 - 🟧 Questions needing improvement",
                    3: "3 - 🟨 Questions with moderate knowledge",
                    4: "4 - 🟩 Questions with good knowledge",
                    5: "5 - ⬜ All questions"
                }
                
                # Create a selectbox with the descriptive options
                selected_level = st.selectbox(
                    "Maximum knowledge level to practice:",
                    options=list(knowledge_level_options.keys()),
                    format_func=lambda x: knowledge_level_options[x],
                    index=st.session_state.min_score_threshold,
                    help="Only practice questions you've scored at or below this level. Lower values help you focus on material you need to improve on."
                )
                
                # Update the session state with the selected value
                st.session_state.min_score_threshold = selected_level
                
                # Show additional explanation for the selected level
                if selected_level == 0:
                    st.info("You'll practice questions you've never seen before. Perfect for getting started with new material.")
                elif selected_level == 1:
                    st.info("You'll practice new questions and ones you're struggling with (rated 0-1). Great for exam preparation.")
                elif selected_level == 2:
                    st.info("You'll practice questions needing improvement (rated 0-2). Good for focusing on challenging material.")
                elif selected_level == 3:
                    st.info("You'll practice questions with moderate knowledge (rated 0-3). Balanced practice for better retention.")
                elif selected_level == 4:
                    st.info("You'll practice questions with good knowledge (rated 0-4). Useful for comprehensive review.")
                else:  # 5
                    st.info("You'll practice all questions regardless of your knowledge level. Best for full review sessions.")
            
            with row1_col2:
                available_weeks = ["All"]
                if st.session_state.practice_subject != "All":
                    # Only show weeks for the selected subject (filter out metadata)
                    subject_weeks = [w for w in st.session_state.data[st.session_state.practice_subject].keys()
                                    if w != "vector_store_metadata" and w.isdigit()]
                    available_weeks += sorted(subject_weeks, key=int)
                else:
                    # Show all weeks across all subjects
                    available_weeks += sorted(list(all_weeks), key=int)
                    
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
            
            # Question container
            with st.container(border=True):
                st.write(f"**Subject:** {current_q['subject']}, **Week:** {current_q['week']}")
                
                # Question display
                st.markdown("### Question:")
                st.markdown(f"**{current_q['question']}**")
                
                # Answer section
                st.markdown("### Your Answer:")
                user_answer = st.text_area("Type your answer here (optional)", key=f"user_answer_{st.session_state.current_question_idx}", height=100)
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    button_row1 = st.columns([1, 1])
                    with button_row1[0]:
                        if st.button("Show Answer", use_container_width=True):
                            st.session_state.show_answer = True
                            st.rerun()
                    
                    with button_row1[1]:
                        # Only show the AI feedback button if user has premium access
                        if is_subscribed:
                            if st.session_state.enable_ai_feedback and st.button("Get AI Feedback", use_container_width=True):
                                if not user_answer.strip():
                                    st.error("Please provide an answer to evaluate.")
                                else:
                                    # Create a placeholder for streaming status updates
                                    feedback_placeholder = st.empty()
                                    feedback_placeholder.markdown("Analyzing your answer...")
                                    
                                    # Define the stream handler function for feedback
                                    def feedback_stream_handler(content):
                                        if "evaluating" in content.lower():
                                            feedback_placeholder.markdown("Evaluating your response...")
                                        elif "analyzing" in content.lower():
                                            feedback_placeholder.markdown("Analyzing key concepts...")
                                        elif "comparing" in content.lower():
                                            feedback_placeholder.markdown("Comparing with expected answer...")
                                        elif "finalizing" in content.lower():
                                            feedback_placeholder.markdown("Finalizing feedback...")
                                    
                                    # Get the AI feedback
                                    st.session_state.feedback = evaluate_answer(
                                        current_q["question"],
                                        user_answer,
                                        current_q["answer"],
                                        stream_handler=feedback_stream_handler
                                    )
                                    
                                    # Clear the placeholder
                                    feedback_placeholder.empty()
                                    
                                    # Save the score, user answer, and AI feedback to the question
                                    if "question_idx" in current_q and st.session_state.feedback.get("score") is not None:
                                        score = st.session_state.feedback.get("score")
                                        
                                        # First save the score using the existing function
                                        try:
                                            # Try with user_answer parameter (new format)
                                            st.session_state.data = update_question_score(
                                                st.session_state.data,
                                                current_q["subject"],
                                                current_q["week"],
                                                current_q["question_idx"],
                                                score,
                                                user_answer,  # Include user's answer
                                                user_email  # Include user's email
                                            )
                                        except TypeError:
                                            # Fall back to old format without user_answer
                                            st.session_state.data = update_question_score(
                                                st.session_state.data,
                                                current_q["subject"],
                                                current_q["week"],
                                                current_q["question_idx"],
                                                score,
                                                None,  # No user answer
                                                user_email  # Include user's email
                                            )
                                        
                                        # Then add the AI feedback to the most recent score entry
                                        subject = current_q["subject"]
                                        week = current_q["week"]
                                        idx = current_q["question_idx"]
                                        
                                        if (subject in st.session_state.data and 
                                            week in st.session_state.data[subject] and 
                                            idx < len(st.session_state.data[subject][week]) and
                                            "scores" in st.session_state.data[subject][week][idx] and
                                            st.session_state.data[subject][week][idx]["scores"]):
                                            
                                            # Get the most recent score entry
                                            latest_score = st.session_state.data[subject][week][idx]["scores"][-1]
                                            
                                            # Add feedback data
                                            latest_score["ai_feedback"] = {
                                                "feedback": st.session_state.feedback.get("feedback", ""),
                                                "hint": st.session_state.feedback.get("hint", "")
                                            }
                                        
                                        save_data(st.session_state.data, user_email)
                                        # Mark as rated to disable rating buttons
                                        st.session_state.rating_submitted = True
                                        # Automatically show the expected answer
                                        st.session_state.show_answer = True
                                    st.rerun()
                        else:
                            # Disabled button for non-premium users
                            st.button("Get AI Feedback (Premium)", use_container_width=True, disabled=True, help="AI feedback requires a premium subscription")
                            st.info("🔒 AI feedback is a premium feature.")
                
                # Navigation buttons
                with col2:
                    prev_disabled = st.session_state.current_question_idx == 0
                    if st.button("Previous", disabled=prev_disabled, use_container_width=True):
                        st.session_state.current_question_idx -= 1
                        st.session_state.show_answer = False
                        st.session_state.feedback = None
                        st.session_state.rating_submitted = False
                        st.session_state.chat_messages = []
                        st.rerun()
                
                with col3:
                    next_disabled = st.session_state.current_question_idx == len(st.session_state.questions_queue) - 1
                    if st.button("Next", disabled=next_disabled, use_container_width=True):
                        st.session_state.current_question_idx += 1
                        st.session_state.show_answer = False
                        st.session_state.feedback = None
                        st.session_state.rating_submitted = False
                        st.session_state.chat_messages = []
                        st.rerun()
                
                with col4:
                    # Button for random jump
                    if len(st.session_state.questions_queue) > 1:
                        if st.button("Random Question", use_container_width=True):
                            new_idx = st.session_state.current_question_idx
                            while new_idx == st.session_state.current_question_idx:
                                new_idx = random.randint(0, len(st.session_state.questions_queue) - 1)
                            st.session_state.current_question_idx = new_idx
                            st.session_state.show_answer = False
                            st.session_state.feedback = None
                            st.session_state.rating_submitted = False
                            st.session_state.chat_messages = []
                            st.rerun()
                
                # Self-rating section - only show if AI feedback is not enabled
                if not (is_subscribed and st.session_state.enable_ai_feedback):
                    st.markdown("---")
                    st.markdown("### Rate Your Answer:")
                    
                    # Check if rating has already been submitted for this question
                    if st.session_state.rating_submitted:
                        st.success("Rating submitted! Continue to the next question or try another.")
                    else:
                        rating_cols = st.columns(5)
                        for i in range(5):
                            rating_value = i + 1  # Creates scores: 1, 2, 3, 4, 5
                            with rating_cols[i]:
                                rating_emoji = "🟢" if rating_value >= 4 else "🟠" if rating_value >= 2 else "🔴"
                                btn_label = f"{rating_emoji} {rating_value}"
                                if st.button(btn_label, key=f"self_rate_{rating_value}", use_container_width=True, help=f"Rate your answer as {rating_value}/5"):
                                    # Save the self-rated score and user answer
                                    if "question_idx" in current_q:
                                        try:
                                            # Try with user_answer parameter (new format)
                                            st.session_state.data = update_question_score(
                                                st.session_state.data,
                                                current_q["subject"],
                                                current_q["week"],
                                                current_q["question_idx"],
                                                rating_value,
                                                user_answer,  # Include user's answer
                                                user_email  # Include user's email
                                            )
                                        except TypeError:
                                            # Fall back to old format without user_answer
                                            st.session_state.data = update_question_score(
                                                st.session_state.data,
                                                current_q["subject"],
                                                current_q["week"],
                                                current_q["question_idx"],
                                                rating_value,
                                                None,  # No user answer
                                                user_email  # Include user's email
                                            )
                                        save_data(st.session_state.data, user_email)
                                        st.session_state.rating_submitted = True
                                        st.success(f"Saved self-rating: {rating_value}/5")
                                        st.rerun()
                
                # Display AI feedback if available
                if st.session_state.feedback:
                    st.markdown("---")
                    st.markdown("### AI Feedback:")
                    
                    score = st.session_state.feedback.get("score", 0)
                    feedback = st.session_state.feedback.get("feedback", "No feedback available.")
                    hint = st.session_state.feedback.get("hint")
                    
                    # Score with emoji indicator
                    score_emoji = "🟢" if score >= 4 else "🟠" if score >= 2 else "🔴"
                    st.markdown(f"**Score:** {score_emoji} {score}/5")
                    
                    # Feedback
                    st.markdown(f"**Feedback:** {feedback}")
                    
                    # Hint (if available and score < 4)
                    if hint:
                        st.markdown(f"**Hint:** {hint}")
                    
                    # No buttons here to keep the interface cleaner
                    
                    # Initialize the chat if needed
                    if st.session_state.feedback and is_subscribed and st.session_state.enable_ai_feedback:
                        if "chat_messages" not in st.session_state:
                            st.session_state.chat_messages = []
                            
                        # st.markdown("---")
                        # st.markdown("### Chat with Socratic AI Tutor")
                        # st.info("Ask questions about this topic and I'll guide you to deeper understanding through the Socratic method.")
                        
                        # Get the vector store ID if available
                        vector_store_id = None
                        if current_q["subject"] and current_q["week"]:
                            vector_store_id = get_vector_store_id(current_q["subject"], current_q["week"])
                        
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
                                        feedback=st.session_state.feedback,
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
                        
                # Display expected answer if requested
                if st.session_state.show_answer:
                    st.markdown("---")
                    st.markdown("### Expected Answer:")
                    if current_q["answer"]:
                        st.markdown(current_q["answer"])
                    else:
                        st.info("No expected answer was provided for this question.")
                        
                # Display question's score history if it exists
                if "question_idx" in current_q:
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
                                    score_emoji = "🟢" if score >= 4 else "🟠" if score >= 2 else "🔴"
                                    
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
                
"""
UI components for practice module.

This module provides UI elements and display functions for practice functionality.
"""
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from st_paywall import add_auth

# Import from core module
from features.content.practice.practice_core import (
    get_score_emoji, get_cached_vector_store_id, reset_question_state,
    save_score_with_answer, save_ai_feedback_to_data, go_to_next_question,
    save_data, get_random_question_index, build_cached_queue, build_queue,
    analytics_service  # Import analytics_service instead of update_question_score
)

# Import from base and external modules
from features.content.base_content import get_user_email
from ai_feedback import evaluate_answer, chat_about_question

def display_self_rating_buttons(current_q: Dict, user_answer: str, user_email: str):
    """Display self-rating buttons and handle rating submission"""
    print(f"\n=== Starting self-rating process ===")
    print(f"Current question: {current_q.get('subject')} - Week {current_q.get('week')} - Question {current_q.get('question_idx')}")
    print(f"User email: {user_email}")
    
    # Check if rating has already been submitted for this question
    if st.session_state.rating_submitted:
        print("Rating already submitted for this question")
        st.success("Rating submitted! Continue to the next question or try another.")
    else:
        rating_cols = st.columns(5)
        for i in range(5):
            rating_value = i + 1  # Creates scores: 1, 2, 3, 4, 5
            with rating_cols[i]:
                rating_emoji = get_score_emoji(rating_value)
                btn_label = f"{rating_emoji} {rating_value}"
                if st.button(btn_label, key=f"self_rate_{rating_value}", use_container_width=True, help=f"Rate your answer as {rating_value}/5"):
                    print(f"\n=== Rating button clicked ===")
                    print(f"Selected rating: {rating_value}")
                    try:
                        # Save the self-rated score and user answer
                        if "question_idx" in current_q:
                            print("Updating in-memory data...")
                            # First update the data in memory
                            st.session_state.data = save_score_with_answer(
                                st.session_state.data,
                                current_q,
                                rating_value,
                                user_answer,
                                user_email
                            )
                            print("In-memory data updated successfully")
                            
                            print("Saving to MongoDB...")
                            # Then persist to storage
                            save_data(st.session_state.data, user_email)
                            print("MongoDB save completed")
                            
                            # Update session state
                            st.session_state.rating_submitted = True
                            st.success(f"Saved self-rating: {rating_value}/5")
                            print("Session state updated")
                            st.rerun()
                    except Exception as e:
                        error_msg = f"Failed to save rating: {str(e)}"
                        print(f"ERROR: {error_msg}")
                        st.error(error_msg)
                        # Log the error for debugging
                        import traceback
                        print(f"Full error traceback:\n{traceback.format_exc()}")

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
    
    # Get user input first
    user_message = st.chat_input("Ask a question about this concept...", key=chat_input_key)
    
    # Display all messages and handle new messages in the container
    with chat_message_container:
        # Display existing messages
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

def display_knowledge_level_selector():
    """Display and handle the knowledge level filter selector"""
    # Import KNOWLEDGE_LEVEL_OPTIONS from practice_core
    from features.content.practice.practice_core import KNOWLEDGE_LEVEL_OPTIONS
    
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
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    
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
            go_to_next_question()
            reset_question_state()
            st.rerun()
    
    with col4:
        # Button for random jump
        if queue_length > 1:
            if st.button("Random Question", use_container_width=True):
                from features.content.practice.practice_core import get_random_question_index
                new_idx = get_random_question_index(current_idx, queue_length)
                st.session_state.current_question_idx = new_idx
                reset_question_state()
                st.rerun()
    
    with col5:
        # Reshuffle button (only show in random mode)
        if st.session_state.get('practice_order') == "Random" and queue_length > 1:
            if st.button("🔄 Reshuffle", use_container_width=True, help="Reshuffle the question queue"):
                # Clear the cache to force a new random order
                build_cached_queue.clear()
                # Rebuild the queue
                questions_queue, _, _ = build_queue()
                st.session_state.questions_queue = questions_queue
                # Get a new random starting point
                st.session_state.current_question_idx = get_random_question_index(-1, queue_length)
                reset_question_state()
                st.rerun()
    
    # Return the column for AI feedback button
    return ai_feedback_col

def display_setup_screen(is_authenticated):
    """Display practice setup options"""
    st.subheader("Practice Setup")
    
    # Get unique subjects and weeks
    data_subjects = sorted(list(st.session_state.data.keys()))
    
    if not data_subjects:
        st.warning("No subjects available. Add some questions first!")
        st.link_button("Go to Add Cards with AI", "/render_add_ai")
        return
    
    # Create subjects list (without "All" option)
    subjects = data_subjects
    
    # Default values
    default_subject = data_subjects[0] if data_subjects else ""
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
    week_options = available_weeks

    # Initialize selected_weeks from session state BEFORE rendering the multiselect
    selected_weeks_from_state = st.session_state.get("practice_weeks", [])

    # Set display text based on whether weeks are selected IN THE STATE
    if not selected_weeks_from_state:  # Check state value
        display_text = "Select weeks (leave empty for all)"
    else:
        display_text = "Select weeks"

    # Render the multiselect, using the state value as the default
    selected_weeks = st.multiselect(
        display_text,
        options=week_options,
        default=selected_weeks_from_state, # Use state value for default
        key="practice_weeks"
    )

    # Set practice week based on the selection FROM THE WIDGET
    if not selected_weeks:
        st.session_state.practice_week = ""
        # Also ensure selected_practice_weeks is empty
        st.session_state.selected_practice_weeks = []
        st.info("Practicing with all available weeks.")
    else:
        # If multiple weeks selected, store all selected weeks
        if len(selected_weeks) > 1:
            st.session_state.practice_week = selected_weeks[0]  # Use first week as primary
            # Store the selected weeks in a new session state variable
            st.session_state.selected_practice_weeks = selected_weeks
            st.info(f"Practicing with selected weeks: {', '.join(selected_weeks)}")
        else:
            try:
                st.session_state.practice_week = selected_weeks[0]
                st.session_state.selected_practice_weeks = selected_weeks
            except (IndexError, TypeError):
                # Handle case where selected_weeks is empty or not a list
                st.session_state.practice_week = ""
                st.session_state.selected_practice_weeks = []
                st.info("Defaulting to all available weeks.")
    
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
    
    # Add score filter
    st.markdown("##### Score Filter")
    st.caption("Filter out questions you've already mastered:")
    
    # Initialize max_score_threshold in session state if not exists
    if "max_score_threshold" not in st.session_state:
        st.session_state.max_score_threshold = 5  # Default to showing all questions
    
    # Create score filter slider
    max_score = st.slider(
        "Maximum score to practice:",
        min_value=0,
        max_value=5,
        value=st.session_state.max_score_threshold,
        help="Only practice questions you've scored at or below this level. Lower values help you focus on material you need to improve on."
    )
    
    # Update the session state with the selected value
    st.session_state.max_score_threshold = max_score
    
    # Show additional explanation for the selected level
    score_explanations = {
        0: "You'll only practice questions you've never seen before or scored 0 on.",
        1: "You'll practice questions you're struggling with (scored 0-1).",
        2: "You'll practice questions needing improvement (scored 0-2).",
        3: "You'll practice questions with moderate knowledge (scored 0-3).",
        4: "You'll practice questions with good knowledge (scored 0-4).",
        5: "You'll practice all questions regardless of your score."
    }
    
    st.info(score_explanations[max_score])
    
    # Start practice button
    start_button = st.button("Start Practice", type="primary", use_container_width=True)
    
    if start_button:
        if not is_authenticated:
            # User needs to be authenticated to start practice
            st.warning("Please sign in to start practicing.")
            # Use st-paywall directly
            add_auth(
                required=True,
                login_button_text="Sign in to Study Legend",
                login_button_color="#FF6F00",
            )
            return
            
        # Prepare queue of questions
        queue = []
        if subject in st.session_state.data:
            # If no weeks selected, use all weeks
            weeks_to_use = selected_weeks if selected_weeks else available_weeks
            
            for week in weeks_to_use:
                if week in st.session_state.data[subject]:
                    questions_list = st.session_state.data[subject][week]
                    
                    for i, q in enumerate(questions_list):
                        # Only add questions that have questions
                        if "question" in q and q["question"]:
                            # Check if the question meets the score threshold
                            should_include = True
                            if "scores" in q and q["scores"]:
                                # Get the most recent score
                                latest_score = q["scores"][-1]["score"]
                                if latest_score > st.session_state.max_score_threshold:
                                    should_include = False
                            
                            if should_include:
                                queue.append({
                                    "subject": subject,
                                    "week": week,
                                    "question_idx": i,  # Change from "index" to "question_idx" to match expected format
                                    "question": q["question"],  # Include the actual question text
                                    "answer": q["answer"],      # Include the answer text
                                    "idx": i  # Add idx key for question_key tracking
                                })
        
        # Shuffle if random mode
        if practice_mode == "Random":
            import random
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
        from mongodb.queue_cards import update_single_question_score
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
        # Handle both old and new question data format for backward compatibility
        subject = question_data.get('subject', '')
        week = question_data.get('week', '')
        
        # Get the question text - could be directly in question_data or in question_data['data']
        question_text = ''
        if 'question' in question_data:
            question_text = question_data['question']
        elif 'data' in question_data and 'question' in question_data['data']:
            question_text = question_data['data']['question']
            
        # Get the answer text
        answer_text = ''
        if 'answer' in question_data:
            answer_text = question_data['answer']
        elif 'data' in question_data and 'answer' in question_data['data']:
            answer_text = question_data['data']['answer']
            
        # Display the question header and text
        st.markdown(f"**Subject:** {subject} - Week {week}")
        st.markdown(f"### Q: {question_text}")
        
        # Remember this question key for tracking
        # Handle both idx and index formats
        idx = question_data.get('idx', question_data.get('index', question_data.get('question_idx', 0)))
        question_key = (
            subject,
            week,
            idx
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
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            # Show Answer button - just shows the answer without AI feedback
            if st.button("Show Answer", use_container_width=True):
                if not is_authenticated:
                    st.warning("Please sign in to view the answer.")
                    # Use st-paywall directly
                    add_auth(
                        required=True,
                        login_button_text="Sign in to Study Legend",
                        login_button_color="#FF6F00",
                    )
                    return
                
                st.session_state.show_answer = True
                st.rerun()
        
        with col2:
            # Check Answer with AI button - shows answer and provides AI feedback
            if st.button("Check Answer with AI", use_container_width=True):
                if not is_authenticated:
                    st.warning("Please sign in to check your answer with AI.")
                    # Use st-paywall directly
                    add_auth(
                        required=True,
                        login_button_text="Sign in to Study Legend",
                        login_button_color="#FF6F00",
                    )
                    return
                    
                st.session_state.show_answer = True
                
                # Check if user provided an answer
                if not user_answer or user_answer.strip() == "":
                    # Set default feedback for empty answer
                    st.session_state.feedback = {
                        "score": 0,
                        "feedback": "No answer provided. Please provide your answer before checking with AI.",
                        "hint": "Try to write down your thoughts about the question, even if you're not completely sure."
                    }
                else:
                    # Generate AI feedback
                    with st.spinner("Analyzing your answer..."):
                        try:
                            feedback_result = evaluate_answer(
                                question_text,
                                user_answer,
                                answer_text
                            )
                            
                            # Store feedback in session state
                            st.session_state.feedback = feedback_result
                            
                            # Clear chat messages when new feedback is generated
                            st.session_state.chat_messages = []
                            
                            # Save answer and feedback together if user is authenticated
                            if is_authenticated and user_email:
                                try:
                                    # Save the answer with the AI-generated score
                                    st.session_state.data = save_score_with_answer(
                                        st.session_state.data,
                                        {
                                            "subject": subject,
                                            "week": week,
                                            "question_idx": idx
                                        },
                                        feedback_result.get("score", 0),  # Use AI-generated score
                                        user_answer,
                                        user_email
                                    )
                                    
                                    # Save the AI feedback
                                    from mongodb.queue_cards import save_ai_feedback
                                    save_ai_feedback(
                                        user_email,
                                        {
                                            "subject": subject,
                                            "week": week,
                                            "idx": idx,
                                            "question_idx": idx,
                                            "question": question_text,
                                            "answer": answer_text,
                                            "user_answer": user_answer
                                        },
                                        feedback_result
                                    )
                                    print("Answer and feedback saved successfully")
                                except Exception as e:
                                    print(f"Error saving answer and feedback: {str(e)}")
                        except Exception as e:
                            st.error(f"Error generating feedback: {str(e)}")
                            st.session_state.feedback = {
                                "score": 0,
                                "explanation": "Could not generate feedback. Please try again."
                            }
                
                # Rerun to show feedback
                st.rerun()
                
        with col3:
            # Always show next question button to allow skipping questions
            if st.button("Next Question →", use_container_width=True):
                print("\n=== Next Question button clicked ===")
                # Save the current rating before moving to the next question (if authenticated)
                if is_authenticated and st.session_state.show_answer:
                    print("User is authenticated and answer is shown")
                    # Get the self rating from the session state
                    self_rating = st.session_state.get(f"self_rating_{st.session_state.current_question_idx}")
                    print(f"Self rating from session state: {self_rating}")
                    
                    if self_rating is not None and user_email:
                        print(f"Attempting to save rating {self_rating} for user {user_email}")
                        try:
                            # Update the score using save_score_with_answer
                            st.session_state.data = save_score_with_answer(
                                st.session_state.data,
                                {
                                    "subject": question_data["subject"],
                                    "week": question_data["week"],
                                    "question_idx": question_data["idx"]
                                },
                                self_rating,
                                user_answer,
                                user_email
                            )
                            print("Score saved successfully")
                        except Exception as e:
                            print(f"Error saving score: {str(e)}")
                            import traceback
                            print(f"Full error traceback:\n{traceback.format_exc()}")
                
                # Move to the next question
                go_to_next_question()
                st.rerun()
        
        # Display answer and feedback if show_answer is True
        if st.session_state.show_answer:
            # Display answer
            st.markdown("---")
            st.markdown("### Answer:")
            st.markdown(answer_text)
            
            # Display AI feedback if available
            if st.session_state.feedback:
                st.markdown("---")
                st.markdown("### AI Feedback:")
                
                feedback = st.session_state.feedback
                score = feedback.get("score", 0)
                explanation = feedback.get("feedback", "No explanation provided.")
                hint = feedback.get("hint")
                
                # Create a score color based on the score
                if score >= 4:
                    score_color = "green"
                elif score >= 2:
                    score_color = "orange"
                else:
                    score_color = "red"
                
                # Display score - changed from /10 to /5
                st.markdown(f"**Score:** <span style='color:{score_color};font-size:18px;'>{score}/5</span>", unsafe_allow_html=True)
                
                # Display explanation
                st.markdown(f"**Feedback:** {explanation}")
                
                # Display hint if available
                if hint:
                    st.markdown(f"**Hint:** {hint}")
                
                # Add retry button
                if st.button("🔄 Retry Question", use_container_width=True):
                    # Reset the question state
                    st.session_state.user_answer = ""
                    st.session_state.feedback = None
                    st.session_state.show_answer = False
                    st.session_state.chat_messages = []
                    st.rerun()
                
                # Only show self-rating if authenticated
                if is_authenticated:
                    # Self-rating section
                    st.markdown("### How would you rate your answer?")
                    self_rating = st.slider(
                        "Your self-assessment (0-5)",
                        min_value=0,
                        max_value=5,
                        value=min(score, 5),  # Cap at 5 for the slider
                        step=1,
                        key=f"self_rating_{st.session_state.current_question_idx}"
                    )
                    
                    # Save the rating in session state
                    if question_key not in st.session_state.question_ratings:
                        st.session_state.question_ratings[question_key] = self_rating
                    
                    # Chat with AI about the question
                    st.markdown("---")
                    st.markdown("### Chat with AI about this question")
                    
                    # Create a container for the entire chat interface
                    chat_interface_container = st.container()
                    
                    with chat_interface_container:
                        # Create a container for chat messages with a fixed height
                        chat_messages_container = st.container(height=400)
                        
                        # Create a placeholder for the chat input
                        chat_input_placeholder = st.empty()
                        
                        with chat_messages_container:
                            # Display previous chat messages
                            for message in st.session_state.chat_messages:
                                role = message["role"]
                                content = message["content"]
                                
                                if role == "user":
                                    st.chat_message("user").write(content)
                                else:
                                    st.chat_message("assistant").write(content)
                        
                        # Chat input at the bottom of the chat interface container
                        chat_input = chat_input_placeholder.chat_input("Ask a question about this topic...")
                        
                        if chat_input:
                            # Add user message to chat history
                            st.session_state.chat_messages.append({
                                "role": "user",
                                "content": chat_input
                            })
                            
                            # Immediately display the user's message
                            with chat_messages_container:
                                st.chat_message("user").write(chat_input)
                                
                                # Stream the AI response as a new assistant message
                                with st.chat_message("assistant"):
                                    message_placeholder = st.empty()
                                    full_response = ""
                                    
                                    def stream_handler(content):
                                        nonlocal full_response
                                        full_response += content
                                        message_placeholder.markdown(full_response + "▌")
                                    
                                    ai_response = chat_about_question(
                                        question_text,
                                        answer_text,
                                        user_answer,
                                        st.session_state.feedback,
                                        subject,
                                        week,
                                        chat_messages=st.session_state.chat_messages,
                                        stream_handler=stream_handler
                                    )
                                    message_placeholder.markdown(full_response)
                                
                                # Add AI response to chat history
                                st.session_state.chat_messages.append({
                                    "role": "assistant",
                                    "content": full_response
                                })
                    
                    # Add Show Attempts History button after chat
                    st.markdown("---")
                    
                    # Initialize show_attempts in session state if it doesn't exist
                    if "show_attempts" not in st.session_state:
                        st.session_state.show_attempts = False
                    
                    # Toggle button for attempt history
                    if st.button("📚 " + ("Hide Attempt History" if st.session_state.show_attempts else "Show Attempt History")):
                        st.session_state.show_attempts = not st.session_state.show_attempts
                        st.rerun()
                    
                    # Display attempt history if toggled on
                    if st.session_state.show_attempts:
                        with st.container(border=True):
                            if subject in st.session_state.data and week in st.session_state.data[subject] and idx < len(st.session_state.data[subject][week]):
                                question_data_from_state = st.session_state.data[subject][week][idx]
                                scores = question_data_from_state.get("scores", [])
                                
                                if scores:
                                    st.markdown("### Attempt History")
                                    
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
                                else:
                                    st.info("No previous attempts for this question.")
                    
                else:
                    # Show login prompt for chat functionality
                    st.info("Sign in to rate your answers and chat with AI about this question.") 
            else:
                if user_email:  # Only show rating if user is logged in
                    display_self_rating_buttons(question_data, user_answer, user_email)
    
    # Return the question data for chat processing
    return {
        "question_text": question_text,
        "answer_text": answer_text,
        "user_answer": user_answer,
        "subject": subject,
        "week": week
    }

def handle_chat_input(question_info: Dict, is_authenticated: bool):
    """This function is no longer needed as chat input is now handled within the display_practice_question function"""
    pass
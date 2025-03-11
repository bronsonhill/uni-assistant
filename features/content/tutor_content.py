import streamlit as st
import sys
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import from Home and rag_manager
import Home
import mongodb
from rag_manager import RAGManager
from paywall import check_subscription, show_premium_benefits, display_subscription_status

def run():
    """Main tutor page content - this gets run by the navigation system"""
    # Check subscription status - required for this premium feature
    is_subscribed, user_email = check_subscription(required=True)
    
    # Display subscription status in sidebar
    display_subscription_status()
    
    # If user is not subscribed, the above function will redirect them
    # The code below will only execute for subscribed users
    
    # Initialize session state for chat
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = None
    
    if "assistant_id" not in st.session_state:
        st.session_state.assistant_id = None
    
    if "rag_manager" not in st.session_state:
        # Initialize RAG manager only for the current user if logged in
        user_email = st.session_state.get("email")
        st.session_state.rag_manager = Home.init_rag_manager(email=user_email)
    
    # For storing subject/week selections (needed when loading from history)
    if "selected_subject" not in st.session_state:
        st.session_state.selected_subject = None
        
    if "selected_week" not in st.session_state:
        st.session_state.selected_week = None
        
    # For storing chat title
    if "chat_title" not in st.session_state:
        st.session_state.chat_title = None
        
    # For tracking current chat session ID
    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = None
    
    # Load data
    if "data" not in st.session_state:
        # Load data only for the current user if logged in
        user_email = st.session_state.get("email")
        st.session_state.data = Home.load_data(email=user_email)
    
    # Title and description
    st.title("💬 Chat with Subject Tutor")
    st.markdown("""
    Talk to your personal AI study buddy who knows your course materials!
    Ask questions, get explanations, and deepen your understanding of course topics.
    """)
    
    # Function to create or get a thread
    def get_or_create_thread():
        """Create a new thread if one doesn't exist"""
        if st.session_state.thread_id is None:
            try:
                thread = st.session_state.rag_manager.client.beta.threads.create()
                st.session_state.thread_id = thread.id
                return thread.id
            except Exception as e:
                st.error(f"Error creating thread: {str(e)}")
                return None
        return st.session_state.thread_id
    
    # Function to create an assistant with access to course materials
    def create_assistant_for_chat(vector_store_id: str):
        """Create or get an assistant that can access the selected course materials"""
        try:
            # Create a new assistant focused on explaining concepts
            assistant = st.session_state.rag_manager.client.beta.assistants.create(
                name="Course Assistant",
                instructions="""You are a helpful teaching assistant for university students.
    Your goal is to help students understand concepts from their course materials.
    Always provide thorough, accurate explanations based on the content you have access to.
    If you're not sure about something, be clear about that rather than making up information.
    Use examples and analogies when helpful to explain complex topics.""",
                model="gpt-4o",
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}}
            )
            
            st.session_state.assistant_id = assistant.id
            return assistant.id
        except Exception as e:
            st.error(f"Error creating assistant: {str(e)}")
            return None
    
    # Function to send a message and get a response
    def send_message(message: str, vector_store_id: str, subject: str, week: str, stream_handler=None, stream=True):
        """
        Send a message to the assistant and get a response
        
        Args:
            message: Message to send
            vector_store_id: Vector store ID to use
            subject: Subject of the conversation
            week: Week of the conversation
            stream_handler: Optional callback function for streaming responses
            stream: Whether to use streaming (default True)
        
        Returns:
            The assistant's response text
        """
        try:
            # Make sure we have a thread
            thread_id = get_or_create_thread()
            
            if not thread_id:
                return "Error: Could not create or retrieve thread."
            
            # Make sure we have an assistant
            if st.session_state.assistant_id is None:
                assistant_id = create_assistant_for_chat(vector_store_id)
                if not assistant_id:
                    return "Error: Could not create assistant."
            else:
                assistant_id = st.session_state.assistant_id
            
            # Add the user message to the thread
            st.session_state.rag_manager.client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=message
            )
            
            # Create a run
            run = st.session_state.rag_manager.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                stream=stream
            )
            
            response_text = ""
            
            # Handle streaming if requested
            if stream and stream_handler:
                # Process the stream
                for chunk in run:
                    if chunk.event == "thread.message.delta" and hasattr(chunk, "data") and hasattr(chunk.data, "delta") and hasattr(chunk.data.delta, "content"):
                        for content in chunk.data.delta.content:
                            if content.type == "text" and hasattr(content.text, "value"):
                                delta_text = content.text.value
                                response_text += delta_text
                                stream_handler(delta_text)
            else:
                # Wait for the run to complete without streaming
                while run.status in ["queued", "in_progress"]:
                    time.sleep(1)
                    run = st.session_state.rag_manager.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                
                # Get the latest messages (should include the assistant's response)
                messages = st.session_state.rag_manager.client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                
                # Find the assistant's response (the most recent assistant message)
                response_text = "No response from the assistant."
                for message in messages.data:
                    if message.role == "assistant":
                        # Extract and return the text content
                        response_text = ""
                        for content in message.content:
                            if content.type == "text":
                                response_text += content.text.value
                        break
            
            # Save the conversation to MongoDB if we have a user email
            if "email" in st.session_state and st.session_state.email:
                # Get or create chat title
                chat_title = None
                if "chat_title" in st.session_state and st.session_state.chat_title:
                    chat_title = st.session_state.chat_title
                
                # Save conversation to MongoDB
                mongodb.save_chat_session(
                    email=st.session_state.email,
                    subject=subject,
                    week=week,
                    vector_store_id=vector_store_id,
                    messages=st.session_state.chat_messages + [{"role": "assistant", "content": response_text}],
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    chat_type=mongodb.CHAT_TYPE_TUTOR,
                    title=chat_title
                )
            
            return response_text
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Subject and week selection layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Add tabs for material selection and chat history
        select_tab, history_tab = st.tabs(["Select Material", "Chat History"])
        
        with select_tab:
            st.subheader("Select Course Material")
            
            # Check if course materials have been loaded
            if not st.session_state.rag_manager.vector_stores:
                # Try to reload course materials directly from the session state data
                st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data)
                
                # If still no course materials, show debugging info and error
                if not st.session_state.rag_manager.vector_stores:
                    # Check if course materials metadata exists in the data
                    has_metadata = False
                    metadata_info = []
                    
                    for subject in st.session_state.data:
                        if isinstance(st.session_state.data[subject], dict) and "vector_store_metadata" in st.session_state.data[subject]:
                            has_metadata = True
                            metadata_info.append(f"Subject: {subject}, Weeks: {list(st.session_state.data[subject]['vector_store_metadata'].keys())}")
                    
                    if has_metadata:
                        st.error("Your course materials were found but couldn't be loaded properly. This might be due to a connection issue.")
                        with st.expander("Technical Details"):
                            st.write("Course materials found for:")
                            for info in metadata_info:
                                st.write(info)
                    else:
                        st.warning("No course materials found. Please upload your study materials first.")
                    
                    st.markdown("### Upload Materials")
                    st.info("To add your course materials, go to 'Add Queue Cards with AI' and upload your files.")
                    st.button("Go to Add Cards with AI", on_click=lambda: st.switch_page("features/1_🤖_Add_Queue_Cards_with_AI.py"))
                    st.stop()
        
        # Get subjects that have course materials
        subjects_with_materials = []
        for subject in st.session_state.data:
            if isinstance(st.session_state.data[subject], dict) and "vector_store_metadata" in st.session_state.data[subject]:
                # Verify that this subject has valid course materials
                has_valid_materials = False
                for week in st.session_state.data[subject]["vector_store_metadata"]:
                    store_key = f"{subject}_{week}"
                    if store_key in st.session_state.rag_manager.vector_stores:
                        has_valid_materials = True
                        break
                
                if has_valid_materials:
                    subjects_with_materials.append(subject)
        
        if not subjects_with_materials:
            st.warning("No course materials found. Please upload materials in the 'Add Queue Cards with AI' page first.")
            st.button("Go to Add Cards with AI", on_click=lambda: st.switch_page("features/1_🤖_Add_Queue_Cards_with_AI.py"))
            st.stop()
            
        # Determine initial subject selection
        default_index = 0
        if st.session_state.selected_subject and st.session_state.selected_subject in subjects_with_materials:
            default_index = subjects_with_materials.index(st.session_state.selected_subject)
        
        # Subject selection
        selected_subject = st.selectbox(
            "Select subject",
            options=subjects_with_materials,
            index=default_index if subjects_with_materials else None
        )
        
        # Store the selected subject in session state
        st.session_state.selected_subject = selected_subject
        
        # Week selection - only show weeks that have valid materials
        weeks_with_materials = []
        if selected_subject and "vector_store_metadata" in st.session_state.data[selected_subject]:
            for week in st.session_state.data[selected_subject]["vector_store_metadata"]:
                store_key = f"{selected_subject}_{week}"
                if store_key in st.session_state.rag_manager.vector_stores:
                    weeks_with_materials.append(week)
            
        if not weeks_with_materials:
            st.warning(f"No course materials found for {selected_subject}. Please upload materials again in the 'Add Cards with AI' page first.")
            st.button("Go to Add Cards with AI", on_click=lambda: st.switch_page("features/1_🤖_Add_Queue_Cards_with_AI.py"))
            st.stop()
            
        # Determine initial week selection
        default_week_index = 0
        if (st.session_state.selected_week and 
            st.session_state.selected_week in weeks_with_materials):
            default_week_index = weeks_with_materials.index(st.session_state.selected_week)
            
        selected_week = st.selectbox(
            "Select week",
            options=weeks_with_materials,
            index=default_week_index if weeks_with_materials else None
        )
        
        # Store the selected week in session state
        st.session_state.selected_week = selected_week
        
        # Get vector store ID
        vector_store_id = None
        if (selected_subject and selected_week and 
            "vector_store_metadata" in st.session_state.data[selected_subject] and
            selected_week in st.session_state.data[selected_subject]["vector_store_metadata"]):
            vector_store_id = st.session_state.data[selected_subject]["vector_store_metadata"][selected_week]["id"]
        
        # Reset chat button
        if st.button("Reset Chat", type="secondary"):
            st.session_state.chat_messages = []
            st.session_state.thread_id = None
            st.session_state.assistant_id = None
            st.rerun()
            
        # Add the chat history tab content
        with history_tab:
            st.subheader("Chat History")
            
            # Check if user is logged in
            if "email" not in st.session_state or not st.session_state.email:
                st.info("Please log in to view your chat history.")
            else:
                # Get chat history from MongoDB (filter to tutor chats only)
                user_email = st.session_state.email
                chat_sessions = mongodb.get_chat_sessions(user_email, chat_type=mongodb.CHAT_TYPE_TUTOR)
                
                if not chat_sessions:
                    st.info("No chat history found. Start a conversation to create history.")
                else:
                    # Display chat sessions
                    for session in chat_sessions:
                        # Use title if available, otherwise create one from subject and week
                        if 'title' in session and session['title']:
                            session_title = f"{session['title']} ({session.get('updated_at_readable', 'Unknown date')})"
                        else:
                            session_title = f"{session.get('subject', 'Unknown')} - Week {session.get('week', 'Unknown')} ({session.get('updated_at_readable', 'Unknown date')})"
                        
                        # Create an expander with preview of last message
                        with st.expander(session_title):
                            # Show session details
                            st.markdown(f"**Last message:** {session.get('last_message', 'No messages')[:100]}...")
                            
                            # Create a row for buttons
                            btn_col1, btn_col2, btn_col3 = st.columns([1, 1.2, 1])
                            
                            # Add option to load this conversation
                            session_id = session.get("_id")
                            with btn_col1:
                                if st.button(f"Load", key=f"load_{session_id}"):
                                    # Load the full session
                                    full_session = mongodb.get_chat_session(session_id)
                                    
                                    if full_session:
                                        # Set the session state variables to match this conversation
                                        st.session_state.chat_messages = full_session.get("messages", [])
                                        st.session_state.thread_id = full_session.get("thread_id")
                                        st.session_state.assistant_id = full_session.get("assistant_id")
                                        st.session_state.current_chat_id = session_id
                                        
                                        # Set the custom title if available
                                        if 'title' in full_session:
                                            st.session_state.chat_title = full_session.get("title")
                                        
                                        # Set the subject and week
                                        subject = full_session.get("subject")
                                        week = full_session.get("week")
                                        
                                        # Check if these are valid and try to set them
                                        if subject in st.session_state.data and "vector_store_metadata" in st.session_state.data[subject]:
                                            # Update the selection if the subject exists
                                            st.session_state.selected_subject = subject
                                            
                                            # Check if the week is valid for this subject
                                            if week in st.session_state.data[subject]["vector_store_metadata"]:
                                                st.session_state.selected_week = week
                                        
                                        # Rerun to update the UI
                                        st.rerun()
                                    else:
                                        st.error(f"Could not load conversation with ID: {session_id}")
                            
                            # Add option to rename this conversation
                            with btn_col2:
                                if st.button(f"Rename", key=f"rename_{session_id}"):
                                    # Store the session ID in session state to show rename form
                                    st.session_state[f"rename_session_{session_id}"] = True
                                    st.rerun()
                            
                            # Add option to delete this conversation
                            with btn_col3:
                                if st.button(f"Delete", key=f"delete_{session_id}", type="secondary"):
                                    success = mongodb.delete_chat_session(session_id, user_email)
                                    if success:
                                        st.success("Conversation deleted successfully.")
                                        # Reset current chat ID if this was the active chat
                                        if st.session_state.current_chat_id == session_id:
                                            st.session_state.current_chat_id = None
                                        # Rerun to update the list
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete conversation. Please try again.")
                            
                            # Show rename form if button was clicked
                            if st.session_state.get(f"rename_session_{session_id}", False):
                                st.write("---")
                                st.write("Rename conversation:")
                                
                                # Get current title or default
                                current_title = session.get('title', f"{session.get('subject', 'Unknown')} - Week {session.get('week', 'Unknown')}")
                                new_title = st.text_input("New title:", value=current_title, key=f"new_title_{session_id}")
                                
                                rename_col1, rename_col2 = st.columns(2)
                                with rename_col1:
                                    if st.button("Save", key=f"save_rename_{session_id}"):
                                        success = mongodb.rename_chat_session(
                                            session_id, 
                                            user_email, 
                                            new_title
                                        )
                                        if success:
                                            st.success("Conversation renamed successfully.")
                                            # Update current chat title if this was the active chat
                                            if st.session_state.current_chat_id == session_id:
                                                st.session_state.chat_title = new_title
                                            # Reset rename state and rerun to update
                                            st.session_state[f"rename_session_{session_id}"] = False
                                            st.rerun()
                                        else:
                                            st.error("Failed to rename conversation. Please try again.")
                                
                                with rename_col2:
                                    if st.button("Cancel", key=f"cancel_rename_{session_id}", type="secondary"):
                                        # Reset rename state and rerun
                                        st.session_state[f"rename_session_{session_id}"] = False
                                        st.rerun()
        
        # Information about the chat
        with st.expander("About this feature"):
            st.markdown("""
            ### How it works
            
            This chat connects you with an AI study buddy that knows your course materials.
            
            Your study buddy can:
            - Answer questions about your uploaded materials
            - Explain difficult concepts
            - Help you understand challenging topics
            - Provide helpful examples and analogies
            
            For best results:
            - Ask specific questions
            - Upload complete course materials
            - Use this alongside practicing with flashcards
            """)
        
        with st.expander("Troubleshooting"):
            st.markdown("""
            ### Common Issues
            
            #### "No materials found" message
            If you're seeing this error even though you've uploaded files:
            
            1. Go to "Add Cards with AI" page
            2. Upload your materials again
            3. Make sure you see "Materials successfully processed" message
            4. Return to this page and try again
            
            #### Connection Issues
            Sometimes the system might experience temporary connection problems:
            
            1. Check your internet connection
            2. Wait a few minutes and try again
            3. Refresh the page
            
            #### Your study buddy doesn't know your materials
            If the AI doesn't seem to know about your uploaded content:
            
            1. Make sure you've selected the correct subject and week
            2. Try uploading your materials again with better quality files
            3. Break large files into smaller chunks when uploading
            """)
    
    with col2:
        st.subheader("Chat")
        
        # Check if course materials are selected
        if not vector_store_id:
            st.info("Please select a subject and week with uploaded course materials to start chatting.")
            st.stop()
        
        # Chat interface
        chat_container = st.container(height=500, border=True)
        
        # Add custom title input for the chat
        if st.session_state.chat_messages:
            # Create a collapsible section for managing the chat
            with st.expander("Chat Settings", expanded=False):
                # Show current title or set a default
                current_title = st.session_state.chat_title or f"{selected_subject} - Week {selected_week}"
                new_chat_title = st.text_input("Chat title:", value=current_title, key="chat_title_input")
                
                # Update chat title if changed
                if new_chat_title != current_title:
                    st.session_state.chat_title = new_chat_title
                    
                    # Update in database if we have a current chat ID
                    if st.session_state.current_chat_id and "email" in st.session_state:
                        mongodb.rename_chat_session(
                            st.session_state.current_chat_id,
                            st.session_state.email,
                            new_chat_title
                        )
        
        with chat_container:
            # Display chat messages
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # User input with a specific key for tutor chat
        user_message = st.chat_input("Ask a question about your course materials...", key="tutor_chat_input")
        
        if user_message:
            # Add user message to chat history
            st.session_state.chat_messages.append({"role": "user", "content": user_message})
            
            # Display user message
            with chat_container:
                with st.chat_message("user"):
                    st.write(user_message)
            
            # Display assistant message with streaming
            with chat_container:
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
                    
                    # Get assistant response with streaming
                    response = send_message(
                        message=user_message, 
                        vector_store_id=vector_store_id,
                        subject=selected_subject,
                        week=selected_week,
                        stream_handler=stream_handler,
                        stream=True
                    )
                    
                    # Update the final response without the cursor
                    message_placeholder.markdown(full_response)
            
            # Add assistant response to chat history
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            
            # Force a rerun to update the UI
            st.rerun()
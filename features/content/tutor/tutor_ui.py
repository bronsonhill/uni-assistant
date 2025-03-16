"""
UI components for tutor module.

This module provides UI elements and display functions for the Subject Tutor feature.
"""
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from st_paywall import add_auth
import mongodb

# Import core functionality
from features.content.tutor.tutor_core import (
    send_message,
    reset_chat,
    get_vector_store_for_subject_week,
    load_chat_session,
    is_valid_vector_store
)

# Import utility functions
from features.content.tutor.vector_store_manager import extract_vector_store_id

# Import RAG manager initialization
from features.content.tutor import init_rag_manager

def display_subject_selection():
    """
    Display subject and week selection UI
    
    Returns:
        Tuple of (selected_subject, selected_week, vector_store_id)
    """
    # Check for data
    if "data" not in st.session_state:
        st.error("No data loaded. Please refresh the page.")
        return None, None, None
    
    # Initialize RAG manager
    user_email = st.session_state.get('email')
    if user_email:
        init_rag_manager(user_email)
    
    # Debug toggle for advanced users
    show_debug = st.sidebar.checkbox("Show Vector Store Debug Info", value=False)
    if show_debug:
        _display_vector_store_debug_info()
    
    # Get subjects that have vector store metadata
    subjects_with_materials = []
    for subject in st.session_state.data.keys():
        if "vector_store_metadata" in st.session_state.data[subject]:
            # Only include the subject if it has at least one vector store
            if st.session_state.data[subject]["vector_store_metadata"]:
                subjects_with_materials.append(subject)
    
    if not subjects_with_materials:
        st.info("No course materials found. Please upload materials in the 'Add with AI' section first.")
        return None, None, None
    
    # Subject selection
    selected_subject = st.selectbox(
        "Select subject",
        options=subjects_with_materials,
        index=0 if subjects_with_materials else None,
        key="subject_selection"
    )
    
    # Week selection - only show weeks that have vector stores
    week_options = []
    if selected_subject and "vector_store_metadata" in st.session_state.data[selected_subject]:
        week_options = list(st.session_state.data[selected_subject]["vector_store_metadata"].keys())
    
    if not week_options:
        st.info(f"No course materials found for {selected_subject}. Please upload materials first.")
        return selected_subject, None, None
    
    selected_week = st.selectbox(
        "Select week",
        options=week_options,
        index=0 if week_options else None,
        key="week_selection"
    )
    
    # Get vector store ID
    vector_store_id = None
    if selected_subject and selected_week:
        vector_store_id = get_vector_store_for_subject_week(selected_subject, selected_week)
    
    return selected_subject, selected_week, vector_store_id

def display_chat_history(user_email: Optional[str], on_load_callback: Callable = None):
    """Display the chat history tab and handle loading sessions"""
    st.subheader("Chat History")
    
    # Check if user is logged in
    if user_email is None:
        st.info("Please log in to view your chat history.")
        return
    
    # Get chat history from MongoDB (filter to tutor chats only)
    chat_sessions = mongodb.get_chat_sessions(user_email, chat_type=mongodb.CHAT_TYPE_TUTOR)
    
    if not chat_sessions:
        st.info("No chat history found. Start a conversation to create history.")
        return
    
    # Display chat sessions
    st.write(f"Found {len(chat_sessions)} saved conversations:")
    
    for session in chat_sessions:
        # Extract session data
        session_id = session.get("_id")
        title = session.get("title", "Untitled Conversation")
        
        # Get subject and week
        subject = session.get("subject", "Unknown")
        week = session.get("week", "Unknown")
        
        # Get timestamp and format it
        timestamp = session.get("timestamp", datetime.now())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now()
        
        formatted_date = timestamp.strftime("%b %d, %Y at %I:%M %p")
        
        # Create session card
        with st.container(border=True):
            # Row 1: Title and time
            st.caption(f"{formatted_date}")
            st.markdown(f"**{title}**")
            st.caption(f"Subject: {subject}, Week: {week}")
            
            # Row 2: Button actions
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if st.button(f"Load", key=f"load_{session_id}"):
                    # Load the full session
                    subject, week = load_chat_session(session_id)
                    
                    # Run the callback if provided
                    if on_load_callback:
                        on_load_callback(subject, week)
                    
                    # Rerun to update UI
                    st.rerun()
            
            with btn_col2:
                # Only allow renaming if it's the current chat
                is_current = session_id == st.session_state.get("current_chat_id")
                
                if st.button(f"Rename", key=f"rename_{session_id}", disabled=not is_current):
                    # Enable rename mode in session state
                    st.session_state.renaming_chat = True
                    st.session_state.rename_chat_id = session_id
                    st.session_state.rename_chat_title = title
                    st.rerun()
            
            with btn_col3:
                if st.button(f"Delete", key=f"delete_{session_id}"):
                    # Delete the session
                    mongodb.delete_chat_session(session_id, user_email)
                    
                    # If this was the current chat, reset the chat
                    if session_id == st.session_state.get("current_chat_id"):
                        reset_chat()
                    
                    # Rerun to update UI
                    st.rerun()
    
    # Handle renaming a chat
    if st.session_state.get("renaming_chat", False):
        with st.form(key="rename_form"):
            new_title = st.text_input(
                "New title:",
                value=st.session_state.get("rename_chat_title", ""),
                key="new_chat_title"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                submit = st.form_submit_button("Save")
            
            with col2:
                cancel = st.form_submit_button("Cancel")
            
            if submit and new_title:
                # Update the title in MongoDB
                mongodb.rename_chat_session(
                    st.session_state.rename_chat_id,
                    user_email,
                    new_title
                )
                
                # Update in session state
                st.session_state.chat_title = new_title
                st.session_state.renaming_chat = False
                st.rerun()
            
            if cancel:
                st.session_state.renaming_chat = False
                st.rerun()

def display_chat_interface(vector_store_id: str, selected_subject: str, selected_week: str):
    """Display the chat interface and handle messages"""
    st.subheader("Chat")
    
    # Extract ID if we received a dictionary
    actual_id = extract_vector_store_id(vector_store_id)
    if actual_id != vector_store_id:
        print(f"Extracted vector store ID in display_chat_interface: {actual_id} (from {type(vector_store_id).__name__})")
    
    # Check if course materials are selected
    if not actual_id:
        st.warning("⚠️ No course materials are available for this subject and week.")
        st.info("To use the Subject Tutor, please:")
        st.markdown("""
        1. Go to the **Add with AI** feature
        2. Upload PDF documents, lecture notes, or textbooks
        3. Select the same subject and week you're trying to chat about
        4. Process the files to create a knowledge base
        """)
        return
    
    # Check if the vector store is valid (has content)
    if not is_valid_vector_store(actual_id):
        st.warning("⚠️ The selected subject materials appear to be empty or invalid.")
        st.info("Please make sure you've successfully uploaded and processed course materials in the **Add with AI** feature.")
        return
    
    # Display the file management component
    from features.content.tutor.vector_store_manager import display_vector_store_files
    display_vector_store_files(actual_id, selected_subject, selected_week)
    
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
                    vector_store_id=actual_id,
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

def display_vector_store_files(vector_store_id: str, selected_subject: str, selected_week: str):
    """
    Display and manage files in a vector store
    
    Args:
        vector_store_id: The ID of the vector store
        selected_subject: The selected subject name
        selected_week: The selected week number/name
    """
    if not vector_store_id:
        st.info("Please select a subject and week first.")
        return
        
    # Create a container for the file management UI
    with st.expander("📚 Manage Course Materials", expanded=False):
        st.write(f"Managing materials for: **{selected_subject} - Week {selected_week}**")
        
        # Get the list of files in the vector store
        if not hasattr(st.session_state, 'rag_manager') or st.session_state.rag_manager is None:
            st.error("RAG Manager not initialized. Please refresh the page.")
            return
        
        files = st.session_state.rag_manager.list_vector_store_files(vector_store_id)
        
        # Display the files
        if not files:
            st.info("No files found in this knowledge base. Upload files to add them.")
        else:
            st.markdown("### Current Files")
            for file in files:
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        filename = file.get('filename', 'Unknown file')
                        created_at = file.get('created_at')
                        if created_at:
                            date_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d")
                            st.write(f"**{filename}** (Added: {date_str})")
                        else:
                            st.write(f"**{filename}**")
                    
                    with col2:
                        # Delete button for each file
                        file_id = file.get('id')
                        if st.button("🗑️ Delete", key=f"delete_{file_id}"):
                            try:
                                deleted = st.session_state.rag_manager.delete_vector_store_file(vector_store_id, file_id)
                                if deleted:
                                    st.success(f"Deleted: {filename}")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        
        # Add new files
        st.markdown("### Add New Files")
        uploaded_files = st.file_uploader(
            "Upload PDF, TXT, or other documents",
            type=["pdf", "txt", "docx", "md"],
            accept_multiple_files=True,
            key=f"vector_store_upload_{vector_store_id}"
        )
        
        if uploaded_files:
            if st.button("Process Files", use_container_width=True):
                for uploaded_file in uploaded_files:
                    try:
                        file_bytes = uploaded_file.getvalue()
                        st.session_state.rag_manager.add_file_to_vector_store(
                            vector_store_id=vector_store_id,
                            file_bytes=file_bytes,
                            file_name=uploaded_file.name
                        )
                        st.success(f"Added: {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                st.rerun() 

def _display_vector_store_debug_info():
    """Display debug information about vector stores"""
    st.sidebar.markdown("### Vector Store Debug Info")
    
    # Display vector store metadata for each subject
    if "data" in st.session_state:
        for subject in st.session_state.data.keys():
            if "vector_store_metadata" in st.session_state.data[subject]:
                st.sidebar.markdown(f"**Subject: {subject}**")
                
                for week, metadata in st.session_state.data[subject]["vector_store_metadata"].items():
                    st.sidebar.markdown(f"Week {week}:")
                    
                    # Show the raw metadata with more detail
                    metadata_type = type(metadata).__name__
                    metadata_format = "Unknown"
                    
                    if isinstance(metadata, dict) and "id" in metadata:
                        metadata_format = "Dictionary with 'id' key"
                    elif isinstance(metadata, str):
                        if metadata.startswith("{") and "id" in metadata:
                            metadata_format = "JSON string with 'id' key"
                        elif metadata.startswith("vs_"):
                            metadata_format = "Plain vector store ID string"
                    
                    st.sidebar.code(f"Type: {metadata_type}\nFormat: {metadata_format}\nValue: {metadata}")
                    
                    # Process metadata to extract the ID using our utility function
                    vector_store_id = extract_vector_store_id(metadata)
                    
                    if vector_store_id != metadata:
                        st.sidebar.success(f"Extracted ID: {vector_store_id}")
                    else:
                        st.sidebar.info(f"ID: {vector_store_id}")
                    
                    # Check if the ID is valid
                    if vector_store_id:
                        if not isinstance(vector_store_id, str):
                            st.sidebar.error(f"ID is not a string: {type(vector_store_id).__name__}")
                        elif len(vector_store_id) > 64:
                            st.sidebar.error(f"ID too long: {len(vector_store_id)} chars")
                        elif not str(vector_store_id).startswith("vs_"):
                            st.sidebar.warning("ID format may be incorrect (should start with 'vs_')")
                        else:
                            st.sidebar.success("ID format looks valid")
                        
                        # Add a test button
                        if st.sidebar.button(f"Test Vector Store: {subject}-{week}", key=f"test_{subject}_{week}"):
                            try:
                                rag_manager = st.session_state.get('rag_manager')
                                if rag_manager:
                                    # Use our utility function to ensure we have the correct ID
                                    id_to_test = extract_vector_store_id(vector_store_id)
                                    
                                    files = rag_manager.list_vector_store_files(id_to_test)
                                    if files:
                                        st.sidebar.success(f"Success! Found {len(files)} files")
                                        for file in files:
                                            st.sidebar.info(f"- {file.get('filename', 'Unknown')}")
                                    else:
                                        st.sidebar.warning("Vector store exists but has no files")
                                else:
                                    st.sidebar.error("RAG Manager not initialized")
                            except Exception as e:
                                st.sidebar.error(f"Test failed: {str(e)}")
    
    # Add a repair button to fix any invalid formats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Repair Tools")
    
    if st.sidebar.button("Repair All Vector Stores", key="repair_all_vector_stores"):
        try:
            from Home import force_cleanup_vector_store_data
            
            with st.sidebar.spinner("Cleaning up vector store data..."):
                cleanup_count = force_cleanup_vector_store_data(st.session_state.get('email'))
                if cleanup_count > 0:
                    st.sidebar.success(f"Fixed {cleanup_count} vector store entries!")
                    # Force page reload
                    st.rerun()
                else:
                    st.sidebar.info("No issues found requiring repair.")
        except Exception as e:
            st.sidebar.error(f"Error during repair: {str(e)}")
    
    # Add a separator
    st.sidebar.markdown("---") 
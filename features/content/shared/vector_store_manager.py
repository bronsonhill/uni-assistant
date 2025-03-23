"""
Shared vector store management module.

This module provides common functions to manage vector stores across different features.
"""
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import from Home
from Home import load_data, save_data

# Import common utilities
from features.content.shared.vector_store_common import extract_vector_store_id

def init_rag_manager(user_email: str):
    """
    Initialize the RAG manager and load vector stores
    
    Args:
        user_email: The user's email address
        
    Returns:
        True if initialization was successful, False otherwise
    """
    if "rag_manager" not in st.session_state or not hasattr(st.session_state.rag_manager, 'delete_vector_store'):
        try:
            # Import here to avoid circular imports
            from rag_manager import RAGManager
            
            # Reinitialize if we don't have the expected methods
            print("Initializing RAGManager with all required methods")
            st.session_state.rag_manager = RAGManager()
            # Load any existing study materials from data
            if "data" in st.session_state:
                st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data, user_email)
            return True
        except Exception as e:
            print(f"Error initializing RAGManager: {e}")
            st.session_state.rag_manager = None
            return False
    return True

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
    
    # Extract ID if we received a dictionary
    actual_id = extract_vector_store_id(vector_store_id)
    if actual_id != vector_store_id:
        print(f"Extracted vector store ID in display_vector_store_files: {actual_id} (from {type(vector_store_id).__name__})")
        
    # Create a container for the file management UI
    with st.expander("📚 Manage Course Materials", expanded=False):
        st.write(f"Managing materials for: **{selected_subject} - Week {selected_week}**")
        
        # Ensure rag_manager is initialized
        if not hasattr(st.session_state, 'rag_manager') or st.session_state.rag_manager is None:
            user_email = st.session_state.get('email')
            if user_email:
                init_success = init_rag_manager(user_email)
                if not init_success:
                    st.error("RAG Manager could not be initialized. Please refresh the page.")
                    return
            else:
                st.error("User not recognized. Please refresh the page.")
                return
        
        # Try to get files with error handling
        try:
            print(f"Listing vector store files with ID (length {len(actual_id)}): {actual_id}")
            files = st.session_state.rag_manager.list_vector_store_files(actual_id)
        except Exception as e:
            st.error(f"Error accessing vector store: {str(e)}")
            # Check for common error cases
            if "string too long" in str(e) or "above_max_length" in str(e) or len(actual_id) > 64:
                st.warning("The vector store ID is too long. OpenAI API requires IDs to be 64 characters or less.")
                st.info("Please use the 'Repair Vector Store Data' button below to fix this issue.")
                
                col1, col2 = st.columns(2)
                
                # Add repair button
                with col1:
                    if st.button("🔧 Repair All Vector Stores", use_container_width=True):
                        try:
                            from Home import force_cleanup_vector_store_data
                            
                            with st.spinner("Cleaning up invalid vector store IDs..."):
                                cleanup_count = force_cleanup_vector_store_data(st.session_state.get('email'))
                                if cleanup_count > 0:
                                    st.success(f"Fixed {cleanup_count} invalid vector store IDs!")
                                    # Force page reload
                                    st.rerun()
                                else:
                                    st.info("No issues found requiring repair.")
                        except Exception as repair_error:
                            st.error(f"Error during repair: {str(repair_error)}")
                
                # Add reset button for this specific vector store
                with col2:
                    if st.button("🗑️ Reset This Vector Store", use_container_width=True):
                        try:
                            from Home import reset_vector_store_id
                            
                            with st.spinner(f"Resetting vector store for {selected_subject} - Week {selected_week}..."):
                                success = reset_vector_store_id(selected_subject, selected_week, st.session_state.get('email'))
                                if success:
                                    st.success(f"Successfully reset vector store for {selected_subject} - Week {selected_week}")
                                    # Force page reload
                                    st.rerun()
                                else:
                                    st.warning("Could not find vector store to reset.")
                        except Exception as reset_error:
                            st.error(f"Error during reset: {str(reset_error)}")
                        
                # Add option to create new vector store
                st.markdown("---")
                st.markdown("After resetting, you can upload new files to create a new knowledge base for this subject/week.")
                
            elif "not found" in str(e):
                st.warning("This vector store may have been deleted or is no longer accessible.")
                
                # Add reset button for this specific vector store
                if st.button("🗑️ Reset This Vector Store", use_container_width=True):
                    try:
                        from Home import reset_vector_store_id
                        
                        with st.spinner(f"Resetting vector store for {selected_subject} - Week {selected_week}..."):
                            success = reset_vector_store_id(selected_subject, selected_week, st.session_state.get('email'))
                            if success:
                                st.success(f"Successfully reset vector store for {selected_subject} - Week {selected_week}")
                                # Force page reload
                                st.rerun()
                            else:
                                st.warning("Could not find vector store to reset.")
                    except Exception as reset_error:
                        st.error(f"Error during reset: {str(reset_error)}")
            return
        
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
                                deleted = st.session_state.rag_manager.delete_vector_store_file(actual_id, file_id)
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
            key=f"vector_store_upload_{actual_id}"
        )
        
        if uploaded_files:
            if st.button("Process Files", use_container_width=True):
                for uploaded_file in uploaded_files:
                    try:
                        file_bytes = uploaded_file.getvalue()
                        st.session_state.rag_manager.add_file_to_vector_store(
                            vector_store_id=actual_id,
                            file_bytes=file_bytes,
                            file_name=uploaded_file.name
                        )
                        st.success(f"Added: {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
                st.rerun()

def display_enhanced_kb_management():
    """Display enhanced knowledge base management with vector store file management"""
    # st.subheader("Knowledge Base Management")
    
    # Check if we have any knowledge bases
    has_kb = False
    kb_data = []
    
    for subject in st.session_state.data:
        if "vector_store_metadata" in st.session_state.data[subject]:
            for week, vector_store_id in st.session_state.data[subject]["vector_store_metadata"].items():
                has_kb = True
                # Extract the ID to show a cleaner view
                actual_id = extract_vector_store_id(vector_store_id)
                kb_data.append({
                    "Subject": subject,
                    "Week": week,
                    "ID": actual_id
                })
    
    if not has_kb:
        st.info("No knowledge bases found. Upload files to create knowledge bases.")
        return
    
    # Let user select knowledge base to manage
    st.markdown("### Manage Knowledge Base Files")
    st.info("Select a subject and week to manage its files (view, add, or delete files)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Subject selection dropdown
        subjects_with_kb = list(set([item["Subject"] for item in kb_data]))
        selected_subject = st.selectbox(
            "Subject",
            options=subjects_with_kb,
            key="manage_kb_subject"
        )
    
    with col2:
        # Week selection dropdown (filtered by subject)
        weeks_for_subject = [item["Week"] for item in kb_data if item["Subject"] == selected_subject]
        selected_week = st.selectbox(
            "Week",
            options=weeks_for_subject,
            key="manage_kb_week"
        )
    
    # Get vector store ID for selection
    vector_store_id = None
    if selected_subject and selected_week:
        if (selected_subject in st.session_state.data and 
            "vector_store_metadata" in st.session_state.data[selected_subject] and
            str(selected_week) in st.session_state.data[selected_subject]["vector_store_metadata"]):
            
            vector_store_id = st.session_state.data[selected_subject]["vector_store_metadata"][str(selected_week)]
    
    # Display file management for selected knowledge base
    if vector_store_id:
        display_vector_store_files(vector_store_id, selected_subject, selected_week)
    else:
        st.warning("No knowledge base found for the selected subject and week.")
    
    # Delete knowledge base section
    st.markdown("### Delete Knowledge Base")
    st.warning("⚠️ Deleting a knowledge base will remove the stored course material but not the questions already generated.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Subject selection dropdown
        delete_subject = st.selectbox(
            "Subject",
            options=subjects_with_kb,
            key="delete_subject"
        )
    
    with col2:
        # Week selection dropdown
        weeks_for_subject = [item["Week"] for item in kb_data if item["Subject"] == delete_subject]
        delete_week = st.selectbox(
            "Week",
            options=weeks_for_subject,
            key="delete_week"
        )
    
    # Delete button
    if st.button("Delete Knowledge Base", key="delete_kb", type="secondary", use_container_width=True):
        # Confirm deletion
        if delete_subject and delete_week:
            # Import delete function (should be moved to shared module as well)
            from features.content.shared.vector_store_utils import delete_vector_store
            
            success = delete_vector_store(delete_subject, delete_week, st.session_state.get('email'))
            
            if success:
                st.success(f"Successfully deleted knowledge base for {delete_subject} - Week {delete_week}")
                # Force page reload
                st.rerun()
            else:
                st.error("Error deleting knowledge base. Please try again later.") 
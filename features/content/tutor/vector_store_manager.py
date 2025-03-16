"""
Vector store management module.

This module provides functions to manage vector store files for the Subject Tutor feature.
"""
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional

# Import RAG manager initialization
from features.content.tutor import init_rag_manager

def extract_vector_store_id(vector_store_id: Any) -> str:
    """
    Safely extract a vector store ID from various formats
    
    Args:
        vector_store_id: The vector store ID in any format (dict, JSON string, or plain string)
        
    Returns:
        Extracted vector store ID as string
    """
    # Case 1: None value
    if not vector_store_id:
        return None
    
    # Case 2: Dictionary with id field
    if isinstance(vector_store_id, dict) and "id" in vector_store_id:
        return vector_store_id["id"]
    
    # Case 3: JSON string in format: "{\"id\":\"vs_xxx\",\"name\":\"Subject_Week\"}"
    if isinstance(vector_store_id, str) and vector_store_id.startswith("{") and "id" in vector_store_id:
        try:
            import json
            parsed = json.loads(vector_store_id)
            if isinstance(parsed, dict) and "id" in parsed:
                return parsed["id"]
        except Exception as e:
            print(f"Error parsing vector store JSON: {e}")
            # Fall through to return the original string
    
    # Case 4: Plain string ID or fallback
    return vector_store_id

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
"""
Initialization for the tutor module.

This module initializes the tutor component, including RAG manager initialization.
"""
import os
import sys
import streamlit as st
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import RAG manager
from rag_manager import RAGManager

def init_rag_manager(user_email: str):
    """Initialize the RAG manager and load vector stores"""
    try:
        # Check if we already have a valid RAG manager
        if hasattr(st.session_state, 'rag_manager') and st.session_state.rag_manager is not None:
            # Verify the RAG manager is working by checking if it has the required methods
            if hasattr(st.session_state.rag_manager, 'delete_vector_store'):
                print("Using existing RAG manager")
                return True
            else:
                print("Existing RAG manager is invalid, reinitializing")
                st.session_state.rag_manager = None

        # Initialize new RAG manager
        print("Initializing new RAGManager")
        st.session_state.rag_manager = RAGManager()
        
        # Verify the client was initialized
        if not hasattr(st.session_state.rag_manager, 'client') or st.session_state.rag_manager.client is None:
            print("Failed to initialize OpenAI client")
            st.error("Failed to initialize AI service. Please check your API key and try again.")
            return False
            
        # Load any existing study materials from data
        if "data" in st.session_state:
            print(f"Loading vector stores for user: {user_email}")
            st.session_state.rag_manager.load_vector_stores_from_data(st.session_state.data, user_email)
            
        print("RAGManager initialized successfully")
        return True
        
    except Exception as e:
        error_details = traceback.format_exc()
        print(f"Error initializing RAGManager: {str(e)}\n{error_details}")
        st.error(f"Failed to initialize AI service: {str(e)}")
        st.session_state.rag_manager = None
        return False

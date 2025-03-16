"""
Initialization for the tutor module.

This module initializes the tutor component, including RAG manager initialization.
"""
import os
import sys
import streamlit as st

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import RAG manager
from rag_manager import RAGManager

def init_rag_manager(user_email: str):
    """Initialize the RAG manager and load vector stores"""
    if "rag_manager" not in st.session_state or not hasattr(st.session_state.rag_manager, 'delete_vector_store'):
        try:
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

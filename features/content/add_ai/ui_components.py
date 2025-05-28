import streamlit as st
from typing import List, Dict, Optional, Any
from services.rag_manager import RAGManager

class QuestionGeneratorUI:
    def __init__(self, rag_manager: RAGManager):
        """Initialize the UI with RAG Manager"""
        self.rag_manager = rag_manager
    
    def render(self):
        """Render the question generator UI"""
        self._render_subject_week_inputs()
        self._render_file_upload()
        self._render_custom_prompt()
        self._render_generate_button()
        self._render_question_review()
    
    def _render_subject_week_inputs(self):
        """Render subject and week inputs"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input(
                "Subject",
                key="generation_subject",
                help="Enter the subject name (e.g., Mathematics, Physics)"
            )
            
        with col2:
            st.number_input(
                "Week",
                min_value=1,
                value=1,
                key="generation_week",
                help="Enter the week number"
            )
    
    def _render_file_upload(self):
        """Render file upload interface"""
        st.subheader("Upload Content")
        
        uploaded_file = st.file_uploader(
            "Upload a file",
            type=['pdf', 'txt'],
            help="Upload study materials to generate questions from"
        )
        
        if uploaded_file:
            st.session_state.file_uploaded = True
            st.session_state.uploaded_file = uploaded_file
    
    def _render_custom_prompt(self):
        """Render custom prompt input"""
        st.subheader("Custom Instructions")
        
        st.text_area(
            "Custom Prompt",
            key="custom_questions",
            help="Add any specific instructions or context for question generation"
        )
    
    def _render_generate_button(self):
        """Render generate button"""
        if st.button("Generate Questions", disabled=st.session_state.get("generation_in_progress", False)):
            st.session_state.generation_in_progress = True
            
            try:
                # Get the uploaded file if any
                uploaded_file = st.session_state.get("uploaded_file")
                
                # Generate questions
                questions = self.rag_manager.generate_questions(
                    subject=st.session_state.generation_subject,
                    week=st.session_state.generation_week,
                    num_questions=5,  # Default value, can be made configurable
                    custom_prompt=st.session_state.get("custom_questions"),
                    email=st.session_state.get("user_email")
                )
                
                # Update session state
                st.session_state.generated_questions = questions
                
            except Exception as e:
                st.error(f"Error generating questions: {str(e)}")
            finally:
                st.session_state.generation_in_progress = False
    
    def _render_question_review(self):
        """Render question review interface"""
        if not st.session_state.get("generated_questions"):
            return
            
        st.subheader("Generated Questions")
        
        for i, question in enumerate(st.session_state.generated_questions, 1):
            with st.expander(f"Question {i}"):
                # Question text
                st.markdown(f"**Q:** {question['question']}")
                
                # Answer (initially hidden)
                if st.checkbox(f"Show Answer {i}"):
                    st.markdown(f"**A:** {question['answer']}")
                    if 'explanation' in question:
                        st.markdown(f"**Explanation:** {question['explanation']}")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Edit {i}"):
                        self._edit_question(i-1)
                with col2:
                    if st.button(f"Delete {i}"):
                        self._delete_question(i-1)

    def _edit_question(self, index: int):
        """Edit a specific question"""
        if 0 <= index < len(st.session_state.generated_questions):
            question = st.session_state.generated_questions[index]
            
            # Create a form for editing
            with st.form(f"edit_question_{index}"):
                edited_question = st.text_area("Question", value=question['question'])
                edited_answer = st.text_area("Answer", value=question['answer'])
                edited_explanation = st.text_area("Explanation", value=question.get('explanation', ''))
                
                if st.form_submit_button("Save Changes"):
                    # Update the question
                    st.session_state.generated_questions[index] = {
                        'question': edited_question,
                        'answer': edited_answer,
                        'explanation': edited_explanation
                    }
                    st.success("Question updated successfully")

    def _delete_question(self, index: int):
        """Delete a specific question"""
        if 0 <= index < len(st.session_state.generated_questions):
            st.session_state.generated_questions.pop(index)
            st.success("Question deleted successfully") 
import streamlit as st
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseComponent:
    """Base class for all UI components with state management."""
    
    def __init__(self):
        self._state = {}

    def set_state(self, key: str, value: Any) -> None:
        """Set a state value for the component."""
        self._state[key] = value

    def get_state(self, key: str) -> Any:
        """Get a state value from the component."""
        return self._state.get(key)

class QuestionCard(BaseComponent):
    """Component for displaying a single question card."""
    
    def __init__(self, question: Dict[str, Any]):
        super().__init__()
        self.question = question
        self.set_state('show_answer', False)

    def render(self) -> None:
        """Render the question card with expandable answer."""
        st.write(f"**Question:** {self.question['question']}")
        
        if st.button("Show Answer", key=f"show_answer_{self.question.get('id', '')}"):
            self.set_state('show_answer', not self.get_state('show_answer'))
        
        if self.get_state('show_answer'):
            st.write(f"**Answer:** {self.question['answer']}")
            
            # Display score if available
            if 'score' in self.question:
                st.metric("Score", f"{self.question['score']:.2%}")

class QuestionEditor(BaseComponent):
    """Component for editing or creating questions."""
    
    def __init__(self, question: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.question = question or {}
        self.set_state('is_editing', False)

    def render(self) -> Dict[str, Any]:
        """Render the question editor form."""
        with st.form(key=f"question_editor_{self.question.get('id', 'new')}"):
            question = st.text_area(
                "Question",
                value=self.question.get("question", ""),
                key=f"question_text_{self.question.get('id', 'new')}"
            )
            
            answer = st.text_area(
                "Answer",
                value=self.question.get("answer", ""),
                key=f"answer_text_{self.question.get('id', 'new')}"
            )
            
            if st.form_submit_button("Save"):
                return {
                    "question": question,
                    "answer": answer,
                    "subject": self.question.get("subject", ""),
                    "week": self.question.get("week", 1)
                }
        return None

class QuestionList(BaseComponent):
    """Component for displaying a list of questions."""
    
    def __init__(self, questions: List[Dict[str, Any]]):
        super().__init__()
        self.questions = questions
        self.set_state('expanded_questions', set())

    def render(self) -> None:
        """Render the list of questions with expandable cards."""
        for idx, question in enumerate(self.questions):
            with st.expander(f"Question {idx + 1}"):
                QuestionCard(question).render()
                
                # Add edit and delete buttons if needed
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit", key=f"edit_{question.get('id', idx)}"):
                        self.set_state('editing_question', question)
                with col2:
                    if st.button("Delete", key=f"delete_{question.get('id', idx)}"):
                        self.set_state('deleting_question', question)

class ScoreDisplay(BaseComponent):
    """Component for displaying question scores."""
    
    def __init__(self, score: float):
        super().__init__()
        self.score = score

    def render(self) -> None:
        """Render the score display with appropriate styling."""
        st.metric(
            "Score",
            f"{self.score:.2%}",
            delta=None if self.score == 0 else f"{self.score:.2%}"
        )

class QuestionComponents:
    """Collection of question-related components and utilities."""
    
    @staticmethod
    def create_question_form(subjects: List[str]) -> Dict[str, Any]:
        """Render a form for creating a new question."""
        with st.form("create_question"):
            subject = st.selectbox("Subject", subjects)
            week = st.number_input("Week", min_value=1, max_value=52, value=1)
            question = st.text_area("Question")
            answer = st.text_area("Answer")
            
            if st.form_submit_button("Create"):
                return {
                    "subject": subject,
                    "week": week,
                    "question": question,
                    "answer": answer
                }
        return None

    @staticmethod
    def edit_question_form(question: Dict[str, Any]) -> Dict[str, Any]:
        """Render a form for editing an existing question."""
        with st.form("edit_question"):
            question_text = st.text_area("Question", value=question.get("question", ""))
            answer = st.text_area("Answer", value=question.get("answer", ""))
            
            if st.form_submit_button("Update"):
                return {
                    "id": question.get("id"),
                    "question": question_text,
                    "answer": answer,
                    "subject": question.get("subject"),
                    "week": question.get("week")
                }
        return None

    @staticmethod
    def confirm_delete(question: Dict[str, Any]) -> bool:
        """Render a confirmation dialog for deleting a question."""
        return st.button(
            "Confirm Delete",
            key=f"confirm_delete_{question.get('id', '')}",
            type="primary"
        ) 
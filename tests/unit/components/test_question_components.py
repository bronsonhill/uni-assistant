import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from features.content.shared.question_components import (
    BaseComponent,
    QuestionCard,
    QuestionEditor,
    QuestionList,
    ScoreDisplay,
    QuestionComponents
)

class TestBaseComponent(unittest.TestCase):
    def setUp(self):
        self.component = BaseComponent()

    def test_set_state(self):
        self.component.set_state('test_key', 'test_value')
        self.assertEqual(self.component.get_state('test_key'), 'test_value')

    def test_get_state_nonexistent(self):
        self.assertIsNone(self.component.get_state('nonexistent_key'))

class TestQuestionCard(unittest.TestCase):
    def setUp(self):
        self.question = {
            'id': '1',
            'question': 'Test question?',
            'answer': 'Test answer',
            'score': 0.85
        }
        self.card = QuestionCard(self.question)

    @patch('streamlit.write')
    @patch('streamlit.button')
    @patch('streamlit.metric')
    def test_render_without_answer(self, mock_metric, mock_button, mock_write):
        mock_button.return_value = False
        self.card.render()
        mock_write.assert_called_with('**Question:** Test question?')
        mock_metric.assert_not_called()

    @patch('streamlit.write')
    @patch('streamlit.button')
    @patch('streamlit.metric')
    def test_render_with_answer(self, mock_metric, mock_button, mock_write):
        mock_button.return_value = True
        self.card.render()
        mock_write.assert_any_call('**Question:** Test question?')
        mock_write.assert_any_call('**Answer:** Test answer')
        mock_metric.assert_called_with('Score', '85.00%')

class TestQuestionEditor(unittest.TestCase):
    def setUp(self):
        self.question = {
            'id': '1',
            'question': 'Test question?',
            'answer': 'Test answer',
            'subject': 'Math',
            'week': 1
        }
        self.editor = QuestionEditor(self.question)

    @patch('streamlit.form')
    @patch('streamlit.text_area')
    @patch('streamlit.form_submit_button')
    def test_render_without_submit(self, mock_submit, mock_text_area, mock_form):
        mock_submit.return_value = False
        mock_text_area.side_effect = ['Test question?', 'Test answer']
        result = self.editor.render()
        self.assertIsNone(result)

    @patch('streamlit.form')
    @patch('streamlit.text_area')
    @patch('streamlit.form_submit_button')
    def test_render_with_submit(self, mock_submit, mock_text_area, mock_form):
        mock_submit.return_value = True
        mock_text_area.side_effect = ['Updated question?', 'Updated answer']
        result = self.editor.render()
        self.assertEqual(result['question'], 'Updated question?')
        self.assertEqual(result['answer'], 'Updated answer')

class TestQuestionList(unittest.TestCase):
    def setUp(self):
        self.questions = [
            {
                'id': '1',
                'question': 'Question 1?',
                'answer': 'Answer 1'
            },
            {
                'id': '2',
                'question': 'Question 2?',
                'answer': 'Answer 2'
            }
        ]
        self.list = QuestionList(self.questions)

    @patch('streamlit.expander')
    @patch('streamlit.columns')
    @patch('streamlit.button')
    def test_render(self, mock_button, mock_columns, mock_expander):
        mock_expander.return_value.__enter__.return_value = MagicMock()
        mock_columns.return_value = [MagicMock(), MagicMock()]
        mock_button.side_effect = [False, False, False, False]
        self.list.render()
        self.assertEqual(mock_expander.call_count, 2)

class TestScoreDisplay(unittest.TestCase):
    def setUp(self):
        self.score = 0.85
        self.display = ScoreDisplay(self.score)

    @patch('streamlit.metric')
    def test_render(self, mock_metric):
        self.display.render()
        mock_metric.assert_called_with(
            'Score',
            '85.00%',
            delta='85.00%'
        )

class TestQuestionComponents(unittest.TestCase):
    @patch('streamlit.form')
    @patch('streamlit.selectbox')
    @patch('streamlit.number_input')
    @patch('streamlit.text_area')
    @patch('streamlit.form_submit_button')
    def test_create_question_form(self, mock_submit, mock_text_area, 
                                mock_number_input, mock_selectbox, mock_form):
        mock_submit.return_value = True
        mock_selectbox.return_value = 'Math'
        mock_number_input.return_value = 1
        mock_text_area.side_effect = ['New question?', 'New answer']
        
        result = QuestionComponents.create_question_form(['Math', 'Science'])
        self.assertEqual(result['subject'], 'Math')
        self.assertEqual(result['week'], 1)
        self.assertEqual(result['question'], 'New question?')
        self.assertEqual(result['answer'], 'New answer')

    @patch('streamlit.form')
    @patch('streamlit.text_area')
    @patch('streamlit.form_submit_button')
    def test_edit_question_form(self, mock_submit, mock_text_area, mock_form):
        question = {
            'id': '1',
            'question': 'Original question?',
            'answer': 'Original answer',
            'subject': 'Math',
            'week': 1
        }
        mock_submit.return_value = True
        mock_text_area.side_effect = ['Updated question?', 'Updated answer']
        
        result = QuestionComponents.edit_question_form(question)
        self.assertEqual(result['id'], '1')
        self.assertEqual(result['question'], 'Updated question?')
        self.assertEqual(result['answer'], 'Updated answer')

    @patch('streamlit.button')
    def test_confirm_delete(self, mock_button):
        question = {'id': '1', 'question': 'Test question?'}
        mock_button.return_value = True
        result = QuestionComponents.confirm_delete(question)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main() 
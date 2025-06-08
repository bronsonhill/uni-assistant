"""
Unit tests for authentication components.
"""
import unittest
from unittest.mock import patch, MagicMock
import streamlit as st
from features.content.shared.auth_components import (
    AuthenticationManager,
    SessionManager,
    require_authentication,
    require_premium,
    AuthComponents
)

class TestAuthenticationManager(unittest.TestCase):
    def setUp(self):
        self.mock_user_service = MagicMock()
        self.auth_manager = AuthenticationManager(self.mock_user_service)
        
    def test_is_authenticated(self):
        # Test when not authenticated
        self.assertFalse(self.auth_manager.is_authenticated())
        
        # Test when authenticated
        st.session_state.email = "test@example.com"
        self.assertTrue(self.auth_manager.is_authenticated())
        
    def test_get_current_user(self):
        # Test when not authenticated
        self.assertIsNone(self.auth_manager.get_current_user())
        
        # Test when authenticated
        st.session_state.email = "test@example.com"
        mock_user = {"email": "test@example.com", "name": "Test User"}
        self.mock_user_service.get_user_profile.return_value = mock_user
        self.assertEqual(self.auth_manager.get_current_user(), mock_user)
        
    def test_record_login(self):
        # Test new login
        st.session_state.clear()
        self.mock_user_service.get_user_profile.return_value = {"login_count": 0}
        self.assertTrue(self.auth_manager.record_login("test@example.com"))
        self.mock_user_service.record_login.assert_called_once_with("test@example.com")
        
        # Test existing login
        self.mock_user_service.reset_mock()
        self.assertFalse(self.auth_manager.record_login("test@example.com"))
        self.mock_user_service.record_login.assert_not_called()

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.session_manager = SessionManager()
        
    def test_set_get_session(self):
        # Test setting and getting session value
        self.session_manager.set_session("test_key", "test_value")
        self.assertEqual(self.session_manager.get_session("test_key"), "test_value")
        
    def test_clear_session(self):
        # Test clearing session
        self.session_manager.set_session("test_key", "test_value")
        self.session_manager.clear_session()
        self.assertIsNone(self.session_manager.get_session("test_key"))

class TestAuthDecorators(unittest.TestCase):
    def test_require_authentication(self):
        # Test when not authenticated
        @require_authentication
        def test_func():
            return "success"
            
        st.session_state.clear()
        self.assertIsNone(test_func())
        
        # Test when authenticated
        st.session_state.email = "test@example.com"
        self.assertEqual(test_func(), "success")
        
    def test_require_premium(self):
        # Test when not premium
        @require_premium
        def test_func():
            return "success"
            
        st.session_state.clear()
        self.assertIsNone(test_func())
        
        # Test when premium
        st.session_state.is_subscribed = True
        self.assertEqual(test_func(), "success")

class TestAuthComponents(unittest.TestCase):
    def setUp(self):
        self.auth_components = AuthComponents()
        
    @patch('streamlit.form')
    def test_login_form(self, mock_form):
        # Test login form rendering
        self.auth_components.login_form()
        mock_form.assert_called_once_with("login_form")
        
    def test_user_profile(self):
        # Test when not logged in
        st.session_state.clear()
        with patch('streamlit.write') as mock_write:
            self.auth_components.user_profile()
            mock_write.assert_not_called()
            
        # Test when logged in
        st.session_state.email = "test@example.com"
        with patch('streamlit.write') as mock_write:
            self.auth_components.user_profile()
            mock_write.assert_called_once_with("Welcome, test@example.com")
            
    def test_subscription_status(self):
        # Test free account
        st.session_state.clear()
        with patch('streamlit.info') as mock_info:
            self.auth_components.subscription_status()
            mock_info.assert_called_once_with("Free Account")
            
        # Test premium account
        st.session_state.is_subscribed = True
        with patch('streamlit.success') as mock_success:
            self.auth_components.subscription_status()
            mock_success.assert_called_once_with("Premium Subscription Active")

if __name__ == '__main__':
    unittest.main() 
import streamlit as st
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
from config.page_config import configure_page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class StudyLegendApp:
    def __init__(self):
        logger.info("Initializing StudyLegendApp")
        try:
            self.config = self._load_config()
            logger.debug(f"Loaded config: {self.config}")
            self.container = self._initialize_container()
            self._initialize_services()
            self._initialize_components()
            self._initialize_pages()
            logger.info("StudyLegendApp initialized successfully")
        except Exception as e:
            logger.error(f"Error during StudyLegendApp initialization: {str(e)}", exc_info=True)
            raise

    def _load_config(self):
        """Load application configuration"""
        logger.debug("Loading application configuration")
        return {
            "mongodb_uri": os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
            "database_name": os.getenv("DB_NAME", "study_legend"),
            "debug": os.getenv("DEBUG", "False").lower() == "true",
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "max_connections": int(os.getenv("MAX_CONNECTIONS", "100"))
        }

    def _initialize_container(self):
        """Initialize dependency injection container"""
        logger.debug("Initializing dependency injection container")
        try:
            from core.di.container import Container
            container = Container()
            
            # Register repositories
            from data.repositories.question_repository import MongoDBQuestionRepository
            from data.repositories.user_repository import MongoDBUserRepository
            container.register_repository("question", MongoDBQuestionRepository)
            container.register_repository("user", MongoDBUserRepository)
            
            logger.debug("Container initialized successfully")
            return container
        except Exception as e:
            logger.error(f"Error initializing container: {str(e)}", exc_info=True)
            raise

    def _initialize_services(self):
        """Initialize application services"""
        logger.debug("Initializing application services")
        try:
            # Initialize repositories
            self.question_repository = self.container.get_repository("question")
            self.user_repository = self.container.get_repository("user")

            # Initialize services
            from core.services.question_service import QuestionService
            from core.services.user_service import UserService
            from core.services.analytics_service import AnalyticsService
            
            self.question_service = QuestionService(self.question_repository)
            self.user_service = UserService(self.user_repository)
            self.analytics_service = AnalyticsService(self.question_repository, self.user_repository)
            logger.debug("Services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}", exc_info=True)
            raise

    def _initialize_components(self):
        """Initialize UI components"""
        logger.debug("Initializing UI components")
        try:
            from features.content.home.home_content import HomeContent
            from features.content.shared.auth_components import AuthComponents
            
            self.home_content = HomeContent(
                self.user_service,
                self.analytics_service
            )
            self.auth_components = AuthComponents(self.user_service)
            logger.debug("UI components initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing UI components: {str(e)}", exc_info=True)
            raise

    def _home_page(self):
        """Render the home page"""
        try:
            logger.info("Rendering home page")
            self.home_content.render()
        except Exception as e:
            logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
            st.error("Error loading home page")
            if self.config["debug"]:
                st.exception(e)

    def _practice_page(self):
        """Render the practice page"""
        self._execute_feature_page("features/content/practice/practice_ui.py")

    def _add_questions_page(self):
        """Render the add questions page"""
        self._execute_feature_page("features/content/add_questions/add_questions_ui.py")

    def _manage_questions_page(self):
        """Render the manage questions page"""
        self._execute_feature_page("features/content/manage_questions/manage_questions_ui.py")

    def _add_ai_page(self):
        """Render the add with AI page"""
        self._execute_feature_page("features/content/add_ai/add_ai_ui.py")

    def _tutor_page(self):
        """Render the tutor page"""
        self._execute_feature_page("features/content/tutor/tutor_ui.py")

    def _assessments_page(self):
        """Render the assessments page"""
        self._execute_feature_page("features/content/assessments/assessments_ui.py")

    def _account_page(self):
        """Render the account page"""
        self._execute_feature_page("features/content/account/account_ui.py")

    def _settings_page(self):
        """Render the settings page"""
        self._execute_feature_page("features/content/settings/settings_ui.py")

    def _initialize_pages(self):
        """Initialize application pages"""
        logger.debug("Initializing pages")
        try:
            # Create page objects
            self.pages = [
                st.Page(
                    self._home_page,
                    title="Home",
                    icon="🏠",
                    default=True
                ),
                st.Page(
                    self._practice_page,
                    title="Practice",
                    icon="🎯"
                ),
                st.Page(
                    self._add_questions_page,
                    title="Add Questions",
                    icon="🆕"
                ),
                st.Page(
                    self._manage_questions_page,
                    title="Manage Questions",
                    icon="📝"
                ),
                st.Page(
                    self._add_ai_page,
                    title="Add with AI",
                    icon="🤖"
                ),
                st.Page(
                    self._tutor_page,
                    title="Tutor",
                    icon="👨‍🏫"
                ),
                st.Page(
                    self._assessments_page,
                    title="Assessments",
                    icon="📅"
                ),
                st.Page(
                    self._account_page,
                    title="Account",
                    icon="👤"
                ),
                st.Page(
                    self._settings_page,
                    title="Settings",
                    icon="⚙️"
                )
            ]
            
            logger.debug(f"Pages initialized successfully: {[p.title for p in self.pages]}")
        except Exception as e:
            logger.error(f"Error initializing pages: {str(e)}", exc_info=True)
            raise

    def _execute_feature_page(self, page_path: str):
        """Execute a feature page with proper setup and error handling"""
        try:
            logger.info(f"Executing feature page: {page_path}")
            
            # Import the page module
            import importlib.util
            spec = importlib.util.spec_from_file_location("feature_page", page_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Execute the page's render function
            if hasattr(module, "render"):
                module.render()
            else:
                logger.error(f"Page {page_path} does not have a render function")
                st.error("Error: Page not properly configured")
            
            logger.info(f"Feature page execution completed: {page_path}")
        except Exception as e:
            logger.error(f"Error executing feature page {page_path}: {str(e)}", exc_info=True)
            st.error(f"Error loading page: {page_path}")
            if self.config["debug"]:
                st.exception(e)

    def _setup_page(self):
        """Configure Streamlit page settings"""
        logger.debug("Setting up Streamlit page")
        try:
            logger.debug("Page setup completed")
        except Exception as e:
            logger.error(f"Error setting up page: {str(e)}", exc_info=True)
            raise

    def _setup_sidebar(self):
        """Configure and render the sidebar"""
        logger.debug("Setting up sidebar")
        try:
            with st.sidebar:
                # User profile section
                if self.auth_components.is_authenticated():
                    email = st.session_state.get("email")
                    st.markdown(f"### 👤 {email}")
                    
                    # Add subscription status
                    with st.expander("💳 Subscription Status", expanded=True):
                        if st.session_state.get("user_subscribed", False):
                            st.success("✅ Premium subscription active")
                            if st.session_state.get("subscriptions"):
                                try:
                                    subscription = st.session_state.subscriptions.data[0]
                                    if subscription.get("current_period_end"):
                                        end_timestamp = subscription["current_period_end"]
                                        end_date = datetime.fromtimestamp(end_timestamp)
                                        days_remaining = (end_date - datetime.now()).days
                                        st.info(f"⏱️ {days_remaining} days remaining")
                                except Exception as e:
                                    logger.error(f"Error displaying subscription info: {str(e)}")
                            
                            st.markdown("[View account details](/7_👤_Account)", unsafe_allow_html=True)
                        else:
                            st.warning("❌ No active subscription")
                            st.markdown("[View account details](/render_account)", unsafe_allow_html=True)
                else:
                    st.markdown("### 👋 Welcome to Study Legend")
                    st.markdown("Please sign in to access all features")
                    self.auth_components.show_login_prompt()
            
            logger.debug("Sidebar setup completed")
        except Exception as e:
            logger.error(f"Error setting up sidebar: {str(e)}", exc_info=True)
            raise

    def _handle_error(self, error: Exception):
        """Handle application errors"""
        from core.exceptions.business_exceptions import BusinessException
        
        logger.error(f"Handling error: {str(error)}", exc_info=True)
        
        if isinstance(error, BusinessException):
            st.error(error.message)
        else:
            st.error("An unexpected error occurred. Please try again later.")
        
        if self.config["debug"]:
            st.exception(error)

    def _execute_page(self, page):
        """Execute a page with proper error handling"""
        try:
            logger.info(f"Executing page: {page.title}")
            page.run()
            logger.info(f"Page execution completed: {page.title}")
        except Exception as e:
            logger.error(f"Error executing page {page.title}: {str(e)}", exc_info=True)
            st.error(f"Error loading page: {page.title}")
            if self.config["debug"]:
                st.exception(e)

    def run(self):
        """Run the application"""
        logger.info("Starting application")
        try:
            self._setup_page()
            
            # Log session state for debugging
            logger.info(f"Current session state: {dict(st.session_state)}")
            
            # Check authentication
            is_auth = self.auth_components.is_authenticated()
            logger.info(f"Authentication check result: {is_auth}")
            
            if not is_auth:
                logger.info("User not authenticated, showing login prompt")
                self.auth_components.show_login_prompt()
                return
            
            # Log email after authentication
            email = st.session_state.get("email")
            logger.info(f"User email from session: {email}")
            
            # Setup sidebar
            self._setup_sidebar()
            
            # Setup navigation and run selected page
            selected_page = st.navigation(self.pages)
            self._execute_page(selected_page)
            
            logger.info("Application run completed successfully")
            
        except Exception as e:
            logger.error(f"Error running application: {str(e)}", exc_info=True)
            self._handle_error(e)

def main():
    """Application entry point"""
    # Configure the page only when running as main script
    configure_page()
    
    logger.info("Application starting")
    try:
        app = StudyLegendApp()
        app.run()
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
import streamlit as st
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from datetime import datetime
from config.page_config import configure_page

# Configure the page
configure_page()

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

    def _setup_page(self):
        """Configure Streamlit page settings"""
        logger.debug("Setting up Streamlit page")
        try:
            logger.debug("Page setup completed")
        except Exception as e:
            logger.error(f"Error setting up page: {str(e)}", exc_info=True)
            raise

    def _handle_navigation(self):
        """Handle page navigation"""
        logger.debug("Handling navigation")
        try:
            query_params = st.query_params
            current_page = query_params.get("page", ["home"])[0]
            logger.info(f"Navigating to page: {current_page}")
            
            if current_page == "home":
                self.home_content.render()
            elif current_page == "practice":
                from features.content.practice.practice_content import PracticeContent
                PracticeContent(self.question_service).render()
            elif current_page == "profile":
                from features.content.profile.profile_content import ProfileContent
                ProfileContent(self.user_service).render()
            logger.debug("Navigation completed successfully")
        except Exception as e:
            logger.error(f"Error during navigation: {str(e)}", exc_info=True)
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
            
            # Handle navigation and render current page
            self._handle_navigation()
            logger.info("Application run completed successfully")
            
        except Exception as e:
            logger.error(f"Error running application: {str(e)}", exc_info=True)
            self._handle_error(e)

def main():
    """Application entry point"""
    logger.info("Application starting")
    try:
        app = StudyLegendApp()
        app.run()
    except Exception as e:
        logger.critical(f"Critical error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
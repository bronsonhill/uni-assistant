# Home.py Documentation

## Class Diagram

```mermaid
classDiagram
    class StudyLegendApp {
        -config: dict
        -container: Container
        -question_repository: MongoDBQuestionRepository
        -user_repository: MongoDBUserRepository
        -question_service: QuestionService
        -user_service: UserService
        -analytics_service: AnalyticsService
        -home_content: HomeContent
        -auth_components: AuthComponents
        +__init__()
        -_load_config() dict
        -_initialize_container() Container
        -_initialize_services()
        -_initialize_components()
        -_setup_page()
        -_handle_navigation()
        -_handle_error(error: Exception)
        +run()
    }

    class Container {
        +register_repository(name: str, repository: class)
        +get_repository(name: str) Repository
    }

    class QuestionService {
        -question_repository: MongoDBQuestionRepository
    }

    class UserService {
        -user_repository: MongoDBUserRepository
    }

    class AnalyticsService {
        -question_repository: MongoDBQuestionRepository
        -user_repository: MongoDBUserRepository
    }

    class HomeContent {
        -user_service: UserService
        -analytics_service: AnalyticsService
        +render()
    }

    class AuthComponents {
        -user_service: UserService
        +is_authenticated() bool
        +show_login_prompt()
    }

    StudyLegendApp --> Container : uses
    StudyLegendApp --> QuestionService : uses
    StudyLegendApp --> UserService : uses
    StudyLegendApp --> AnalyticsService : uses
    StudyLegendApp --> HomeContent : uses
    StudyLegendApp --> AuthComponents : uses
    QuestionService --> MongoDBQuestionRepository : uses
    UserService --> MongoDBUserRepository : uses
    AnalyticsService --> MongoDBQuestionRepository : uses
    AnalyticsService --> MongoDBUserRepository : uses
    HomeContent --> UserService : uses
    HomeContent --> AnalyticsService : uses
    AuthComponents --> UserService : uses
```

## Application Flow Sequence Diagram

```mermaid
sequenceDiagram
    participant Main
    participant StudyLegendApp
    participant Container
    participant Services
    participant Components
    participant Streamlit

    Main->>StudyLegendApp: Create instance
    StudyLegendApp->>StudyLegendApp: _load_config()
    StudyLegendApp->>Container: _initialize_container()
    StudyLegendApp->>Services: _initialize_services()
    StudyLegendApp->>Components: _initialize_components()
    StudyLegendApp->>StudyLegendApp: _setup_page()
    
    StudyLegendApp->>Components: is_authenticated()
    alt Not Authenticated
        Components->>Streamlit: show_login_prompt()
    else Authenticated
        StudyLegendApp->>StudyLegendApp: _handle_navigation()
        alt Home Page
            StudyLegendApp->>Components: render()
        else Practice Page
            StudyLegendApp->>Components: render()
        else Profile Page
            StudyLegendApp->>Components: render()
        end
    end
```

## Key Components

### StudyLegendApp
The main application class that orchestrates the entire application. It handles:
- Configuration loading
- Dependency injection
- Service initialization
- Component initialization
- Page navigation
- Error handling

### Container
Manages dependency injection and repository registration.

### Services
- **QuestionService**: Handles question-related operations
- **UserService**: Manages user-related operations
- **AnalyticsService**: Handles analytics and reporting

### Components
- **HomeContent**: Renders the home page content
- **AuthComponents**: Manages authentication and user sessions

## Error Handling
The application implements comprehensive error handling with:
- Logging at different levels (INFO, DEBUG, ERROR, CRITICAL)
- Business exception handling
- Debug mode for detailed error information
- Graceful error presentation to users

## Configuration
The application uses environment variables for configuration:
- MongoDB connection URI
- Database name
- Debug mode
- Log level
- Maximum connections

## Navigation
The application supports multiple pages:
- Home
- Practice
- Profile

Navigation is handled through Streamlit query parameters. 
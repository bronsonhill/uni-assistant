# Study Legend Refactoring Tasks

## Executive Summary

The Study Legend codebase has grown organically and now suffers from several architectural issues that impact maintainability, testability, and code organization. The main issues include:

1. **Violation of Single Responsibility Principle**: `Home.py` contains data access, business logic, UI rendering, and utility functions
2. **Tight Coupling**: Direct database calls scattered throughout UI components
3. **Inconsistent Architecture**: Mix of functional and object-oriented patterns
4. **Poor Separation of Concerns**: Business logic mixed with presentation logic
5. **Code Duplication**: Similar patterns repeated across different modules

## Current Architecture Issues

### 1. Home.py Violations
- **Data Access Functions**: `load_data()`, `save_data()`, `add_question()`, `delete_question()`, `update_question()`
- **Business Logic**: `calculate_weighted_score()`, `sanitize_data_vector_store_ids()`
- **UI Rendering**: `render_home_page()`, `display_user_stats()`
- **Utility Functions**: `get_user_email()`, `force_cleanup_vector_store_data()`

### 2. Inconsistent Service Layer
- Only `RAGManager` follows a proper service pattern
- MongoDB operations scattered across multiple files
- No clear business logic layer

### 3. Feature Module Inconsistencies
- Some features have proper separation (`add_ai` has core/ui/demo modules)
- Others mix concerns in single files
- Inconsistent dependency injection patterns

## Proposed Architecture

```
study_legend/
├── core/                           # Core business logic
│   ├── services/                   # Business services
│   │   ├── question_service.py     # Question CRUD operations
│   │   ├── user_service.py         # User management
│   │   ├── assessment_service.py   # Assessment operations
│   │   ├── analytics_service.py    # Score calculations & analytics
│   │   └── file_service.py         # File upload/management
│   ├── models/                     # Data models/DTOs
│   │   ├── question.py
│   │   ├── user.py
│   │   ├── assessment.py
│   │   └── session.py
│   └── exceptions/                 # Custom exceptions
│       └── business_exceptions.py
├── data/                          # Data access layer
│   ├── repositories/              # Repository pattern
│   │   ├── question_repository.py
│   │   ├── user_repository.py
│   │   └── assessment_repository.py
│   └── mongodb/                   # MongoDB implementation (existing)
├── features/                      # Feature modules (existing structure)
│   └── content/
│       ├── shared/                # Shared UI components
│       │   ├── auth_components.py
│       │   ├── question_components.py
│       │   └── navigation_components.py
│       └── [existing feature dirs]
├── utils/                         # Pure utility functions
│   ├── auth_utils.py
│   ├── date_utils.py
│   └── validation_utils.py
└── config/                        # Configuration management
    ├── settings.py
    └── dependencies.py
```

## Refactoring Tasks (Step-by-Step Plan)

### Phase 1: Extract Core Services (High Priority)

#### Task 1.1: Create Question Service
**Estimated Time**: 4-6 hours
**Files to Create**: `core/services/question_service.py`
**Files to Modify**: `Home.py`, feature content files

**Input/Output Specifications**:

1. `add_question(subject: str, week: int, question: str, answer: str, email: str) -> dict`:
   - Input Validation:
     - subject: non-empty string, max 100 chars
     - week: positive integer, 1-52
     - question: non-empty string, max 1000 chars
     - answer: non-empty string, max 2000 chars
     - email: valid email format
   - Returns: dict with question_id and status
   - Error Cases:
     - Invalid input format
     - Duplicate question
     - Database connection error
     - User not found

2. `update_question(subject: str, week: int, idx: int, question: str, answer: str, email: str) -> bool`:
   - Input Validation: Same as add_question
   - Returns: True if successful, False if not found
   - Error Cases:
     - Question not found
     - Unauthorized access
     - Database error

3. `delete_question(subject: str, week: int, idx: int, email: str) -> bool`:
   - Input Validation: Same as add_question
   - Returns: True if deleted, False if not found
   - Error Cases:
     - Question not found
     - Unauthorized access
     - Database error

4. `get_questions_by_subject_week(subject: str, week: int, email: str) -> List[dict]`:
   - Input Validation: Same as add_question
   - Returns: List of question dictionaries
   - Error Cases:
     - Invalid subject/week
     - Database error
     - User not found

5. `get_all_questions(email: str) -> List[dict]`:
   - Input Validation: email only
   - Returns: List of all questions for user
   - Error Cases:
     - Database error
     - User not found

**Implementation Steps**:

1. Create Service Class:
```python
class QuestionService:
    def __init__(self, question_repository, user_repository):
        self.question_repository = question_repository
        self.user_repository = user_repository
```

2. Implement Input Validation:
```python
def _validate_question_input(self, subject, week, question, answer, email):
    if not all([subject, week, question, answer, email]):
        raise ValueError("All fields are required")
    if not isinstance(week, int) or week < 1 or week > 52:
        raise ValueError("Week must be between 1 and 52")
    # Add more validation...
```

3. Implement Error Handling:
```python
class QuestionServiceError(Exception):
    pass

class QuestionNotFoundError(QuestionServiceError):
    pass

class UnauthorizedAccessError(QuestionServiceError):
    pass
```

4. Add Logging:
```python
import logging

logger = logging.getLogger(__name__)

def add_question(self, subject, week, question, answer, email):
    try:
        logger.info(f"Adding question for {email} in {subject} week {week}")
        # Implementation
    except Exception as e:
        logger.error(f"Error adding question: {str(e)}")
        raise
```

**Test Cases**:

1. Unit Tests:
```python
def test_add_question_success():
    # Test successful question addition
    pass

def test_add_question_validation():
    # Test input validation
    pass

def test_add_question_duplicate():
    # Test duplicate question handling
    pass

def test_add_question_unauthorized():
    # Test unauthorized access
    pass
```

2. Integration Tests:
```python
def test_question_service_integration():
    # Test full service integration
    pass
```

**Dependencies**:
- Must be completed before Task 1.2 (Analytics Service)
- Requires Task 2.1 (Repository Interfaces) to be completed first
- Can be developed in parallel with Task 1.3 (User Service)

**Success Criteria**:
1. All methods implemented with proper validation
2. 100% test coverage for core functionality
3. All error cases handled and logged
4. Documentation complete with examples
5. Performance metrics met:
   - add_question: < 100ms
   - get_questions: < 50ms
   - update/delete: < 75ms

**Rollback Plan**:
1. Keep old implementation in `Home.py` until new service is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

#### Task 1.2: Create Analytics Service
**Estimated Time**: 3-4 hours
**Files to Create**: `core/services/analytics_service.py`
**Files to Modify**: `Home.py`, practice features

**Input/Output Specifications**:

1. `calculate_weighted_score(scores: List[float], last_practiced: datetime, decay_factor: float, forgetting_decay_factor: float) -> float`:
   - Input Validation:
     - scores: non-empty list of floats between 0 and 1
     - last_practiced: valid datetime object
     - decay_factor: float between 0 and 1
     - forgetting_decay_factor: float between 0 and 1
   - Returns: weighted score between 0 and 1
   - Error Cases:
     - Invalid score values
     - Invalid datetime
     - Invalid decay factors

2. `update_question_score(subject: str, week: int, idx: int, score: float, user_answer: str, email: str) -> dict`:
   - Input Validation:
     - subject: non-empty string, max 100 chars
     - week: positive integer, 1-52
     - idx: non-negative integer
     - score: float between 0 and 1
     - user_answer: non-empty string
     - email: valid email format
   - Returns: dict with updated score and statistics
   - Error Cases:
     - Question not found
     - Invalid score
     - Database error

3. `get_user_statistics(email: str) -> dict`:
   - Input Validation:
     - email: valid email format
   - Returns: dict containing:
     - total_questions: int
     - average_score: float
     - subject_stats: dict
     - weekly_progress: dict
   - Error Cases:
     - User not found
     - Database error

4. `get_subject_statistics(subject: str, email: str) -> dict`:
   - Input Validation:
     - subject: non-empty string
     - email: valid email format
   - Returns: dict containing:
     - total_questions: int
     - average_score: float
     - weekly_scores: dict
     - weak_areas: List[str]
   - Error Cases:
     - Subject not found
     - Database error

**Implementation Steps**:

1. Create Service Class:
```python
class AnalyticsService:
    def __init__(self, question_repository, user_repository):
        self.question_repository = question_repository
        self.user_repository = user_repository
```

2. Implement Score Calculation:
```python
def _calculate_time_decay(self, last_practiced: datetime, decay_factor: float) -> float:
    time_diff = datetime.now() - last_practiced
    days = time_diff.days
    return math.exp(-decay_factor * days)
```

3. Implement Statistics Aggregation:
```python
def _aggregate_subject_stats(self, questions: List[dict]) -> dict:
    return {
        'total': len(questions),
        'average_score': sum(q['score'] for q in questions) / len(questions),
        'weak_areas': self._identify_weak_areas(questions)
    }
```

4. Add Caching Layer:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_user_statistics(self, email: str) -> dict:
    # Implementation
    pass
```

**Test Cases**:

1. Unit Tests:
```python
def test_calculate_weighted_score():
    # Test score calculation with various inputs
    pass

def test_score_decay():
    # Test time-based score decay
    pass

def test_statistics_aggregation():
    # Test statistics calculation
    pass

def test_cache_invalidation():
    # Test cache behavior
    pass
```

2. Integration Tests:
```python
def test_analytics_service_integration():
    # Test full service integration
    pass
```

**Dependencies**:
- Requires Task 1.1 (Question Service) to be completed
- Can be developed in parallel with Task 1.3 (User Service)
- Requires Task 2.1 (Repository Interfaces) to be completed first

**Success Criteria**:
1. All methods implemented with proper validation
2. 100% test coverage for core functionality
3. All error cases handled and logged
4. Documentation complete with examples
5. Performance metrics met:
   - score calculation: < 10ms
   - statistics retrieval: < 100ms
   - cache hit ratio: > 80%

**Rollback Plan**:
1. Keep old implementation in `Home.py` until new service is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

#### Task 1.3: Create User Service
**Estimated Time**: 2-3 hours
**Files to Create**: `core/services/user_service.py`
**Files to Modify**: `users.py`, `auth.py`, feature files

**Input/Output Specifications**:

1. `get_user_profile(email: str) -> dict`:
   - Input Validation:
     - email: valid email format
   - Returns: dict containing:
     - email: str
     - name: str
     - subscription_status: str
     - preferences: dict
     - last_login: datetime
   - Error Cases:
     - User not found
     - Database error

2. `update_user_settings(email: str, settings: dict) -> bool`:
   - Input Validation:
     - email: valid email format
     - settings: dict with valid keys
   - Returns: True if successful
   - Error Cases:
     - Invalid settings
     - User not found
     - Database error

3. `get_subscription_status(email: str) -> dict`:
   - Input Validation:
     - email: valid email format
   - Returns: dict containing:
     - status: str
     - expiry_date: datetime
     - features: List[str]
   - Error Cases:
     - User not found
     - Database error

4. `validate_user_access(email: str, feature: str) -> bool`:
   - Input Validation:
     - email: valid email format
     - feature: valid feature name
   - Returns: True if access granted
   - Error Cases:
     - User not found
     - Invalid feature
     - Database error

**Implementation Steps**:

1. Create Service Class:
```python
class UserService:
    def __init__(self, user_repository, subscription_repository):
        self.user_repository = user_repository
        self.subscription_repository = subscription_repository
```

2. Implement User Validation:
```python
def _validate_user_exists(self, email: str) -> bool:
    user = self.user_repository.find_by_email(email)
    if not user:
        raise UserNotFoundError(f"User {email} not found")
    return True
```

3. Implement Subscription Check:
```python
def _check_subscription(self, email: str) -> dict:
    subscription = self.subscription_repository.get_active_subscription(email)
    if not subscription:
        raise SubscriptionNotFoundError(f"No active subscription for {email}")
    return subscription
```

4. Add Session Management:
```python
def _create_user_session(self, email: str) -> str:
    session_id = str(uuid.uuid4())
    self.user_repository.update_last_login(email)
    return session_id
```

**Test Cases**:

1. Unit Tests:
```python
def test_get_user_profile():
    # Test profile retrieval
    pass

def test_update_settings():
    # Test settings update
    pass

def test_subscription_validation():
    # Test subscription checks
    pass

def test_access_control():
    # Test feature access control
    pass
```

2. Integration Tests:
```python
def test_user_service_integration():
    # Test full service integration
    pass
```

**Dependencies**:
- Can be developed in parallel with Task 1.1 and 1.2
- Requires Task 2.1 (Repository Interfaces) to be completed first

**Success Criteria**:
1. All methods implemented with proper validation
2. 100% test coverage for core functionality
3. All error cases handled and logged
4. Documentation complete with examples
5. Performance metrics met:
   - profile retrieval: < 50ms
   - settings update: < 100ms
   - access validation: < 20ms

**Rollback Plan**:
1. Keep old implementation in `users.py` until new service is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

### Phase 2: Implement Repository Pattern (Medium Priority)

#### Task 2.1: Create Data Repository Interfaces
**Estimated Time**: 2-3 hours
**Files to Create**: `data/repositories/base_repository.py`, `data/repositories/question_repository.py`

**Input/Output Specifications**:

1. Base Repository Interface:
```python
class BaseRepository(ABC):
    @abstractmethod
    def find_by_id(self, id: str) -> Optional[dict]:
        pass

    @abstractmethod
    def find_all(self, filters: dict = None) -> List[dict]:
        pass

    @abstractmethod
    def create(self, data: dict) -> str:
        pass

    @abstractmethod
    def update(self, id: str, data: dict) -> bool:
        pass

    @abstractmethod
    def delete(self, id: str) -> bool:
        pass
```

2. Question Repository Interface:
```python
class QuestionRepository(BaseRepository):
    @abstractmethod
    def find_by_subject_week(self, subject: str, week: int) -> List[dict]:
        pass

    @abstractmethod
    def find_by_user(self, email: str) -> List[dict]:
        pass

    @abstractmethod
    def update_score(self, id: str, score: float) -> bool:
        pass
```

**Implementation Steps**:

1. Create Base Repository:
```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict

class BaseRepository(ABC):
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def _validate_id(self, id: str) -> bool:
        if not id or not isinstance(id, str):
            raise ValueError("Invalid ID format")
        return True
```

2. Create Question Repository:
```python
class QuestionRepository(BaseRepository):
    def __init__(self):
        super().__init__("questions")

    def _validate_question(self, question: dict) -> bool:
        required_fields = ["subject", "week", "question", "answer"]
        if not all(field in question for field in required_fields):
            raise ValueError("Missing required fields")
        return True
```

3. Implement MongoDB Repository:
```python
class MongoDBQuestionRepository(QuestionRepository):
    def __init__(self, db_client):
        super().__init__()
        self.db = db_client[self.collection_name]

    def find_by_id(self, id: str) -> Optional[dict]:
        return self.db.find_one({"_id": ObjectId(id)})
```

**Test Cases**:

1. Unit Tests:
```python
def test_base_repository_validation():
    # Test ID validation
    pass

def test_question_repository_validation():
    # Test question validation
    pass

def test_mongodb_repository_operations():
    # Test CRUD operations
    pass
```

2. Integration Tests:
```python
def test_repository_integration():
    # Test full repository integration
    pass
```

**Dependencies**:
- Must be completed before Task 1.1, 1.2, and 1.3
- Requires MongoDB connection setup

**Success Criteria**:
1. All interfaces properly defined
2. 100% test coverage for core functionality
3. All error cases handled
4. Documentation complete with examples
5. Performance metrics met:
   - find operations: < 50ms
   - write operations: < 100ms

**Rollback Plan**:
1. Keep old implementation until new repositories are verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

#### Task 2.2: Refactor MongoDB Integration
**Estimated Time**: 4-5 hours
**Files to Modify**: All files in `mongodb/` directory

**Input/Output Specifications**:

1. Connection Management:
```python
class MongoDBConnection:
    def __init__(self, connection_string: str, max_pool_size: int = 100):
        self.connection_string = connection_string
        self.max_pool_size = max_pool_size
        self._client = None

    def connect(self) -> None:
        # Implementation
        pass

    def disconnect(self) -> None:
        # Implementation
        pass
```

2. Transaction Support:
```python
class MongoDBTransaction:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        self.session.start_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.session.commit_transaction()
        else:
            self.session.abort_transaction()
```

**Implementation Steps**:

1. Implement Connection Pooling:
```python
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class MongoDBConnectionManager:
    _instance = None
    _client = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_client(self) -> MongoClient:
        if self._client is None:
            self._client = MongoClient(
                self.connection_string,
                maxPoolSize=self.max_pool_size
            )
        return self._client
```

2. Implement Error Handling:
```python
class MongoDBError(Exception):
    pass

class ConnectionError(MongoDBError):
    pass

class QueryError(MongoDBError):
    pass

def handle_mongodb_operation(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ConnectionFailure as e:
            raise ConnectionError(f"Failed to connect to MongoDB: {str(e)}")
        except Exception as e:
            raise QueryError(f"Query failed: {str(e)}")
    return wrapper
```

3. Implement Retry Logic:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def execute_with_retry(operation):
    return operation()
```

**Test Cases**:

1. Unit Tests:
```python
def test_connection_pooling():
    # Test connection pool behavior
    pass

def test_transaction_handling():
    # Test transaction support
    pass

def test_error_handling():
    # Test error scenarios
    pass

def test_retry_logic():
    # Test retry mechanism
    pass
```

2. Integration Tests:
```python
def test_mongodb_integration():
    # Test full MongoDB integration
    pass
```

**Dependencies**:
- Requires Task 2.1 to be completed
- Requires MongoDB server access

**Success Criteria**:
1. Connection pooling implemented
2. Transaction support working
3. Error handling comprehensive
4. Retry logic implemented
5. Performance metrics met:
   - connection time: < 100ms
   - query time: < 50ms
   - transaction time: < 200ms

**Rollback Plan**:
1. Keep old implementation until new integration is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

### Phase 3: Extract Shared UI Components (Medium Priority)

#### Task 3.1: Create Shared Authentication Components
**Estimated Time**: 3-4 hours
**Files to Create**: `features/content/shared/auth_components.py`
**Files to Modify**: All feature content files

**Input/Output Specifications**:

1. Authentication Decorator:
```python
def require_authentication(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            return show_login_prompt()
        return func(*args, **kwargs)
    return wrapper
```

2. Premium Access Check:
```python
def require_premium(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not has_premium_access():
            return show_upgrade_prompt()
        return func(*args, **kwargs)
    return wrapper
```

3. Login Prompt Component:
```python
def show_login_prompt() -> None:
    st.warning("Please log in to access this feature")
    if st.button("Login"):
        redirect_to_login()
```

4. Upgrade Prompt Component:
```python
def show_upgrade_prompt() -> None:
    st.info("This feature requires a premium subscription")
    if st.button("Upgrade Now"):
        redirect_to_upgrade()
```

**Implementation Steps**:

1. Create Authentication Manager:
```python
class AuthenticationManager:
    def __init__(self, user_service):
        self.user_service = user_service
        self._current_user = None

    def is_authenticated(self) -> bool:
        return self._current_user is not None

    def get_current_user(self) -> Optional[dict]:
        return self._current_user
```

2. Implement Session Management:
```python
class SessionManager:
    def __init__(self):
        self._session = {}

    def set_session(self, key: str, value: Any) -> None:
        self._session[key] = value

    def get_session(self, key: str) -> Any:
        return self._session.get(key)
```

3. Create Authentication Components:
```python
class AuthComponents:
    @staticmethod
    def login_form() -> None:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                handle_login(email, password)

    @staticmethod
    def user_profile() -> None:
        user = get_current_user()
        if user:
            st.write(f"Welcome, {user['name']}")
            if st.button("Logout"):
                handle_logout()
```

**Test Cases**:

1. Unit Tests:
```python
def test_authentication_decorator():
    # Test authentication requirement
    pass

def test_premium_access_check():
    # Test premium access validation
    pass

def test_session_management():
    # Test session handling
    pass
```

2. Integration Tests:
```python
def test_auth_components_integration():
    # Test full authentication flow
    pass
```

**Dependencies**:
- Requires Task 1.3 (User Service) to be completed
- Requires Task 2.1 (Repository Interfaces) to be completed

**Success Criteria**:
1. All components implemented
2. 100% test coverage
3. All error cases handled
4. Documentation complete
5. Performance metrics met:
   - authentication check: < 10ms
   - session management: < 5ms

**Rollback Plan**:
1. Keep old implementation until new components are verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

#### Task 3.2: Create Shared Question Components
**Estimated Time**: 4-5 hours
**Files to Create**: `features/content/shared/question_components.py`

**Input/Output Specifications**:

1. Question Card Component:
```python
class QuestionCard:
    def __init__(self, question: dict):
        self.question = question

    def render(self) -> None:
        st.write(f"Question: {self.question['question']}")
        if st.button("Show Answer"):
            st.write(f"Answer: {self.question['answer']}")
```

2. Question Editor Component:
```python
class QuestionEditor:
    def __init__(self, question: Optional[dict] = None):
        self.question = question or {}

    def render(self) -> dict:
        with st.form("question_editor"):
            question = st.text_area("Question", self.question.get("question", ""))
            answer = st.text_area("Answer", self.question.get("answer", ""))
            if st.form_submit_button("Save"):
                return {"question": question, "answer": answer}
        return None
```

3. Question List Component:
```python
class QuestionList:
    def __init__(self, questions: List[dict]):
        self.questions = questions

    def render(self) -> None:
        for idx, question in enumerate(self.questions):
            with st.expander(f"Question {idx + 1}"):
                QuestionCard(question).render()
```

4. Score Display Component:
```python
class ScoreDisplay:
    def __init__(self, score: float):
        self.score = score

    def render(self) -> None:
        st.metric("Score", f"{self.score:.2%}")
```

**Implementation Steps**:

1. Create Base Component:
```python
class BaseComponent:
    def __init__(self):
        self._state = {}

    def set_state(self, key: str, value: Any) -> None:
        self._state[key] = value

    def get_state(self, key: str) -> Any:
        return self._state.get(key)
```

2. Implement Question Components:
```python
class QuestionComponents:
    @staticmethod
    def create_question_form() -> None:
        with st.form("create_question"):
            subject = st.selectbox("Subject", get_subjects())
            week = st.number_input("Week", 1, 52)
            question = st.text_area("Question")
            answer = st.text_area("Answer")
            if st.form_submit_button("Create"):
                handle_create_question(subject, week, question, answer)

    @staticmethod
    def edit_question_form(question: dict) -> None:
        with st.form("edit_question"):
            question_text = st.text_area("Question", question["question"])
            answer = st.text_area("Answer", question["answer"])
            if st.form_submit_button("Update"):
                handle_update_question(question["id"], question_text, answer)
```

3. Add State Management:
```python
class QuestionState:
    def __init__(self):
        self._questions = []
        self._current_question = None

    def set_questions(self, questions: List[dict]) -> None:
        self._questions = questions

    def get_questions(self) -> List[dict]:
        return self._questions
```

**Test Cases**:

1. Unit Tests:
```python
def test_question_card():
    # Test question card rendering
    pass

def test_question_editor():
    # Test question editing
    pass

def test_question_list():
    # Test question list display
    pass

def test_score_display():
    # Test score display
    pass
```

2. Integration Tests:
```python
def test_question_components_integration():
    # Test full question management flow
    pass
```

**Dependencies**:
- Requires Task 1.1 (Question Service) to be completed
- Requires Task 3.1 (Auth Components) to be completed

**Success Criteria**:
1. All components implemented
2. 100% test coverage
3. All error cases handled
4. Documentation complete
5. Performance metrics met:
   - component rendering: < 50ms
   - state updates: < 10ms

**Rollback Plan**:
1. Keep old implementation until new components are verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

### Phase 4: Improve Configuration and Dependencies (Low Priority)

#### Task 4.1: Create Configuration Management
**Estimated Time**: 2-3 hours
**Files to Create**: `config/settings.py`, `config/dependencies.py`

**Input/Output Specifications**:

1. Settings Configuration:
```python
class Settings:
    def __init__(self):
        self.mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.database_name: str = os.getenv("DB_NAME", "study_legend")
        self.debug: bool = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.max_connections: int = int(os.getenv("MAX_CONNECTIONS", "100"))
```

2. Environment Configuration:
```python
class EnvironmentConfig:
    def __init__(self, env: str = "development"):
        self.env = env
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        if self.env == "production":
            return self._load_production_settings()
        return self._load_development_settings()
```

3. Dependency Container:
```python
class Container:
    def __init__(self):
        self._services = {}
        self._repositories = {}

    def register_service(self, name: str, service: Any) -> None:
        self._services[name] = service

    def get_service(self, name: str) -> Any:
        return self._services.get(name)
```

**Implementation Steps**:

1. Create Settings Manager:
```python
class SettingsManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.settings = Settings()
        self._validate_settings()

    def _validate_settings(self) -> None:
        if not self.settings.mongodb_uri:
            raise ValueError("MongoDB URI is required")
```

2. Implement Configuration Loading:
```python
class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_env_vars() -> None:
        load_dotenv()
```

3. Create Dependency Injection:
```python
class DependencyInjector:
    def __init__(self, container: Container):
        self.container = container

    def inject(self, target: Any) -> Any:
        for name, service in self.container._services.items():
            if hasattr(target, name):
                setattr(target, name, service)
        return target
```

**Test Cases**:

1. Unit Tests:
```python
def test_settings_validation():
    # Test settings validation
    pass

def test_config_loading():
    # Test configuration loading
    pass

def test_dependency_injection():
    # Test dependency injection
    pass
```

2. Integration Tests:
```python
def test_configuration_integration():
    # Test full configuration system
    pass
```

**Dependencies**:
- No specific dependencies, can be implemented in parallel

**Success Criteria**:
1. All configuration options implemented
2. 100% test coverage
3. All error cases handled
4. Documentation complete
5. Performance metrics met:
   - config loading: < 100ms
   - dependency injection: < 10ms

**Rollback Plan**:
1. Keep old configuration until new system is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

#### Task 4.2: Add Comprehensive Error Handling
**Estimated Time**: 3-4 hours
**Files to Create**: `core/exceptions/business_exceptions.py`

**Input/Output Specifications**:

1. Base Exception Hierarchy:
```python
class BusinessException(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(BusinessException):
    pass

class AuthenticationError(BusinessException):
    pass

class AuthorizationError(BusinessException):
    pass

class ResourceNotFoundError(BusinessException):
    pass
```

2. Error Handler:
```python
class ErrorHandler:
    def __init__(self):
        self._handlers = {}

    def register_handler(self, exception_type: Type[Exception], handler: Callable) -> None:
        self._handlers[exception_type] = handler

    def handle(self, exception: Exception) -> None:
        handler = self._handlers.get(type(exception))
        if handler:
            handler(exception)
        else:
            self._default_handler(exception)
```

3. Error Logger:
```python
class ErrorLogger:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_error(self, error: Exception, context: dict = None) -> None:
        self.logger.error(
            f"Error: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "error_code": getattr(error, "code", None),
                "context": context or {}
            }
        )
```

**Implementation Steps**:

1. Create Exception Classes:
```python
class DatabaseError(BusinessException):
    def __init__(self, message: str, operation: str):
        super().__init__(message, f"DB_{operation}")
        self.operation = operation

class ServiceError(BusinessException):
    def __init__(self, message: str, service: str):
        super().__init__(message, f"SVC_{service}")
        self.service = service
```

2. Implement Error Handling:
```python
def handle_business_exception(error: BusinessException) -> None:
    if isinstance(error, ValidationError):
        st.error(f"Validation Error: {error.message}")
    elif isinstance(error, AuthenticationError):
        st.error("Authentication Error: Please log in")
    elif isinstance(error, AuthorizationError):
        st.error("Authorization Error: Insufficient permissions")
    else:
        st.error(f"An error occurred: {error.message}")
```

3. Add Error Logging:
```python
def setup_error_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('error.log'),
            logging.StreamHandler()
        ]
    )
```

**Test Cases**:

1. Unit Tests:
```python
def test_exception_hierarchy():
    # Test exception inheritance
    pass

def test_error_handling():
    # Test error handler
    pass

def test_error_logging():
    # Test error logging
    pass
```

2. Integration Tests:
```python
def test_error_handling_integration():
    # Test full error handling system
    pass
```

**Dependencies**:
- Requires Task 4.1 to be completed
- Can be implemented in parallel with other tasks

**Success Criteria**:
1. All exception types implemented
2. 100% test coverage
3. All error cases handled
4. Documentation complete
5. Performance metrics met:
   - error handling: < 5ms
   - error logging: < 10ms

**Rollback Plan**:
1. Keep old error handling until new system is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

### Phase 5: Refactor Home.py (High Priority)

#### Task 5.1: Extract Home Page Logic
**Estimated Time**: 3-4 hours
**Files to Modify**: `Home.py`
**Files to Create**: `features/content/home/home_content.py`

**Input/Output Specifications**:

1. Home Page Content:
```python
class HomeContent:
    def __init__(self, user_service, analytics_service):
        self.user_service = user_service
        self.analytics_service = analytics_service

    def render(self) -> None:
        self._render_header()
        self._render_user_stats()
        self._render_quick_actions()
        self._render_recent_activity()
```

2. User Statistics Display:
```python
class UserStatsDisplay:
    def __init__(self, analytics_service):
        self.analytics_service = analytics_service

    def render(self, email: str) -> None:
        stats = self.analytics_service.get_user_statistics(email)
        self._render_overview(stats)
        self._render_subject_stats(stats)
        self._render_progress_chart(stats)
```

3. Quick Actions Menu:
```python
class QuickActions:
    def render(self) -> None:
        st.subheader("Quick Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Add Question"):
                self._handle_add_question()
        with col2:
            if st.button("Start Practice"):
                self._handle_start_practice()
        with col3:
            if st.button("View Progress"):
                self._handle_view_progress()
```

**Implementation Steps**:

1. Create Home Content Manager:
```python
class HomeContentManager:
    def __init__(self):
        self.user_service = get_user_service()
        self.analytics_service = get_analytics_service()
        self.content = HomeContent(
            self.user_service,
            self.analytics_service
        )

    def render_page(self) -> None:
        try:
            self.content.render()
        except Exception as e:
            handle_error(e)
```

2. Implement Navigation:
```python
class NavigationManager:
    def __init__(self):
        self._current_page = "home"

    def navigate_to(self, page: str) -> None:
        self._current_page = page
        st.experimental_set_query_params(page=page)

    def get_current_page(self) -> str:
        return self._current_page
```

3. Add State Management:
```python
class HomeState:
    def __init__(self):
        self._user = None
        self._stats = None
        self._recent_activity = []

    def set_user(self, user: dict) -> None:
        self._user = user

    def set_stats(self, stats: dict) -> None:
        self._stats = stats

    def add_activity(self, activity: dict) -> None:
        self._recent_activity.append(activity)
```

**Test Cases**:

1. Unit Tests:
```python
def test_home_content_rendering():
    # Test home page rendering
    pass

def test_user_stats_display():
    # Test stats display
    pass

def test_quick_actions():
    # Test quick actions
    pass
```

2. Integration Tests:
```python
def test_home_page_integration():
    # Test full home page functionality
    pass
```

**Dependencies**:
- Requires Task 1.1 (Question Service) to be completed
- Requires Task 1.2 (Analytics Service) to be completed
- Requires Task 1.3 (User Service) to be completed

**Success Criteria**:
1. All components extracted
2. 100% test coverage
3. All error cases handled
4. Documentation complete
5. Performance metrics met:
   - page load: < 200ms
   - stats rendering: < 100ms
   - navigation: < 50ms

**Rollback Plan**:
1. Keep old implementation until new system is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

#### Task 5.2: Clean Up Main Application File
**Estimated Time**: 2-3 hours
**Files to Modify**: `Home.py`

**Input/Output Specifications**:

1. Main Application Class:
```python
class StudyLegendApp:
    def __init__(self):
        self.config = SettingsManager.get_instance()
        self.container = Container()
        self._initialize_services()
        self._initialize_components()

    def run(self) -> None:
        self._setup_page()
        self._handle_navigation()
        self._render_current_page()
```

2. Service Initialization:
```python
class ServiceInitializer:
    def __init__(self, container: Container):
        self.container = container

    def initialize(self) -> None:
        self._initialize_repositories()
        self._initialize_services()
        self._initialize_components()
```

3. Page Configuration:
```python
class PageConfigurator:
    def configure(self) -> None:
        st.set_page_config(
            page_title="Study Legend",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="expanded"
        )
```

**Implementation Steps**:

1. Create Main Application:
```python
def main():
    app = StudyLegendApp()
    try:
        app.run()
    except Exception as e:
        handle_error(e)
        st.error("An error occurred. Please try again later.")

if __name__ == "__main__":
    main()
```

2. Implement Service Initialization:
```python
def _initialize_services(self) -> None:
    # Initialize repositories
    self.question_repository = MongoDBQuestionRepository(self.db)
    self.user_repository = MongoDBUserRepository(self.db)

    # Initialize services
    self.question_service = QuestionService(self.question_repository)
    self.user_service = UserService(self.user_repository)
    self.analytics_service = AnalyticsService(self.question_repository)
```

3. Add Error Handling:
```python
def _handle_error(self, error: Exception) -> None:
    logger.error(f"Application error: {str(error)}")
    if isinstance(error, BusinessException):
        st.error(error.message)
    else:
        st.error("An unexpected error occurred")
```

**Test Cases**:

1. Unit Tests:
```python
def test_app_initialization():
    # Test app initialization
    pass

def test_service_initialization():
    # Test service setup
    pass

def test_page_configuration():
    # Test page setup
    pass
```

2. Integration Tests:
```python
def test_main_application():
    # Test full application flow
    pass
```

**Dependencies**:
- Requires Task 5.1 to be completed
- Requires all Phase 1 tasks to be completed
- Requires Task 4.1 to be completed

**Success Criteria**:
1. Clean main application file
2. 100% test coverage
3. All error cases handled
4. Documentation complete
5. Performance metrics met:
   - app initialization: < 500ms
   - page rendering: < 100ms
   - service initialization: < 200ms

**Rollback Plan**:
1. Keep old implementation until new system is verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

### Phase 6: Testing and Documentation (Medium Priority)

#### Task 6.1: Add Unit Tests
**Estimated Time**: 8-10 hours
**Files to Create**: `tests/` directory structure

**Input/Output Specifications**:

1. Test Configuration:
```python
class TestConfig:
    def __init__(self):
        self.test_db_uri = "mongodb://localhost:27017/test_db"
        self.test_user = {
            "email": "test@example.com",
            "name": "Test User"
        }
        self.test_question = {
            "subject": "Test Subject",
            "week": 1,
            "question": "Test Question",
            "answer": "Test Answer"
        }
```

2. Test Base Classes:
```python
class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = TestConfig()
        cls.db = connect_test_db()

    @classmethod
    def tearDownClass(cls):
        cls.db.drop_database("test_db")
```

3. Mock Services:
```python
class MockQuestionService:
    def __init__(self):
        self.questions = []

    def add_question(self, question: dict) -> str:
        question_id = str(len(self.questions))
        self.questions.append(question)
        return question_id
```

**Implementation Steps**:

1. Create Test Structure:
```python
# tests/
# ├── unit/
# │   ├── services/
# │   ├── repositories/
# │   └── components/
# ├── integration/
# │   ├── api/
# │   └── ui/
# └── conftest.py
```

2. Implement Service Tests:
```python
class TestQuestionService(BaseTestCase):
    def setUp(self):
        self.service = QuestionService(self.db)

    def test_add_question(self):
        question_id = self.service.add_question(self.config.test_question)
        self.assertIsNotNone(question_id)
        question = self.service.get_question(question_id)
        self.assertEqual(question["question"], self.config.test_question["question"])
```

3. Implement Repository Tests:
```python
class TestQuestionRepository(BaseTestCase):
    def setUp(self):
        self.repository = MongoDBQuestionRepository(self.db)

    def test_find_by_subject_week(self):
        self.repository.create(self.config.test_question)
        questions = self.repository.find_by_subject_week(
            self.config.test_question["subject"],
            self.config.test_question["week"]
        )
        self.assertEqual(len(questions), 1)
```

4. Implement Component Tests:
```python
class TestQuestionCard(BaseTestCase):
    def setUp(self):
        self.component = QuestionCard(self.config.test_question)

    def test_render(self):
        with patch('streamlit.write') as mock_write:
            self.component.render()
            mock_write.assert_called_with(
                f"Question: {self.config.test_question['question']}"
            )
```

**Test Cases**:

1. Service Tests:
```python
def test_question_service_crud():
    # Test CRUD operations
    pass

def test_analytics_service_calculations():
    # Test analytics calculations
    pass

def test_user_service_operations():
    # Test user operations
    pass
```

2. Repository Tests:
```python
def test_repository_operations():
    # Test repository operations
    pass

def test_repository_validation():
    # Test data validation
    pass
```

3. Component Tests:
```python
def test_component_rendering():
    # Test UI components
    pass

def test_component_interactions():
    # Test user interactions
    pass
```

**Dependencies**:
- Requires all previous phases to be completed
- Requires test database setup

**Success Criteria**:
1. All components tested
2. 100% test coverage
3. All edge cases covered
4. Documentation complete
5. Performance metrics met:
   - test execution: < 30s
   - test setup: < 5s

**Rollback Plan**:
1. Keep old tests until new tests are verified
2. Use feature flag to toggle between implementations
3. Maintain backup of original code in separate branch

#### Task 6.2: Update Documentation
**Estimated Time**: 3-4 hours
**Files to Modify**: `README.md`, create architecture docs

**Input/Output Specifications**:

1. Main Documentation Structure:
```markdown
# Study Legend Documentation

## Architecture
- System Overview
- Component Diagram
- Data Flow
- Security Model

## Development
- Setup Guide
- Development Workflow
- Testing Strategy
- Deployment Process

## API Reference
- Service APIs
- Repository Interfaces
- Component APIs
- Error Handling

## User Guide
- Installation
- Configuration
- Usage Examples
- Troubleshooting
```

2. Architecture Documentation:
```markdown
# Architecture Documentation

## System Components
- Core Services
- Data Layer
- UI Components
- Configuration

## Design Patterns
- Repository Pattern
- Service Layer
- Dependency Injection
- Error Handling

## Security
- Authentication
- Authorization
- Data Protection
- Error Handling
```

3. API Documentation:
```python
def generate_api_docs():
    """Generate API documentation for all services and components."""
    docs = {
        "services": generate_service_docs(),
        "repositories": generate_repository_docs(),
        "components": generate_component_docs()
    }
    return docs
```

**Implementation Steps**:

1. Create Documentation Structure:
```python
class DocumentationGenerator:
    def __init__(self):
        self.template_loader = jinja2.FileSystemLoader("templates")
        self.template_env = jinja2.Environment(loader=self.template_loader)

    def generate_docs(self):
        self._generate_architecture_docs()
        self._generate_api_docs()
        self._generate_user_guide()
```

2. Implement API Documentation:
```python
def generate_service_docs(service_class):
    """Generate documentation for a service class."""
    docs = {
        "name": service_class.__name__,
        "methods": [],
        "dependencies": []
    }
    for method in inspect.getmembers(service_class, predicate=inspect.isfunction):
        docs["methods"].append({
            "name": method[0],
            "signature": str(inspect.signature(method[1])),
            "docstring": method[1].__doc__
        })
    return docs
```

3. Create User Guide:
```python
def generate_user_guide():
    """Generate user guide with examples."""
    guide = {
        "installation": generate_installation_guide(),
        "configuration": generate_configuration_guide(),
        "usage": generate_usage_examples(),
        "troubleshooting": generate_troubleshooting_guide()
    }
    return guide
```

**Test Cases**:

1. Documentation Tests:
```python
def test_documentation_generation():
    # Test doc generation
    pass

def test_api_documentation():
    # Test API docs
    pass

def test_user_guide():
    # Test user guide
    pass
```

2. Integration Tests:
```python
def test_documentation_integration():
    # Test full documentation system
    pass
```

**Dependencies**:
- Requires all previous phases to be completed
- Requires documentation tools setup

**Success Criteria**:
1. All components documented
2. Documentation complete and accurate
3. Examples provided
4. Documentation tested
5. Performance metrics met:
   - doc generation: < 30s
   - doc rendering: < 5s

**Rollback Plan**:
1. Keep old documentation until new docs are verified
2. Use version control for documentation
3. Maintain backup of original docs in separate branch

## Implementation Priority

### Immediate (Week 1-2)
1. Task 1.1: Create Question Service
2. Task 1.2: Create Analytics Service
3. Task 5.1: Extract Home Page Logic

### Short Term (Week 3-4)
1. Task 1.3: Create User Service
2. Task 3.1: Create Shared Authentication Components
3. Task 5.2: Clean Up Main Application File

### Medium Term (Month 2)
1. Task 2.1: Create Data Repository Interfaces
2. Task 2.2: Refactor MongoDB Integration
3. Task 3.2: Create Shared Question Components

### Long Term (Month 3+)
1. Task 4.1: Create Configuration Management
2. Task 4.2: Add Comprehensive Error Handling
3. Task 6.1: Add Unit Tests
4. Task 6.2: Update Documentation

## Success Metrics

1. **Reduced Code Duplication**: Target 40% reduction in duplicate code
2. **Improved Test Coverage**: Target 80% coverage for business logic
3. **Better Separation of Concerns**: No data access in UI components
4. **Consistent Architecture**: All features follow same patterns
5. **Improved Maintainability**: Easier to add new features and fix bugs

## Risk Mitigation

1. **Incremental Refactoring**: Implement changes gradually to avoid breaking existing functionality
2. **Feature Flags**: Use feature flags for major changes
3. **Comprehensive Testing**: Test each change thoroughly before moving to next task
4. **Backup Strategy**: Maintain working branches for rollback if needed
5. **Documentation**: Document all changes for team knowledge transfer

## Conclusion

This refactoring plan addresses the core architectural issues while maintaining the existing functionality. The phased approach ensures minimal disruption to ongoing development while systematically improving the codebase quality and maintainability.
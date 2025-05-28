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

**Steps**:
1. Create `QuestionService` class with methods:
   - `add_question(subject, week, question, answer, email)`
   - `update_question(subject, week, idx, question, answer, email)`
   - `delete_question(subject, week, idx, email)`
   - `get_questions_by_subject_week(subject, week, email)`
   - `get_all_questions(email)`

2. Move business logic from `Home.py` functions to service
3. Update all feature modules to use `QuestionService`
4. Add proper error handling and validation

**Benefits**: Centralizes question management, improves testability

#### Task 1.2: Create Analytics Service
**Estimated Time**: 3-4 hours
**Files to Create**: `core/services/analytics_service.py`
**Files to Modify**: `Home.py`, practice features

**Steps**:
1. Create `AnalyticsService` class with methods:
   - `calculate_weighted_score(scores, last_practiced, decay_factor, forgetting_decay_factor)`
   - `update_question_score(subject, week, idx, score, user_answer, email)`
   - `get_user_statistics(email)`
   - `get_subject_statistics(subject, email)`

2. Move scoring logic from `Home.py` and `mongodb/queue_cards.py`
3. Add comprehensive analytics calculations
4. Update practice features to use service

**Benefits**: Centralizes scoring logic, enables advanced analytics

#### Task 1.3: Create User Service
**Estimated Time**: 2-3 hours
**Files to Create**: `core/services/user_service.py`
**Files to Modify**: `users.py`, `auth.py`, feature files

**Steps**:
1. Create `UserService` class with methods:
   - `get_user_profile(email)`
   - `update_user_settings(email, settings)`
   - `get_subscription_status(email)`
   - `validate_user_access(email, feature)`

2. Consolidate user-related operations
3. Add proper session management
4. Update authentication flows

**Benefits**: Centralizes user management, improves security

### Phase 2: Implement Repository Pattern (Medium Priority)

#### Task 2.1: Create Data Repository Interfaces
**Estimated Time**: 2-3 hours
**Files to Create**: `data/repositories/base_repository.py`, `data/repositories/question_repository.py`

**Steps**:
1. Define abstract base repository with common CRUD operations
2. Create `QuestionRepository` interface
3. Implement MongoDB-specific repository
4. Add connection pooling and error handling

**Benefits**: Abstracts data access, enables easier testing and database switching

#### Task 2.2: Refactor MongoDB Integration
**Estimated Time**: 4-5 hours
**Files to Modify**: All files in `mongodb/` directory

**Steps**:
1. Implement repository interfaces in MongoDB modules
2. Add proper connection management
3. Implement transaction support where needed
4. Add comprehensive error handling

**Benefits**: Improves data layer reliability and performance

### Phase 3: Extract Shared UI Components (Medium Priority)

#### Task 3.1: Create Shared Authentication Components
**Estimated Time**: 3-4 hours
**Files to Create**: `features/content/shared/auth_components.py`
**Files to Modify**: All feature content files

**Steps**:
1. Extract common authentication checks
2. Create reusable components:
   - `require_authentication()`
   - `require_premium()`
   - `show_upgrade_prompt()`
   - `show_login_prompt()`

2. Update all features to use shared components
3. Standardize authentication flows

**Benefits**: Reduces code duplication, consistent UX

#### Task 3.2: Create Shared Question Components
**Estimated Time**: 4-5 hours
**Files to Create**: `features/content/shared/question_components.py`

**Steps**:
1. Extract common question display logic
2. Create reusable components:
   - `QuestionCard`
   - `QuestionEditor`
   - `QuestionList`
   - `ScoreDisplay`

3. Update features to use shared components
4. Add consistent styling and behavior

**Benefits**: Consistent UI, easier maintenance

### Phase 4: Improve Configuration and Dependencies (Low Priority)

#### Task 4.1: Create Configuration Management
**Estimated Time**: 2-3 hours
**Files to Create**: `config/settings.py`, `config/dependencies.py`

**Steps**:
1. Centralize all configuration settings
2. Create dependency injection container
3. Add environment-specific configurations
4. Update all modules to use centralized config

**Benefits**: Better configuration management, easier deployment

#### Task 4.2: Add Comprehensive Error Handling
**Estimated Time**: 3-4 hours
**Files to Create**: `core/exceptions/business_exceptions.py`

**Steps**:
1. Define custom exception hierarchy
2. Add proper error handling throughout application
3. Create user-friendly error messages
4. Add logging and monitoring

**Benefits**: Better error handling, improved debugging

### Phase 5: Refactor Home.py (High Priority)

#### Task 5.1: Extract Home Page Logic
**Estimated Time**: 3-4 hours
**Files to Modify**: `Home.py`
**Files to Create**: `features/content/home/home_content.py`

**Steps**:
1. Move `render_home_page()` to dedicated home content module
2. Move `display_user_stats()` to analytics service
3. Remove all data access functions (moved to services)
4. Keep only application bootstrap logic in `Home.py`

**Benefits**: Clean separation of concerns, maintainable home page

#### Task 5.2: Clean Up Main Application File
**Estimated Time**: 2-3 hours
**Files to Modify**: `Home.py`

**Steps**:
1. Simplify `main()` function to only handle:
   - Page configuration
   - Authentication setup
   - Navigation setup
   - Service initialization

2. Remove all business logic
3. Add proper error handling for startup
4. Document the application bootstrap process

**Benefits**: Clean application entry point, easier testing

### Phase 6: Testing and Documentation (Medium Priority)

#### Task 6.1: Add Unit Tests
**Estimated Time**: 8-10 hours
**Files to Create**: `tests/` directory structure

**Steps**:
1. Create test structure for services
2. Add unit tests for business logic
3. Add integration tests for repositories
4. Add UI component tests

**Benefits**: Improved reliability, easier refactoring

#### Task 6.2: Update Documentation
**Estimated Time**: 3-4 hours
**Files to Modify**: `README.md`, create architecture docs

**Steps**:
1. Document new architecture
2. Create developer setup guide
3. Add API documentation for services
4. Create contribution guidelines

**Benefits**: Better developer experience, easier onboarding

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
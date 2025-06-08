# Study Legend Service API Documentation

## Question Service

### `add_question(subject: str, week: int, question: str, answer: str, email: str) -> dict`
Adds a new question to the system.

**Parameters:**
- `subject`: Subject name (max 100 chars)
- `week`: Week number (1-52)
- `question`: Question text (max 1000 chars)
- `answer`: Answer text (max 2000 chars)
- `email`: User's email address

**Returns:**
```json
{
    "question_id": "string",
    "status": "success"
}
```

**Errors:**
- `ValidationError`: Invalid input format
- `DuplicateQuestionError`: Question already exists
- `DatabaseError`: Database connection error
- `UserNotFoundError`: User not found

### `update_question(subject: str, week: int, idx: int, question: str, answer: str, email: str) -> bool`
Updates an existing question.

**Parameters:**
- `subject`: Subject name
- `week`: Week number
- `idx`: Question index
- `question`: Updated question text
- `answer`: Updated answer text
- `email`: User's email address

**Returns:**
- `True` if successful
- `False` if question not found

**Errors:**
- `QuestionNotFoundError`: Question not found
- `UnauthorizedAccessError`: User not authorized
- `DatabaseError`: Database error

## Analytics Service

### `calculate_weighted_score(scores: List[float], last_practiced: datetime, decay_factor: float, forgetting_decay_factor: float) -> float`
Calculates weighted score based on practice history.

**Parameters:**
- `scores`: List of previous scores
- `last_practiced`: Last practice timestamp
- `decay_factor`: Time decay factor
- `forgetting_decay_factor`: Forgetting curve factor

**Returns:**
- Weighted score between 0 and 1

**Errors:**
- `ValidationError`: Invalid input values
- `CalculationError`: Error in calculation

### `get_user_statistics(email: str) -> dict`
Retrieves user's study statistics.

**Parameters:**
- `email`: User's email address

**Returns:**
```json
{
    "total_questions": "integer",
    "average_score": "float",
    "subject_stats": {
        "subject_name": {
            "total": "integer",
            "average": "float"
        }
    },
    "weekly_progress": {
        "week_number": {
            "questions": "integer",
            "score": "float"
        }
    }
}
```

**Errors:**
- `UserNotFoundError`: User not found
- `DatabaseError`: Database error

## User Service

### `get_user_profile(email: str) -> dict`
Retrieves user's profile information.

**Parameters:**
- `email`: User's email address

**Returns:**
```json
{
    "email": "string",
    "name": "string",
    "subscription_status": "string",
    "preferences": {
        "key": "value"
    },
    "last_login": "datetime"
}
```

**Errors:**
- `UserNotFoundError`: User not found
- `DatabaseError`: Database error

### `update_user_settings(email: str, settings: dict) -> bool`
Updates user's settings.

**Parameters:**
- `email`: User's email address
- `settings`: Dictionary of settings to update

**Returns:**
- `True` if successful
- `False` if update failed

**Errors:**
- `ValidationError`: Invalid settings
- `UserNotFoundError`: User not found
- `DatabaseError`: Database error

## Error Handling

### Common Error Types

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

### Error Response Format

```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": {
            "field": "string",
            "reason": "string"
        }
    }
}
```

## Rate Limiting

- Maximum 100 requests per minute per user
- Maximum 1000 requests per hour per user
- Maximum 10000 requests per day per user

## Authentication

All API endpoints require authentication using email-based authentication.

### Authentication Header
```
Authorization: Bearer <token>
```

### Token Format
```
<base64-encoded-email>.<timestamp>.<signature>
```

## Best Practices

1. **Error Handling**
   - Always check return values
   - Handle all possible error cases
   - Use appropriate error types

2. **Input Validation**
   - Validate all input parameters
   - Sanitize user input
   - Check data types

3. **Performance**
   - Use appropriate caching
   - Optimize database queries
   - Handle large datasets efficiently

4. **Security**
   - Never expose sensitive data
   - Validate user permissions
   - Use secure communication 
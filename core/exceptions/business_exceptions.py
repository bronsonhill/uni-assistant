class BusinessException(Exception):
    """Base class for all business exceptions."""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class ValidationError(BusinessException):
    """Raised when input validation fails."""
    def __init__(self, message: str):
        super().__init__(message, "VALIDATION_ERROR")

class UserNotFoundError(BusinessException):
    """Raised when a user is not found."""
    pass

class AuthenticationError(BusinessException):
    """Raised when authentication fails."""
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR")

class AuthorizationError(BusinessException):
    """Raised when user lacks required permissions."""
    def __init__(self, message: str):
        super().__init__(message, "AUTHORIZATION_ERROR")

class UnauthorizedAccessError(AuthorizationError):
    """Raised when a user attempts to access a resource they don't have permission for."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(f"Unauthorized access to {resource_type} with ID {resource_id}")
        self.resource_type = resource_type
        self.resource_id = resource_id

class SubscriptionError(BusinessException):
    """Raised when subscription operations fail."""
    pass

class ResourceNotFoundError(BusinessException):
    """Raised when a requested resource is not found"""
    def __init__(self, message: str):
        super().__init__(message, "RESOURCE_NOT_FOUND")

class QuestionNotFoundError(ResourceNotFoundError):
    """Raised when a requested question is not found"""
    def __init__(self, question_id: str):
        super().__init__(f"Question with ID {question_id} not found")
        self.question_id = question_id

class DuplicateQuestionError(ValidationError):
    """Raised when attempting to create a question that already exists."""
    def __init__(self, subject: str, week: int):
        super().__init__(f"Question already exists for subject '{subject}' in week {week}")
        self.subject = subject
        self.week = week

class DatabaseError(BusinessException):
    """Raised when a database operation fails"""
    def __init__(self, message: str, operation: str):
        super().__init__(message, f"DB_{operation}")
        self.operation = operation

class ServiceError(BusinessException):
    """Raised when a service operation fails"""
    def __init__(self, message: str, service: str):
        super().__init__(message, f"SVC_{service}")
        self.service = service 
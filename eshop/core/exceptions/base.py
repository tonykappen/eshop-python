"""Base exception classes."""


class BaseException(Exception):
    """Base exception class for the application."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class BadRequestException(BaseException):
    """Exception for bad request errors (400)."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message)


class NotFoundException(BaseException):
    """Exception for not found errors (404)."""

    def __init__(self, message: str = "Resource not found", name: str = None, key: str = None):
        if name and key:
            message = f'Entity "{name}" ({key}) was not found.'
        super().__init__(message)


class InternalServerException(BaseException):
    """Exception for internal server errors (500)."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message)


class ValidationException(BaseException):
    """Exception for validation errors."""

    def __init__(self, message: str = "Validation error", errors: dict = None):
        self.errors = errors or {}
        super().__init__(message)

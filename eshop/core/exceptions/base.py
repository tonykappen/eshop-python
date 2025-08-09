"""Base exception classes."""


class BaseError(Exception):
    """Base exception class for the application."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class BadRequestException(BaseError):
    """Exception for bad request errors (400)."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(message)


class NotFoundException(BaseError):
    """Exception for not found errors (404)."""

    def __init__(
        self,
        message: str = "Resource not found",
        name: str | None = None,
        key: str | None = None,
    ):
        if name and key:
            message = f'Entity "{name}" ({key}) was not found.'
        super().__init__(message)


class InternalServerException(BaseError):
    """Exception for internal server errors (500)."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message)


class ValidationException(BaseError):
    """Exception for validation errors."""

    def __init__(self, message: str = "Validation error", errors: dict | None = None):
        self.errors = errors or {}
        super().__init__(message)

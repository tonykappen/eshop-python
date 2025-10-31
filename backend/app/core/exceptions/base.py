"""Base exception classes with 1-1 parity to .NET exceptions."""

from typing import Any


class BaseError(Exception):
    """Base exception class for the application - matches .NET Exception pattern."""

    def __init__(self, message: str = "An error occurred", details: str | None = None):
        """Initialize base error with message and optional details."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class BadRequestError(BaseError):
    """Exception for bad request errors (400) - matches .NET BadRequestException."""

    def __init__(self, message: str = "Bad request", details: str | None = None):
        """Initialize bad request error."""
        super().__init__(message, details)


class NotFoundError(BaseError):
    """Exception for not found errors (404) - matches .NET NotFoundException."""

    def __init__(
        self,
        message: str = "Resource not found",
        name: str | None = None,
        key: Any | None = None,
    ):
        """Initialize not found error with optional entity name and key."""
        if name and key:
            message = f'Entity "{name}" ({key}) was not found.'
        super().__init__(message)


class InternalServerError(BaseError):
    """Exception for internal server errors (500) - matches .NET InternalServerException."""

    def __init__(
        self, message: str = "Internal server error", details: str | None = None
    ):
        """Initialize internal server error."""
        super().__init__(message, details)


class ValidationError(BaseError):
    """Exception for validation errors - matches .NET ValidationException."""

    def __init__(
        self,
        message: str = "Validation error",
        errors: dict[str, Any] | None = None,
        details: str | None = None,
    ):
        """Initialize validation error with validation errors dictionary."""
        self.errors = errors or {}
        super().__init__(message, details)


class UnauthorizedError(BaseError):
    """Exception for unauthorized access (401) - matches .NET UnauthorizedAccessException."""

    def __init__(
        self, message: str = "Unauthorized access", details: str | None = None
    ):
        """Initialize unauthorized error."""
        super().__init__(message, details)


class ForbiddenError(BaseError):
    """Exception for forbidden access (403) - matches .NET ForbiddenException."""

    def __init__(self, message: str = "Access forbidden", details: str | None = None):
        """Initialize forbidden error."""
        super().__init__(message, details)


class ConflictError(BaseError):
    """Exception for conflict errors (409) - matches .NET ConflictException."""

    def __init__(self, message: str = "Resource conflict", details: str | None = None):
        """Initialize conflict error."""
        super().__init__(message, details)


class DatabaseError(BaseError):
    """Exception for database-related errors."""

    def __init__(self, message: str = "Database error", details: str | None = None):
        """Initialize database error."""
        super().__init__(message, details)


class ConnectionError(BaseError):
    """Exception for connection-related errors."""

    def __init__(self, message: str = "Connection error", details: str | None = None):
        """Initialize connection error."""
        super().__init__(message, details)


class ConfigurationError(BaseError):
    """Exception for configuration-related errors."""

    def __init__(
        self, message: str = "Configuration error", details: str | None = None
    ):
        """Initialize configuration error."""
        super().__init__(message, details)


class DomainException(BaseError):
    """Exception for domain-related errors - matches .NET DomainException pattern."""

    def __init__(self, message: str = "Domain error", details: str | None = None):
        """Initialize domain error."""
        super().__init__(message, details)

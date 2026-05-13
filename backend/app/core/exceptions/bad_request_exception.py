"""Standardized BadRequest exception - HTTP 400."""

from app.core.exceptions.common_exceptions import BaseError


class BadRequestException(BaseError):
    """Exception for bad request errors (400) - Standardized BadRequest → 400."""

    def __init__(self, message: str = "Bad request", details: str | None = None):
        """
        Initialize bad request exception.

        Args:
            message: Error message
            details: Optional additional details
        """
        super().__init__(message, details)


# Alias for backward compatibility
BadRequestError = BadRequestException

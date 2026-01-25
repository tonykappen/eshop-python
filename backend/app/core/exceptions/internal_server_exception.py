"""Standardized InternalServerError exception - HTTP 500."""

from app.core.exceptions.common_exceptions import BaseError


class InternalServerException(BaseError):
    """Exception for internal server errors (500) - Standardized InternalServerError → 500."""

    def __init__(
        self, message: str = "Internal server error", details: str | None = None
    ):
        """
        Initialize internal server exception.

        Args:
            message: Error message
            details: Optional additional details
        """
        super().__init__(message, details)


# Alias for backward compatibility
InternalServerError = InternalServerException

"""Standardized NotFoundException - HTTP 404."""

from typing import Any

from app.core.exceptions.common_exceptions import BaseError


class NotFoundException(BaseError):
    """Exception for not found errors (404) - Standardized NotFoundException → 404."""

    def __init__(
        self,
        message: str = "Resource not found",
        name: str | None = None,
        key: Any | None = None,
        details: str | None = None,
    ):
        """
        Initialize not found exception with optional entity name and key.
        
        Args:
            message: Error message
            name: Optional entity name (e.g., "Product")
            key: Optional entity key/ID
            details: Optional additional details
        """
        if name and key:
            message = f'Entity "{name}" ({key}) was not found.'
        super().__init__(message, details)


# Alias for backward compatibility
NotFoundError = NotFoundException

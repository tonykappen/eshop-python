"""Domain exceptions for Catalog module with 1-1 parity to .NET."""

from uuid import UUID

from app.core.exceptions.bad_request_exception import BadRequestException
from app.core.exceptions.common_exceptions import BaseError
from app.core.exceptions.internal_server_exception import \
    InternalServerException
from app.core.exceptions.not_found_exception import NotFoundException


class ProductNotFoundError(NotFoundException):
    """Exception raised when a product is not found - matches .NET ProductNotFoundException."""

    def __init__(self, product_id: UUID) -> None:
        """Initialize exception with product ID."""
        self.product_id = product_id
        super().__init__(name="Product", key=product_id)


class ProductValidationError(BadRequestException):
    """Exception for product validation errors - returns 400 Bad Request."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize product validation error."""
        self.field = field
        super().__init__(message=message)


class ProductCreationError(InternalServerException):
    """Exception for product creation errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize product creation error."""
        super().__init__(message=message, details=details)


class ProductUpdateError(InternalServerException):
    """Exception for product update errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize product update error."""
        super().__init__(message=message, details=details)


class ProductDeletionError(InternalServerException):
    """Exception for product deletion errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize product deletion error."""
        super().__init__(message=message, details=details)


class ProductDeleteError(InternalServerException):
    """Exception for product delete errors - matches .NET naming."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message=message, details=details)


class OptimisticLockException(BaseError):
    """Raised when a concurrent modification is detected via version mismatch."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message)

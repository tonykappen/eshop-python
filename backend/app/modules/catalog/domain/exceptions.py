"""Domain exceptions for Catalog module with 1-1 parity to .NET."""

from uuid import UUID

from app.core.exceptions.base import NotFoundError


class ProductNotFoundError(NotFoundError):
    """Exception raised when a product is not found - matches .NET ProductNotFoundException."""

    def __init__(self, product_id: UUID) -> None:
        """Initialize exception with product ID."""
        self.product_id = product_id
        super().__init__(name="Product", key=product_id)


class ProductValidationError(Exception):
    """Exception for product validation errors."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize product validation error."""
        self.message = message
        self.field = field
        super().__init__(self.message)


class ProductCreationError(Exception):
    """Exception for product creation errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize product creation error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class ProductUpdateError(Exception):
    """Exception for product update errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize product update error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class ProductDeletionError(Exception):
    """Exception for product deletion errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize product deletion error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class ProductDeleteError(Exception):
    """Exception for product delete errors - matches .NET naming."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize product delete error."""
        self.message = message
        self.details = details
        super().__init__(self.message)

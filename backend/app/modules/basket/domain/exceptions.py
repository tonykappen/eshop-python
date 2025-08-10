"""Domain exceptions for Basket module with 1-1 parity to .NET."""

from uuid import UUID

from app.core.exceptions.base import NotFoundError


class BasketNotFoundError(NotFoundError):
    """Exception raised when a basket is not found."""

    def __init__(self, basket_id: UUID) -> None:
        """Initialize exception with basket ID."""
        self.basket_id = basket_id
        super().__init__(name="Basket", key=basket_id)


class BasketItemNotFoundError(NotFoundError):
    """Exception raised when a basket item is not found."""

    def __init__(self, item_id: UUID) -> None:
        """Initialize exception with item ID."""
        self.item_id = item_id
        super().__init__(name="BasketItem", key=item_id)


class BasketValidationError(Exception):
    """Exception for basket validation errors."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize basket validation error."""
        self.message = message
        self.field = field
        super().__init__(self.message)


class BasketCreationError(Exception):
    """Exception for basket creation errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize basket creation error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class BasketUpdateError(Exception):
    """Exception for basket update errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize basket update error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class BasketDeletionError(Exception):
    """Exception for basket deletion errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize basket deletion error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class InsufficientStockError(Exception):
    """Exception for insufficient stock errors."""

    def __init__(
        self, product_id: UUID, requested_quantity: int, available_quantity: int
    ) -> None:
        """Initialize insufficient stock error."""
        self.product_id = product_id
        self.requested_quantity = requested_quantity
        self.available_quantity = available_quantity
        message = f"Insufficient stock for product {product_id}. Requested: {requested_quantity}, Available: {available_quantity}"
        super().__init__(message)

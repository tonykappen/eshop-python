"""Domain exceptions for Ordering module with 1-1 parity to .NET."""

from uuid import UUID

from app.core.exceptions.base import NotFoundError


class OrderNotFoundError(NotFoundError):
    """Exception raised when an order is not found."""

    def __init__(self, order_id: UUID) -> None:
        """Initialize exception with order ID."""
        self.order_id = order_id
        super().__init__(name="Order", key=order_id)


class OrderItemNotFoundError(NotFoundError):
    """Exception raised when an order item is not found."""

    def __init__(self, item_id: UUID) -> None:
        """Initialize exception with item ID."""
        self.item_id = item_id
        super().__init__(name="OrderItem", key=item_id)


class OrderValidationError(Exception):
    """Exception for order validation errors."""

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize order validation error."""
        self.message = message
        self.field = field
        super().__init__(self.message)


class OrderCreationError(Exception):
    """Exception for order creation errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize order creation error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class OrderUpdateError(Exception):
    """Exception for order update errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize order update error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class OrderCancellationError(Exception):
    """Exception for order cancellation errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        """Initialize order cancellation error."""
        self.message = message
        self.details = details
        super().__init__(self.message)


class OrderStatusTransitionError(Exception):
    """Exception for invalid order status transitions."""

    def __init__(self, current_status: str, target_status: str, order_id: UUID) -> None:
        """Initialize order status transition error."""
        self.current_status = current_status
        self.target_status = target_status
        self.order_id = order_id
        message = f"Invalid status transition from {current_status} to {target_status} for order {order_id}"
        super().__init__(message)


class PaymentProcessingError(Exception):
    """Exception for payment processing errors."""

    def __init__(
        self, message: str, payment_id: UUID | None = None, details: str | None = None
    ) -> None:
        """Initialize payment processing error."""
        self.message = message
        self.payment_id = payment_id
        self.details = details
        super().__init__(self.message)


class InventoryReservationError(Exception):
    """Exception for inventory reservation errors."""

    def __init__(
        self, message: str, product_id: UUID | None = None, details: str | None = None
    ) -> None:
        """Initialize inventory reservation error."""
        self.message = message
        self.product_id = product_id
        self.details = details
        super().__init__(self.message)

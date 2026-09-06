"""Domain exceptions for ordering module."""

from app.modules.ordering.domain.exceptions.definitions import (
    InventoryReservationError,
    OrderCancellationError,
    OrderCreationError,
    OrderItemNotFoundError,
    OrderStatusTransitionError,
    OrderUpdateError,
    OrderValidationError,
    PaymentProcessingError,
)
from app.modules.ordering.domain.exceptions.order import OrderNotFoundException

OrderNotFoundError = OrderNotFoundException

__all__ = [
    "InventoryReservationError",
    "OrderCancellationError",
    "OrderCreationError",
    "OrderItemNotFoundError",
    "OrderNotFoundError",
    "OrderNotFoundException",
    "OrderStatusTransitionError",
    "OrderUpdateError",
    "OrderValidationError",
    "PaymentProcessingError",
]

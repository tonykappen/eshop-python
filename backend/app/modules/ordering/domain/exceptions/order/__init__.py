"""Domain exceptions for order aggregate."""

from app.modules.ordering.domain.exceptions.order.order_not_found import (
    OrderNotFoundException,
)

__all__ = ["OrderNotFoundException"]

"""Ordering domain module."""

from app.modules.ordering.domain.domain_events.orders import \
    OrderCreatedDomainEvent
from app.modules.ordering.domain.entities.order import Order, OrderItem
from app.modules.ordering.domain.exceptions.order import OrderNotFoundException
from app.modules.ordering.domain.repositories.order import IOrderRepository
from app.modules.ordering.domain.value_objects import Address, Payment

# Rebuild Pydantic models to resolve forward references
# This must be done after Order is imported so the forward reference in OrderCreatedDomainEvent can be resolved
OrderCreatedDomainEvent.model_rebuild()

__all__ = [
    "Order",
    "OrderItem",
    "Address",
    "Payment",
    "OrderCreatedDomainEvent",
    "OrderNotFoundException",
    "IOrderRepository",
]

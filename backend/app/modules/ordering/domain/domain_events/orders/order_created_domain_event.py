"""Order created domain event."""

from typing import TYPE_CHECKING
from uuid import UUID

from app.core.domain.entity import DomainEvent
from pydantic import Field

if TYPE_CHECKING:
    from app.modules.ordering.domain.entities.order.order import Order


class OrderCreatedDomainEvent(DomainEvent):
    """Domain event raised when an order is created."""

    event_type: str = Field(default="order.created", description="Event type")
    order: "Order" = Field(..., description="The created order")

    def __init__(self, order: "Order", **data):
        """Initialize the domain event."""
        super().__init__(
            event_type="order.created",
            order=order,
            **data,
        )

    @property
    def order_id(self) -> UUID:
        """Get the order ID."""
        return self.order.id

    @property
    def customer_id(self) -> UUID:
        """Get the customer ID."""
        return self.order.customer_id

    @property
    def order_name(self) -> str:
        """Get the order name."""
        return self.order.order_name

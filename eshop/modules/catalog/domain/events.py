"""Product domain events."""

from typing import Any

from pydantic import Field

from eshop.core.domain.entity import DomainEvent


class ProductCreatedEvent(DomainEvent):
    """Domain event raised when a product is created."""

    event_type: str = Field(
        default="ProductCreated", description="Event type identifier"
    )
    product: Any = Field(..., description="The created product")


class ProductPriceChangedEvent(DomainEvent):
    """Domain event raised when a product price is changed."""

    event_type: str = Field(
        default="ProductPriceChanged", description="Event type identifier"
    )
    product: Any = Field(..., description="The product with updated price")

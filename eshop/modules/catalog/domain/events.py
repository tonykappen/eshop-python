"""Product domain events."""

from typing import TYPE_CHECKING

from pydantic import Field

from eshop.core.domain.entity import DomainEvent

if TYPE_CHECKING:
    from eshop.modules.catalog.domain.models import Product


class ProductCreatedEvent(DomainEvent):
    """Domain event raised when a product is created."""

    event_type: str = Field(
        default="ProductCreated", description="Event type identifier"
    )
    product: "Product" = Field(..., description="The created product")


class ProductPriceChangedEvent(DomainEvent):
    """Domain event raised when a product price is changed."""

    event_type: str = Field(
        default="ProductPriceChanged", description="Event type identifier"
    )
    product: "Product" = Field(..., description="The product with updated price")

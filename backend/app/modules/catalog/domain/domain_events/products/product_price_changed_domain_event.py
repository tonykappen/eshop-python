"""Product price changed domain event."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.core.domain.events import DomainEvent
from app.modules.catalog.domain.entities.product.product import Product

# Import Money for type annotation (needed for Pydantic)
from app.modules.catalog.domain.value_objects import Money


class ProductPriceChangedDomainEvent(DomainEvent):
    """Domain event raised when a product price is changed."""

    event_type: str = Field(default="product.price_changed", description="Event type")
    product: Product = Field(..., description="The product with changed price")
    old_price: Money | None = Field(default=None, description="The old price before change")

    def __init__(self, product: Product, old_price: Money | None = None, **data):
        """Initialize the domain event."""
        super().__init__(
            aggregate_id=product.id,
            event_type="product.price_changed",
            product=product,
            old_price=old_price,
            **data,
        )

    @property
    def product_id(self) -> UUID:
        """Get the product ID."""
        return self.product.id

    @property
    def product_name(self) -> str:
        """Get the product name."""
        return self.product.name

    @property
    def product_sku(self) -> str:
        """Get the product SKU."""
        return str(self.product.sku)

    @property
    def new_price(self) -> str:
        """Get the new price as string."""
        return str(self.product.price)

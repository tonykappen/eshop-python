"""Product deleted domain event."""

from uuid import UUID

from app.core.domain.events import DomainEvent
from app.modules.catalog.domain.entities.product.product import Product
from pydantic import Field


class ProductDeletedDomainEvent(DomainEvent):
    """Domain event raised when a product is deleted."""

    event_type: str = Field(default="product.deleted", description="Event type")
    product: Product = Field(..., description="The deleted product")

    def __init__(self, product: Product, **data):
        """Initialize the domain event."""
        super().__init__(
            aggregate_id=product.id,
            event_type="product.deleted",
            product=product,
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

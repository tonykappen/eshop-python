"""Product deactivated domain event."""

from uuid import UUID

from pydantic import Field

from app.core.domain.events import DomainEvent
from app.modules.catalog.domain.product.models.product import Product


class ProductDeactivatedDomainEvent(DomainEvent):
    """Domain event raised when a product is deactivated."""

    event_type: str = Field(default="product.deactivated", description="Event type")
    product: Product = Field(..., description="The deactivated product")

    def __init__(self, product: Product, **data):
        """Initialize the domain event."""
        super().__init__(
            aggregate_id=product.id,
            event_type="product.deactivated",
            product=product,
            **data
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



"""Product created domain event."""

from uuid import UUID

from pydantic import Field

from app.core.domain.events import DomainEvent
from app.modules.catalog.domain.product.models.product import Product


class ProductCreatedDomainEvent(DomainEvent):
    """Domain event raised when a product is created."""

    event_type: str = Field(default="product.created", description="Event type")
    product: Product = Field(..., description="The created product")

    def __init__(self, product: Product, **data):
        """Initialize the domain event."""
        super().__init__(
            aggregate_id=product.id,
            event_type="product.created",
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

    @property
    def product_price(self) -> str:
        """Get the product price as string."""
        return str(self.product.price)



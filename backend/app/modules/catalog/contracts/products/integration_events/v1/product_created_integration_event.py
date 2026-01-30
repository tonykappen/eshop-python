"""Product created integration event v1.

INTERNAL USE ONLY - This event is not published externally.
Product creation is not externally observable per architecture specification.
External systems must discover products via APIs, not events.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreatedIntegrationEventV1(BaseModel):
    """Integration event for product creation (INTERNAL USE ONLY - not published externally)."""

    # Event metadata
    event_id: UUID = Field(..., description="Unique event ID")
    event_type: str = Field(default="product.created.v1", description="Event type")
    event_version: str = Field(default="1.0", description="Event version")
    occurred_at: datetime = Field(..., description="When the event occurred")
    source: str = Field(default="catalog-service", description="Event source")

    # Event data
    product_id: UUID = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_sku: str = Field(..., description="Product SKU")
    product_categories: list[str] = Field(..., description="Product categories")
    product_description: str = Field(..., description="Product description")
    product_image_file: str = Field(..., description="Product image file")
    product_price_amount: float = Field(..., description="Product price amount")
    product_price_currency: str = Field(
        default="USD", description="Product price currency"
    )

    # Additional context
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @classmethod
    def create(
        cls,
        product_id: UUID,
        product_name: str,
        product_sku: str,
        product_categories: list[str],
        product_description: str,
        product_image_file: str,
        product_price_amount: float,
        product_price_currency: str = "USD",
        metadata: dict[str, Any] | None = None,
    ) -> "ProductCreatedIntegrationEventV1":
        """
        Create a new product created integration event.

        NOTE: This event is for internal use only and should not be published externally.

        Args:
            product_id: Product ID
            product_name: Product name
            product_sku: Product SKU
            product_categories: Product categories
            product_description: Product description
            product_image_file: Product image file
            product_price_amount: Product price amount
            product_price_currency: Product price currency
            metadata: Additional metadata

        Returns:
            ProductCreatedIntegrationEventV1 instance
        """
        import uuid

        return cls(
            event_id=uuid.uuid4(),
            occurred_at=datetime.utcnow(),
            product_id=product_id,
            product_name=product_name,
            product_sku=product_sku,
            product_categories=product_categories,
            product_description=product_description,
            product_image_file=product_image_file,
            product_price_amount=product_price_amount,
            product_price_currency=product_price_currency,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source,
            "product_id": str(self.product_id),
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "product_categories": self.product_categories,
            "product_description": self.product_description,
            "product_image_file": self.product_image_file,
            "product_price_amount": self.product_price_amount,
            "product_price_currency": self.product_price_currency,
            "metadata": self.metadata,
        }

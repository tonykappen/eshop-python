"""Product price changed integration event v1."""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID

from pydantic import BaseModel, Field


class ProductPriceChangedIntegrationEventV1(BaseModel):
    """Integration event published when a product price is changed."""

    # Event metadata
    event_id: UUID = Field(..., description="Unique event ID")
    event_type: str = Field(default="product.price_changed.v1", description="Event type")
    event_version: str = Field(default="1.0", description="Event version")
    occurred_at: datetime = Field(..., description="When the event occurred")
    source: str = Field(default="catalog-service", description="Event source")
    
    # Event data
    product_id: UUID = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_sku: str = Field(..., description="Product SKU")
    old_price_amount: float = Field(..., description="Old price amount")
    new_price_amount: float = Field(..., description="New price amount")
    price_currency: str = Field(default="USD", description="Price currency")
    price_change_percentage: float = Field(..., description="Price change percentage")
    
    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @classmethod
    def create(
        cls,
        product_id: UUID,
        product_name: str,
        product_sku: str,
        old_price_amount: float,
        new_price_amount: float,
        price_currency: str = "USD",
        metadata: Dict[str, Any] | None = None,
    ) -> "ProductPriceChangedIntegrationEventV1":
        """
        Create a new product price changed integration event.
        
        Args:
            product_id: Product ID
            product_name: Product name
            product_sku: Product SKU
            old_price_amount: Old price amount
            new_price_amount: New price amount
            price_currency: Price currency
            metadata: Additional metadata
            
        Returns:
            ProductPriceChangedIntegrationEventV1 instance
        """
        import uuid
        
        # Calculate price change percentage
        if old_price_amount == 0:
            price_change_percentage = 0.0
        else:
            price_change_percentage = ((new_price_amount - old_price_amount) / old_price_amount) * 100
        
        return cls(
            event_id=uuid.uuid4(),
            occurred_at=datetime.utcnow(),
            product_id=product_id,
            product_name=product_name,
            product_sku=product_sku,
            old_price_amount=old_price_amount,
            new_price_amount=new_price_amount,
            price_currency=price_currency,
            price_change_percentage=price_change_percentage,
            metadata=metadata or {},
        )

    def to_dict(self) -> Dict[str, Any]:
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
            "old_price_amount": self.old_price_amount,
            "new_price_amount": self.new_price_amount,
            "price_currency": self.price_currency,
            "price_change_percentage": self.price_change_percentage,
            "metadata": self.metadata,
        }



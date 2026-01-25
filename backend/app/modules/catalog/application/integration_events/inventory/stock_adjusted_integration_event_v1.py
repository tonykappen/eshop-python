"""Stock adjusted integration event v1."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class StockAdjustedIntegrationEventV1(BaseModel):
    """Integration event published when stock is adjusted."""

    # Event metadata
    event_id: UUID = Field(..., description="Unique event ID")
    event_type: str = Field(
        default="inventory.stock_adjusted.v1", description="Event type"
    )
    event_version: str = Field(default="1.0", description="Event version")
    occurred_at: datetime = Field(..., description="When the event occurred")
    source: str = Field(default="catalog-service", description="Event source")

    # Event data
    inventory_item_id: UUID = Field(..., description="Inventory item ID")
    product_id: UUID = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_sku: str = Field(..., description="Product SKU")
    old_quantity: int = Field(..., description="Old quantity")
    new_quantity: int = Field(..., description="New quantity")
    adjustment: int = Field(..., description="Quantity adjustment")
    is_stock_increase: bool = Field(..., description="Whether this is a stock increase")
    is_stock_decrease: bool = Field(..., description="Whether this is a stock decrease")
    is_low_stock: bool = Field(..., description="Whether stock is now low")
    is_out_of_stock: bool = Field(..., description="Whether item is now out of stock")

    # Additional context
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @classmethod
    def create(
        cls,
        inventory_item_id: UUID,
        product_id: UUID,
        product_name: str,
        product_sku: str,
        old_quantity: int,
        new_quantity: int,
        adjustment: int,
        is_low_stock: bool,
        is_out_of_stock: bool,
        metadata: dict[str, Any] | None = None,
    ) -> "StockAdjustedIntegrationEventV1":
        """
        Create a new stock adjusted integration event.

        Args:
            inventory_item_id: Inventory item ID
            product_id: Product ID
            product_name: Product name
            product_sku: Product SKU
            old_quantity: Old quantity
            new_quantity: New quantity
            adjustment: Quantity adjustment
            is_low_stock: Whether stock is now low
            is_out_of_stock: Whether item is now out of stock
            metadata: Additional metadata

        Returns:
            StockAdjustedIntegrationEventV1 instance
        """
        import uuid

        return cls(
            event_id=uuid.uuid4(),
            occurred_at=datetime.utcnow(),
            inventory_item_id=inventory_item_id,
            product_id=product_id,
            product_name=product_name,
            product_sku=product_sku,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            adjustment=adjustment,
            is_stock_increase=adjustment > 0,
            is_stock_decrease=adjustment < 0,
            is_low_stock=is_low_stock,
            is_out_of_stock=is_out_of_stock,
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
            "inventory_item_id": str(self.inventory_item_id),
            "product_id": str(self.product_id),
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "old_quantity": self.old_quantity,
            "new_quantity": self.new_quantity,
            "adjustment": self.adjustment,
            "is_stock_increase": self.is_stock_increase,
            "is_stock_decrease": self.is_stock_decrease,
            "is_low_stock": self.is_low_stock,
            "is_out_of_stock": self.is_out_of_stock,
            "metadata": self.metadata,
        }

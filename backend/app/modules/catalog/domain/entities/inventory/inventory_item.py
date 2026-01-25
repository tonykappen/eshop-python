"""Inventory item domain entity."""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.core.domain.entity import Aggregate


class InventoryItem(Aggregate):
    """Inventory item aggregate root."""

    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(default=0, ge=0, description="Available quantity")
    reserved_quantity: int = Field(default=0, ge=0, description="Reserved quantity")
    reorder_threshold: int = Field(default=10, ge=0, description="Reorder threshold")
    max_stock_threshold: int = Field(
        default=1000, ge=0, description="Maximum stock threshold"
    )
    version: int = Field(default=1, description="Inventory item version")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    created_by: UUID | None = Field(
        None, description="User who created the inventory item"
    )
    updated_by: UUID | None = Field(
        None, description="User who last updated the inventory item"
    )
    is_deleted: bool = Field(default=False, description="Soft delete flag")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is non-negative."""
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("reserved_quantity")
    @classmethod
    def validate_reserved_quantity(cls, v: int) -> int:
        """Validate reserved quantity is non-negative."""
        if v < 0:
            raise ValueError("Reserved quantity cannot be negative")
        return v

    @property
    def available_quantity(self) -> int:
        """Get available quantity (total - reserved)."""
        return max(0, self.quantity - self.reserved_quantity)

    @property
    def needs_reorder(self) -> bool:
        """Check if inventory needs reordering."""
        return self.quantity <= self.reorder_threshold

    @property
    def is_out_of_stock(self) -> bool:
        """Check if inventory is out of stock."""
        return self.available_quantity <= 0

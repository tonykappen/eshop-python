"""Inventory availability read model for query side."""

from uuid import UUID

from pydantic import BaseModel, Field


class InventoryAvailabilityView(BaseModel):
    """Inventory availability read model for efficient querying."""

    product_id: UUID = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_sku: str = Field(..., description="Product SKU")
    available_quantity: int = Field(..., description="Available quantity")
    reserved_quantity: int = Field(..., description="Reserved quantity")
    total_quantity: int = Field(..., description="Total quantity")
    reorder_threshold: int = Field(..., description="Reorder threshold")
    max_stock_threshold: int = Field(..., description="Max stock threshold")
    is_low_stock: bool = Field(..., description="Whether stock is low")
    is_out_of_stock: bool = Field(..., description="Whether out of stock")
    is_available: bool = Field(..., description="Whether available for purchase")
    last_updated: str = Field(..., description="Last update timestamp")

    @property
    def stock_status(self) -> str:
        """Get stock status as string."""
        if self.is_out_of_stock:
            return "out_of_stock"
        elif self.is_low_stock:
            return "low_stock"
        else:
            return "in_stock"

    @property
    def stock_percentage(self) -> float:
        """Get stock percentage relative to max threshold."""
        if self.max_stock_threshold == 0:
            return 0.0
        return (self.total_quantity / self.max_stock_threshold) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "product_id": str(self.product_id),
            "product_name": self.product_name,
            "product_sku": self.product_sku,
            "available_quantity": self.available_quantity,
            "reserved_quantity": self.reserved_quantity,
            "total_quantity": self.total_quantity,
            "reorder_threshold": self.reorder_threshold,
            "max_stock_threshold": self.max_stock_threshold,
            "is_low_stock": self.is_low_stock,
            "is_out_of_stock": self.is_out_of_stock,
            "is_available": self.is_available,
            "stock_status": self.stock_status,
            "stock_percentage": self.stock_percentage,
            "last_updated": self.last_updated,
        }



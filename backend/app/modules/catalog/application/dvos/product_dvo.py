"""Product Data Value Object (DVO) for application layer."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductDVO(BaseModel):
    """Product Data Value Object for internal application use."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Product SKU")
    category: list[str] = Field(..., description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str = Field(..., description="Product image file path")
    price_amount: Decimal = Field(..., description="Product price amount")
    price_currency: str = Field(default="USD", description="Product price currency")
    version: int = Field(..., description="Product version")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    @property
    def price(self) -> str:
        """Get formatted price string."""
        return f"{self.price_amount} {self.price_currency}"

    @property
    def is_active(self) -> bool:
        """Check if product is active (not deleted)."""
        return True  # In this implementation, products are always active unless explicitly deactivated

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "sku": self.sku,
            "category": self.category,
            "description": self.description,
            "image_file": self.image_file,
            "price": self.price,
            "price_amount": float(self.price_amount),
            "price_currency": self.price_currency,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
        }



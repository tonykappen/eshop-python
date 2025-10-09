"""Product listing read model for query side."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductListingView(BaseModel):
    """Product listing read model for efficient querying."""

    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    sku: str = Field(..., description="Product SKU")
    category: list[str] = Field(..., description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str = Field(..., description="Product image file path")
    price_amount: Decimal = Field(..., description="Product price amount")
    price_currency: str = Field(default="USD", description="Product price currency")
    is_active: bool = Field(..., description="Whether product is active")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    # Denormalized fields for efficient querying
    category_names: str = Field(..., description="Comma-separated category names")
    search_text: str = Field(..., description="Searchable text content")
    price_range: str = Field(..., description="Price range category")

    @property
    def price(self) -> str:
        """Get formatted price string."""
        return f"{self.price_amount} {self.price_currency}"

    @property
    def is_available(self) -> bool:
        """Check if product is available for purchase."""
        return self.is_active

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
            "is_active": self.is_active,
            "is_available": self.is_available,
            "category_names": self.category_names,
            "search_text": self.search_text,
            "price_range": self.price_range,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }



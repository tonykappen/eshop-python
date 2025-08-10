"""Domain entities for the Catalog module."""

from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.core.domain.entity import Entity


class CatalogItem(Entity):
    """Domain entity for catalog items."""

    name: str = Field(..., description="Name of the catalog item")
    description: str | None = Field(None, description="Description of the catalog item")
    price: Decimal = Field(..., description="Price of the catalog item", gt=0)
    stock_quantity: int = Field(default=0, description="Available stock quantity", ge=0)
    is_available: bool = Field(
        default=True, description="Whether the item is available for purchase"
    )

    # Foreign keys (stored as UUIDs in domain, strings in ORM)
    category_id: UUID | None = Field(
        None, description="ID of the category this item belongs to"
    )
    brand_id: UUID | None = Field(
        None, description="ID of the brand this item belongs to"
    )

    def update_stock(self, quantity: int) -> None:
        """Update the stock quantity."""
        if quantity < 0:
            raise ValueError("Stock quantity cannot be negative")
        self.stock_quantity = quantity

    def reduce_stock(self, quantity: int) -> None:
        """Reduce stock by the specified quantity."""
        if quantity <= 0:
            raise ValueError("Quantity to reduce must be positive")
        if self.stock_quantity < quantity:
            raise ValueError("Insufficient stock")
        self.stock_quantity -= quantity

    def increase_stock(self, quantity: int) -> None:
        """Increase stock by the specified quantity."""
        if quantity <= 0:
            raise ValueError("Quantity to increase must be positive")
        self.stock_quantity += quantity

    def mark_unavailable(self) -> None:
        """Mark the item as unavailable."""
        self.is_available = False

    def mark_available(self) -> None:
        """Mark the item as available."""
        self.is_available = True

    def update_price(self, new_price: Decimal) -> None:
        """Update the price of the item."""
        if new_price <= 0:
            raise ValueError("Price must be positive")
        self.price = new_price


class CatalogCategory(Entity):
    """Domain entity for catalog categories."""

    name: str = Field(..., description="Name of the category")
    description: str | None = Field(None, description="Description of the category")

    def update_details(self, name: str, description: str | None = None) -> None:
        """Update category details."""
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty")
        self.name = name.strip()
        self.description = description


class CatalogBrand(Entity):
    """Domain entity for catalog brands."""

    name: str = Field(..., description="Name of the brand")
    description: str | None = Field(None, description="Description of the brand")
    logo_url: str | None = Field(None, description="URL of the brand logo")

    def update_details(
        self, name: str, description: str | None = None, logo_url: str | None = None
    ) -> None:
        """Update brand details."""
        if not name or not name.strip():
            raise ValueError("Brand name cannot be empty")
        self.name = name.strip()
        self.description = description
        self.logo_url = logo_url

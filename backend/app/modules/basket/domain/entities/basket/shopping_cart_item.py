"""ShoppingCartItem entity - represents an item in a shopping cart."""

from decimal import Decimal
from uuid import UUID

from app.core.domain.entity import Entity
from pydantic import Field, field_validator


class ShoppingCartItem(Entity):
    """ShoppingCartItem entity following .NET ShoppingCartItem class structure."""

    shopping_cart_id: UUID = Field(..., description="Shopping cart ID")
    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., description="Item quantity")
    color: str = Field(..., description="Item color")
    price: Decimal = Field(..., description="Item price (from Catalog module)")
    product_name: str = Field(..., description="Product name (from Catalog module)")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: Decimal) -> Decimal:
        """Validate price is positive."""
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate color is not empty."""
        if not v or not v.strip():
            raise ValueError("Color is required and cannot be empty")
        return v.strip()

    @field_validator("product_name")
    @classmethod
    def validate_product_name(cls, v: str) -> str:
        """Validate product name is not empty."""
        if not v or not v.strip():
            raise ValueError("Product name is required and cannot be empty")
        return v.strip()

    def update_price(self, new_price: Decimal) -> None:
        """
        Update the price of the item.

        Args:
            new_price: New price (validated)

        Raises:
            ValueError: If price validation fails
        """
        if new_price <= 0:
            raise ValueError("Price must be greater than 0")
        self.price = new_price

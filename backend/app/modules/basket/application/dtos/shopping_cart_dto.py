"""Shopping cart DTOs - matches .NET DTOs."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ShoppingCartItemDto(BaseModel):
    """Shopping cart item DTO - matches .NET ShoppingCartItemDto."""

    id: UUID | None = Field(None, description="Item ID (optional for creation)")
    shopping_cart_id: UUID | None = Field(None, description="Shopping cart ID (optional, will be set from user_name)")
    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Item quantity")
    color: str = Field(..., description="Item color")
    price: Decimal = Field(..., gt=0, description="Item price")
    product_name: str = Field(..., description="Product name")


class ShoppingCartDto(BaseModel):
    """Shopping cart DTO - matches .NET ShoppingCartDto."""

    id: UUID | None = Field(None, description="Shopping cart ID (optional for creation)")
    user_name: str = Field(..., description="User name")
    items: list[ShoppingCartItemDto] = Field(
        default_factory=list, description="Shopping cart items"
    )

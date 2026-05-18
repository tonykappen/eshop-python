"""AddItemIntoBasketCommand definition - matches .NET implementation."""

from uuid import UUID

from app.modules.basket.application.dtos.shopping_cart_dto import \
    ShoppingCartItemDto
from pydantic import BaseModel, Field


class AddItemIntoBasketCommand(BaseModel):
    """Command to add item into basket - matches .NET AddItemIntoBasketCommand."""

    user_name: str = Field(..., description="User name")
    shopping_cart_item: ShoppingCartItemDto = Field(
        ..., description="Shopping cart item"
    )


class AddItemIntoBasketResult(BaseModel):
    """Result of adding item into basket - matches .NET AddItemIntoBasketResult."""

    id: UUID = Field(..., description="Basket ID")

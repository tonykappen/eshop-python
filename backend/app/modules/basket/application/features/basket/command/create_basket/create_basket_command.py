"""CreateBasketCommand definition - matches .NET implementation."""

from uuid import UUID

from app.modules.basket.application.dtos.shopping_cart_dto import \
    ShoppingCartDto
from pydantic import BaseModel, Field


class CreateBasketCommand(BaseModel):
    """Command to create a new basket - matches .NET CreateBasketCommand."""

    shopping_cart: ShoppingCartDto = Field(..., description="Shopping cart data")


class CreateBasketResult(BaseModel):
    """Result of creating a basket - matches .NET CreateBasketResult."""

    id: UUID = Field(..., description="Created basket ID")

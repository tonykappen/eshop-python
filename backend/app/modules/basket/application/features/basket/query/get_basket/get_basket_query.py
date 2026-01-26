"""GetBasketQuery definition - matches .NET implementation."""

from pydantic import BaseModel, Field

from app.modules.basket.application.dtos.shopping_cart_dto import ShoppingCartDto


class GetBasketQuery(BaseModel):
    """Query to get basket - matches .NET GetBasketQuery."""

    user_name: str = Field(..., description="User name")


class GetBasketResult(BaseModel):
    """Result of getting basket - matches .NET GetBasketResult."""

    shopping_cart: ShoppingCartDto = Field(..., description="Shopping cart")

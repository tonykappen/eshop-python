"""CheckoutBasketCommand definition - matches .NET implementation."""

from pydantic import BaseModel, Field

from app.modules.basket.application.dtos.basket_checkout_dto import BasketCheckoutDto


class CheckoutBasketCommand(BaseModel):
    """Command to checkout basket - matches .NET CheckoutBasketCommand."""

    basket_checkout: BasketCheckoutDto = Field(..., description="Basket checkout data")


class CheckoutBasketResult(BaseModel):
    """Result of checking out basket - matches .NET CheckoutBasketResult."""

    is_success: bool = Field(..., description="Whether the checkout was successful")

"""UpdateItemPriceInBasketCommand definition - matches .NET implementation."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class UpdateItemPriceInBasketCommand(BaseModel):
    """Command to update item price in basket - matches .NET UpdateItemPriceInBasketCommand."""

    product_id: UUID = Field(..., description="Product ID")
    price: Decimal = Field(..., gt=0, description="New price")


class UpdateItemPriceInBasketResult(BaseModel):
    """Result of updating item price in basket - matches .NET UpdateItemPriceInBasketResult."""

    is_success: bool = Field(..., description="Whether the update was successful")

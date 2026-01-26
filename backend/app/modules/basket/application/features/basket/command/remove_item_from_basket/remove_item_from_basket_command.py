"""RemoveItemFromBasketCommand definition - matches .NET implementation."""

from uuid import UUID

from pydantic import BaseModel, Field


class RemoveItemFromBasketCommand(BaseModel):
    """Command to remove item from basket - matches .NET RemoveItemFromBasketCommand."""

    user_name: str = Field(..., description="User name")
    product_id: UUID = Field(..., description="Product ID to remove")


class RemoveItemFromBasketResult(BaseModel):
    """Result of removing item from basket - matches .NET RemoveItemFromBasketResult."""

    id: UUID = Field(..., description="Basket ID")

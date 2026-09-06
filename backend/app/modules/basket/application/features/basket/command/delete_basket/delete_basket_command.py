"""DeleteBasketCommand definition - matches .NET implementation."""

from pydantic import BaseModel, Field


class DeleteBasketCommand(BaseModel):
    """Command to delete basket - matches .NET DeleteBasketCommand."""

    user_name: str = Field(..., description="User name")


class DeleteBasketResult(BaseModel):
    """Result of deleting basket - matches .NET DeleteBasketResult."""

    is_success: bool = Field(..., description="Whether the deletion was successful")

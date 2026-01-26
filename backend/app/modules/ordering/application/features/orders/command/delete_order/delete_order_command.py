"""DeleteOrderCommand definition - matches .NET implementation."""

from uuid import UUID

from pydantic import BaseModel, Field


class DeleteOrderCommand(BaseModel):
    """Command to delete an order - matches .NET DeleteOrderCommand."""

    order_id: UUID = Field(..., description="Order ID to delete")


class DeleteOrderResult(BaseModel):
    """Result of deleting an order - matches .NET DeleteOrderResult."""

    is_success: bool = Field(..., description="Whether deletion was successful")

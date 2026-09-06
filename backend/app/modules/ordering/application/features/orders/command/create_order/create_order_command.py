"""CreateOrderCommand definition - matches .NET implementation."""

from uuid import UUID

from app.modules.ordering.application.dtos.order_dto import OrderDto
from pydantic import BaseModel, Field


class CreateOrderCommand(BaseModel):
    """Command to create a new order - matches .NET CreateOrderCommand."""

    order: OrderDto = Field(..., description="Order data")


class CreateOrderResult(BaseModel):
    """Result of creating an order - matches .NET CreateOrderResult."""

    id: UUID = Field(..., description="Created order ID")

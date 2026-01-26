"""CreateOrderCommand definition - matches .NET implementation."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.ordering.application.dtos.order_dto import OrderDto


class CreateOrderCommand(BaseModel):
    """Command to create a new order - matches .NET CreateOrderCommand."""

    order: OrderDto = Field(..., description="Order data")


class CreateOrderResult(BaseModel):
    """Result of creating an order - matches .NET CreateOrderResult."""

    id: UUID = Field(..., description="Created order ID")

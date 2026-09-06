"""GetOrderByIdQuery definition - matches .NET implementation."""

from uuid import UUID

from app.modules.ordering.application.dtos.order_dto import OrderDto
from pydantic import BaseModel, Field


class GetOrderByIdQuery(BaseModel):
    """Query to get an order by ID - matches .NET GetOrderByIdQuery."""

    id: UUID = Field(..., description="Order ID")


class GetOrderByIdResult(BaseModel):
    """Result of getting an order by ID - matches .NET GetOrderByIdResult."""

    order: OrderDto = Field(..., description="Order data")

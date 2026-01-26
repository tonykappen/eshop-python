"""OrderItemDto for ordering application layer."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemDto(BaseModel):
    """OrderItem DTO matching .NET OrderItemDto record."""

    order_id: UUID = Field(..., description="Order ID")
    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., description="Quantity")
    price: Decimal = Field(..., description="Price")

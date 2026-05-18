"""OrderDto for ordering application layer."""

from uuid import UUID

from app.modules.ordering.application.dtos.address_dto import AddressDto
from app.modules.ordering.application.dtos.order_item_dto import OrderItemDto
from app.modules.ordering.application.dtos.payment_dto import PaymentDto
from pydantic import BaseModel, Field


class OrderDto(BaseModel):
    """Order DTO matching .NET OrderDto record."""

    id: UUID = Field(..., description="Order ID")
    customer_id: UUID = Field(..., description="Customer ID")
    order_name: str = Field(..., description="Order name")
    shipping_address: AddressDto = Field(..., description="Shipping address")
    billing_address: AddressDto = Field(..., description="Billing address")
    payment: PaymentDto = Field(..., description="Payment information")
    items: list[OrderItemDto] = Field(..., description="Order items")

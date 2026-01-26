"""BasketCheckoutIntegrationEvent - matches .NET contract."""

from decimal import Decimal
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.messaging.integration_event import BasketIntegrationEvent


class BasketCheckoutItem(BaseModel):
    """Basket checkout item - represents an item in the basket at checkout."""

    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., description="Item quantity")
    price: Decimal = Field(..., description="Item price")


class BasketCheckoutIntegrationEvent(BasketIntegrationEvent):
    """Integration event published when a basket is checked out."""

    # Event data
    user_name: str = Field(..., description="User name")
    customer_id: UUID = Field(..., description="Customer ID")
    total_price: Decimal = Field(..., description="Total price")
    # Basket items
    items: List[BasketCheckoutItem] = Field(default_factory=list, description="Basket items")
    # Shipping and Billing Address
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email_address: str = Field(..., description="Email address")
    address_line: str = Field(..., description="Address line")
    country: str = Field(..., description="Country")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="Zip code")
    # Payment
    card_name: str = Field(..., description="Card name")
    card_number: str = Field(..., description="Card number")
    expiration: str = Field(..., description="Expiration date")
    cvv: str = Field(..., description="CVV")
    payment_method: int = Field(..., description="Payment method")

"""BasketCheckoutIntegrationEvent - matches .NET contract."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.messaging.integration_event import BasketIntegrationEvent


class BasketCheckoutIntegrationEvent(BasketIntegrationEvent):
    """Integration event published when a basket is checked out."""

    # Event data
    user_name: str = Field(..., description="User name")
    customer_id: UUID = Field(..., description="Customer ID")
    total_price: Decimal = Field(..., description="Total price")
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

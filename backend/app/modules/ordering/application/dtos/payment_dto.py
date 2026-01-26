"""PaymentDto for ordering application layer."""

from pydantic import BaseModel, Field


class PaymentDto(BaseModel):
    """Payment DTO matching .NET PaymentDto record."""

    card_name: str = Field(..., description="Card name")
    card_number: str = Field(..., description="Card number")
    expiration: str = Field(..., description="Expiration date")
    cvv: str = Field(..., description="CVV")
    payment_method: int = Field(..., description="Payment method")

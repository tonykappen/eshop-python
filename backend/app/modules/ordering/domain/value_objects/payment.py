"""Payment value object for ordering domain."""

from app.core.domain.entity import ValueObject
from pydantic import Field, field_validator


class Payment(ValueObject):
    """Payment value object matching .NET Payment record."""

    card_name: str | None = Field(default=None, description="Card name")
    card_number: str = Field(..., description="Card number")
    expiration: str = Field(..., description="Expiration date")
    cvv: str = Field(..., description="CVV")
    payment_method: int = Field(..., description="Payment method")

    @field_validator("card_name")
    @classmethod
    def validate_card_name(cls, v: str | None) -> str | None:
        """Validate card name is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Card name cannot be empty if provided")
        return v.strip() if v else None

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str) -> str:
        """Validate card number is not empty."""
        if not v or not v.strip():
            raise ValueError("Card number is required and cannot be empty")
        return v.strip()

    @field_validator("cvv")
    @classmethod
    def validate_cvv(cls, v: str) -> str:
        """Validate CVV is not empty and length <= 3."""
        if not v or not v.strip():
            raise ValueError("CVV is required and cannot be empty")
        if len(v.strip()) > 3:
            raise ValueError("CVV length cannot be greater than 3")
        return v.strip()

    @classmethod
    def of(
        cls,
        card_name: str,
        card_number: str,
        expiration: str,
        cvv: str,
        payment_method: int,
    ) -> "Payment":
        """
        Create a Payment value object, matching .NET Payment.Of static method.

        Args:
            card_name: Card name (required, cannot be empty)
            card_number: Card number (required, cannot be empty)
            expiration: Expiration date
            cvv: CVV (required, cannot be empty, max length 3)
            payment_method: Payment method

        Returns:
            Payment value object

        Raises:
            ValueError: If card_name, card_number, or cvv is empty, or cvv length > 3
        """
        if not card_name or not card_name.strip():
            raise ValueError("Card name is required and cannot be empty")
        if not card_number or not card_number.strip():
            raise ValueError("Card number is required and cannot be empty")
        if not cvv or not cvv.strip():
            raise ValueError("CVV is required and cannot be empty")
        if len(cvv.strip()) > 3:
            raise ValueError("CVV length cannot be greater than 3")

        return cls(
            card_name=card_name.strip(),
            card_number=card_number.strip(),
            expiration=expiration,
            cvv=cvv.strip(),
            payment_method=payment_method,
        )

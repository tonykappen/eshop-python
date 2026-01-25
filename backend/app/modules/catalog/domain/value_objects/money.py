"""Money value object for catalog domain."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Money(BaseModel):
    """Money value object representing currency and amount."""

    amount: Decimal = Field(..., description="Monetary amount")
    currency: str = Field(default="USD", description="Currency code")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Any) -> Decimal:
        """Validate that amount is non-negative."""
        if isinstance(v, (int, float, str)):
            amount = Decimal(str(v))
        elif isinstance(v, Decimal):
            amount = v
        else:
            raise ValueError("Amount must be a number")

        if amount < 0:
            raise ValueError("Amount cannot be negative")

        return amount

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if not v or len(v) != 3:
            raise ValueError("Currency must be a 3-letter code")
        return v.upper()

    def __str__(self) -> str:
        """String representation of money."""
        return f"{self.amount} {self.currency}"

    def __eq__(self, other: Any) -> bool:
        """Equality comparison."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash((self.amount, self.currency))

    def add(self, other: "Money") -> "Money":
        """Add another money amount."""
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def subtract(self, other: "Money") -> "Money":
        """Subtract another money amount."""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract money with different currencies")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def multiply(self, factor: Decimal) -> "Money":
        """Multiply by a factor."""
        return Money(amount=self.amount * factor, currency=self.currency)

    def is_zero(self) -> bool:
        """Check if amount is zero."""
        return self.amount == 0

    def is_positive(self) -> bool:
        """Check if amount is positive."""
        return self.amount > 0

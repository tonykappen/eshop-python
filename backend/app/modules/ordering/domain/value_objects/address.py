"""Address value object for ordering domain."""

from pydantic import Field, field_validator

from app.core.domain.entity import ValueObject


class Address(ValueObject):
    """Address value object matching .NET Address record."""

    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email_address: str | None = Field(default=None, description="Email address")
    address_line: str = Field(..., description="Address line")
    country: str = Field(..., description="Country")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="Zip code")

    @field_validator("email_address")
    @classmethod
    def validate_email_address(cls, v: str | None) -> str | None:
        """Validate email address is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError("Email address cannot be empty if provided")
        return v.strip() if v else None

    @field_validator("address_line")
    @classmethod
    def validate_address_line(cls, v: str) -> str:
        """Validate address line is not empty."""
        if not v or not v.strip():
            raise ValueError("Address line is required and cannot be empty")
        return v.strip()

    @classmethod
    def of(
        cls,
        first_name: str,
        last_name: str,
        email_address: str,
        address_line: str,
        country: str,
        state: str,
        zip_code: str,
    ) -> "Address":
        """
        Create an Address value object, matching .NET Address.Of static method.

        Args:
            first_name: First name
            last_name: Last name
            email_address: Email address (required, cannot be empty)
            address_line: Address line (required, cannot be empty)
            country: Country
            state: State
            zip_code: Zip code

        Returns:
            Address value object

        Raises:
            ValueError: If email_address or address_line is empty
        """
        if not email_address or not email_address.strip():
            raise ValueError("Email address is required and cannot be empty")
        if not address_line or not address_line.strip():
            raise ValueError("Address line is required and cannot be empty")

        return cls(
            first_name=first_name,
            last_name=last_name,
            email_address=email_address.strip(),
            address_line=address_line.strip(),
            country=country,
            state=state,
            zip_code=zip_code,
        )

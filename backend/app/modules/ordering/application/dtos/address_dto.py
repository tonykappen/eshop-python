"""AddressDto for ordering application layer."""

from pydantic import BaseModel, Field


class AddressDto(BaseModel):
    """Address DTO matching .NET AddressDto record."""

    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email_address: str = Field(..., description="Email address")
    address_line: str = Field(..., description="Address line")
    country: str = Field(..., description="Country")
    state: str = Field(..., description="State")
    zip_code: str = Field(..., description="Zip code")

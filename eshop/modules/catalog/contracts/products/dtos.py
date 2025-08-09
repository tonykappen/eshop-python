"""Product DTOs for catalog contracts."""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductDto(BaseModel):
    """Product DTO matching .NET ProductDto record structure."""

    id: UUID = Field(..., description="Product unique identifier")
    name: str = Field(..., description="Product name")
    category: list[str] = Field(default_factory=list, description="Product categories")
    description: str = Field(..., description="Product description")
    image_file: str = Field(..., description="Product image file path")
    price: Decimal = Field(..., description="Product price", gt=0)

    class Config:
        """Pydantic configuration."""

        json_encoders = {UUID: str, Decimal: float}

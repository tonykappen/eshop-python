"""Product DTOs for catalog contracts."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductDto(BaseModel):
    """Product DTO matching .NET ProductDto record structure."""

    id: Optional[UUID] = Field(default=None, description="Product unique identifier")
    name: str = Field(..., description="Product name")
    category: list[str] = Field(default_factory=list, description="Product categories")
    description: str = Field(..., description="Product description")
    picture_url: str = Field(..., description="Product picture URL")
    price: Decimal = Field(..., description="Product price", gt=0)

    class Config:
        """Pydantic configuration."""

        json_encoders = {UUID: str, Decimal: float}

"""Create product request contract."""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CreateProductRequest(BaseModel):
    """Request contract for creating a product."""

    name: str = Field(..., description="Product name", min_length=1, max_length=255)
    sku: str = Field(..., description="Product SKU", min_length=3, max_length=50)
    category: list[str] = Field(..., description="Product categories", min_items=1)
    description: str = Field(..., description="Product description", min_length=1)
    image_file: str = Field(..., description="Product image file path", min_length=1)
    price: float = Field(..., description="Product price", gt=0)
    currency: str = Field(default="USD", description="Product currency", min_length=3, max_length=3)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate product name."""
        if not v or not v.strip():
            raise ValueError("Product name cannot be empty")
        return v.strip()

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Validate product SKU."""
        if not v or not v.strip():
            raise ValueError("Product SKU cannot be empty")
        
        # Convert to uppercase and validate format
        v = v.strip().upper()
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Product SKU must contain only letters, numbers, hyphens, and underscores")
        
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: list[str]) -> list[str]:
        """Validate product categories."""
        if not v:
            raise ValueError("Product must have at least one category")
        
        # Clean and validate categories
        cleaned_categories = []
        for cat in v:
            if not cat or not cat.strip():
                raise ValueError("Category cannot be empty")
            cleaned_categories.append(cat.strip())
        
        return cleaned_categories

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate product description."""
        if not v or not v.strip():
            raise ValueError("Product description cannot be empty")
        return v.strip()

    @field_validator("image_file")
    @classmethod
    def validate_image_file(cls, v: str) -> str:
        """Validate product image file."""
        if not v or not v.strip():
            raise ValueError("Product image file cannot be empty")
        return v.strip()

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate product price."""
        if v <= 0:
            raise ValueError("Product price must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        if not v or len(v) != 3:
            raise ValueError("Currency must be a 3-letter code")
        return v.upper()

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "iPhone 15 Pro",
                "sku": "IPHONE-15-PRO-256",
                "category": ["Electronics", "Smartphones"],
                "description": "Latest iPhone with advanced camera system and A17 Pro chip",
                "image_file": "/images/iphone-15-pro.jpg",
                "price": 999.00,
                "currency": "USD"
            }
        }



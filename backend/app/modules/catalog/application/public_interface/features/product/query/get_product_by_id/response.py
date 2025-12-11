"""Get product by ID response contract."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.catalog.application.public_interface.dto.product import ProductDto


class GetProductByIdResponse(BaseModel):
    """Response contract for getting a product by ID."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    product: Optional[ProductDto] = Field(None, description="Product data")
    product_id: UUID = Field(..., description="ID of the requested product")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Product retrieved successfully",
                "product_id": "123e4567-e89b-12d3-a456-426614174000",
                "product": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "name": "iPhone 15 Pro",
                    "sku": "IPHONE-15-PRO-256",
                    "category": ["Electronics", "Smartphones"],
                    "description": "Latest iPhone with advanced camera system and A17 Pro chip",
                    "image_file": "/images/iphone-15-pro.jpg",
                    "price": 999.00,
                    "currency": "USD",
                    "version": 1,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            }
        }



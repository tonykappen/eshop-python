"""Get product by ID request contract."""

from uuid import UUID

from pydantic import BaseModel, Field


class GetProductByIdRequest(BaseModel):
    """Request contract for getting a product by ID."""

    product_id: UUID = Field(..., description="Product ID")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "product_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }



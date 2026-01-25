"""GetProductsByCategoryQuery definition - Query DTO for category-filtered products."""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.core.pagination.models import PaginatedResult


class GetProductsByCategoryQuery(BaseModel):
    """Query DTO to get products filtered by category with pagination."""

    category: str = Field(..., description="Category name to filter products by")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of items per page")
    category_id: Optional[UUID] = Field(None, description="Optional category ID (for future use)")


class GetProductsByCategoryResult(PaginatedResult[ProductDto]):
    """Result of getting products by category - paginated product list."""

    category: str = Field(..., description="Category that was used for filtering")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            UUID: str,
        }

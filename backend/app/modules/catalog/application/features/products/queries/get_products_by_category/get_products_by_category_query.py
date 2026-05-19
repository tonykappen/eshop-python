"""GetProductsByCategoryQuery definition - Query DTO for category-filtered products."""

from uuid import UUID

from app.core.pagination.models import PaginatedResult
from app.modules.catalog.application.public_interface.dto.product import \
    ProductDto
from pydantic import BaseModel, Field, field_validator


class GetProductsByCategoryQuery(BaseModel):
    """Query DTO to get products filtered by category with pagination."""

    category: str = Field(..., description="Category name to filter products by")
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(
        default=10, ge=1, le=100, description="Number of items per page"
    )
    category_id: UUID | None = Field(
        default=None, description="Optional category ID (for future use)"
    )

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, v: str) -> str:
        """Reject empty or whitespace-only category names."""
        if not v or not v.strip():
            raise ValueError("category must be a non-empty string")
        return v.strip()


class GetProductsByCategoryResult(PaginatedResult[ProductDto]):
    """Result of getting products by category - paginated product list."""

    category: str = Field(..., description="Category that was used for filtering")

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            UUID: str,
        }

"""Category domain entity."""

from datetime import datetime
from uuid import UUID

from app.core.domain.entity import Aggregate
from pydantic import Field, field_validator


class Category(Aggregate):
    """Category aggregate root."""

    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Category description")
    parent_id: UUID | None = Field(None, description="Parent category ID")
    is_active: bool = Field(default=True, description="Whether category is active")
    version: int = Field(default=1, description="Category version")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    created_by: UUID | None = Field(None, description="User who created the category")
    updated_by: UUID | None = Field(
        None, description="User who last updated the category"
    )
    is_deleted: bool = Field(default=False, description="Soft delete flag")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate category name is not empty."""
        if not v or not v.strip():
            raise ValueError("Category name cannot be empty")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError("Category description cannot be empty")
        return v.strip()

    @property
    def is_root(self) -> bool:
        """Check if category is a root category (no parent)."""
        return self.parent_id is None

"""Category Data Value Object (DVO) for application layer."""

from uuid import UUID

from pydantic import BaseModel, Field


class CategoryDVO(BaseModel):
    """Category Data Value Object for internal application use."""

    id: UUID = Field(..., description="Category ID")
    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Category description")
    parent_id: UUID | None = Field(None, description="Parent category ID")
    is_active: bool = Field(..., description="Whether category is active")
    version: int = Field(..., description="Category version")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    @property
    def is_root(self) -> bool:
        """Check if category is a root category (no parent)."""
        return self.parent_id is None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "is_active": self.is_active,
            "is_root": self.is_root,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

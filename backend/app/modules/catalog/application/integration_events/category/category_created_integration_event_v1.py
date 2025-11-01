"""Category created integration event v1."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryCreatedIntegrationEventV1(BaseModel):
    """Integration event published when a category is created."""

    # Event metadata
    event_id: UUID = Field(..., description="Unique event ID")
    event_type: str = Field(default="category.created.v1", description="Event type")
    event_version: str = Field(default="1.0", description="Event version")
    occurred_at: datetime = Field(..., description="When the event occurred")
    source: str = Field(default="catalog-service", description="Event source")

    # Event data
    category_id: UUID = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")
    category_description: str = Field(..., description="Category description")
    parent_category_id: UUID | None = Field(None, description="Parent category ID")
    is_root_category: bool = Field(..., description="Whether this is a root category")

    # Additional context
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @classmethod
    def create(
        cls,
        category_id: UUID,
        category_name: str,
        category_description: str,
        parent_category_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "CategoryCreatedIntegrationEventV1":
        """
        Create a new category created integration event.

        Args:
            category_id: Category ID
            category_name: Category name
            category_description: Category description
            parent_category_id: Parent category ID
            metadata: Additional metadata

        Returns:
            CategoryCreatedIntegrationEventV1 instance
        """
        import uuid

        return cls(
            event_id=uuid.uuid4(),
            occurred_at=datetime.utcnow(),
            category_id=category_id,
            category_name=category_name,
            category_description=category_description,
            parent_category_id=parent_category_id,
            is_root_category=parent_category_id is None,
            metadata=metadata or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "event_version": self.event_version,
            "occurred_at": self.occurred_at.isoformat(),
            "source": self.source,
            "category_id": str(self.category_id),
            "category_name": self.category_name,
            "category_description": self.category_description,
            "parent_category_id": (
                str(self.parent_category_id) if self.parent_category_id else None
            ),
            "is_root_category": self.is_root_category,
            "metadata": self.metadata,
        }

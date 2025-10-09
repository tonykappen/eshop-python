"""Category created domain event."""

from uuid import UUID

from pydantic import Field

from app.core.domain.events import DomainEvent
from app.modules.catalog.domain.category.models.category import Category


class CategoryCreatedDomainEvent(DomainEvent):
    """Domain event raised when a category is created."""

    event_type: str = Field(default="category.created", description="Event type")
    category: Category = Field(..., description="The created category")

    def __init__(self, category: Category, **data):
        """Initialize the domain event."""
        super().__init__(
            aggregate_id=category.id,
            event_type="category.created",
            category=category,
            **data
        )

    @property
    def category_id(self) -> UUID:
        """Get the category ID."""
        return self.category.id

    @property
    def category_name(self) -> str:
        """Get the category name."""
        return self.category.name

    @property
    def parent_id(self) -> UUID | None:
        """Get the parent category ID."""
        return self.category.parent_id



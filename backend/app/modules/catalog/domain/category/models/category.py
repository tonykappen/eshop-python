"""Category domain model."""

from uuid import UUID

from pydantic import Field, field_validator

from app.core.domain.entity import Aggregate


class Category(Aggregate):
    """Category aggregate."""

    name: str = Field(..., description="Category name")
    description: str = Field(..., description="Category description")
    parent_id: UUID | None = Field(None, description="Parent category ID")
    is_active: bool = Field(default=True, description="Whether category is active")

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

    @classmethod
    def create(
        cls,
        category_id: UUID,
        name: str,
        description: str,
        parent_id: UUID | None = None,
    ) -> "Category":
        """
        Create a new category.

        Args:
            category_id: Unique identifier for the category
            name: Category name (validated)
            description: Category description (validated)
            parent_id: Parent category ID (optional)

        Returns:
            Created Category instance with domain events

        Raises:
            ValueError: If any validation fails
        """
        category = cls(
            id=category_id,
            name=name,
            description=description,
            parent_id=parent_id,
            is_active=True,
        )

        # Add domain event
        from app.modules.catalog.domain.category.domain_events.category_created_domain_event import (
            CategoryCreatedDomainEvent,
        )

        category.add_domain_event(CategoryCreatedDomainEvent(category=category))

        return category

    def update(self, name: str, description: str) -> None:
        """
        Update category details.

        Args:
            name: New category name (validated)
            description: New description (validated)

        Raises:
            ValueError: If any validation fails
        """
        self.name = name
        self.description = description
        self.increment_version()

    def deactivate(self) -> None:
        """Deactivate the category."""
        self.is_active = False
        self.increment_version()

    def activate(self) -> None:
        """Activate the category."""
        self.is_active = True
        self.increment_version()

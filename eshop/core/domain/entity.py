"""Base Entity class for Domain-Driven Design."""

from abc import ABC
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for domain events."""

    event_id: UUID = Field(default_factory=uuid4)
    occurred_on: str = Field(default_factory=lambda: str(uuid4().time))
    event_type: str = Field(default="")

    class Config:
        arbitrary_types_allowed = True


class Entity(ABC, BaseModel):
    """Base Entity class following DDD patterns."""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime | None = Field(default=None)
    created_by: str | None = Field(default=None)
    last_modified: datetime | None = Field(default=None)
    last_modified_by: str | None = Field(default=None)
    domain_events: list[DomainEvent] = Field(default_factory=list, exclude=True)

    def add_domain_event(self, event: DomainEvent) -> None:
        """Add a domain event to the entity."""
        self.domain_events.append(event)

    def clear_domain_events(self) -> None:
        """Clear all domain events."""
        self.domain_events.clear()

    @property
    def domain_events_copy(self) -> list[DomainEvent]:
        """Get all domain events."""
        return self.domain_events.copy()

    def __eq__(self, other: Any) -> bool:
        """Compare entities by ID."""
        if not isinstance(other, Entity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    class Config:
        arbitrary_types_allowed = True


class Aggregate(Entity):
    """Base Aggregate class following DDD patterns."""

    version: int = Field(default=1)

    def increment_version(self) -> None:
        """Increment the aggregate version."""
        self.version += 1


class ValueObject(BaseModel):
    """Base Value Object class following DDD patterns."""

    def __eq__(self, other: Any) -> bool:
        """Compare value objects by their attributes."""
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """Hash based on all attributes."""
        return hash(tuple(sorted(self.model_dump().items())))

    class Config:
        arbitrary_types_allowed = True
        frozen = True

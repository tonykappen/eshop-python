"""Base Repository interface for Domain-Driven Design."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# Type variables for generic repository
T = TypeVar("T")  # Entity type
K = TypeVar("K")  # Key type (usually UUID or int)


class Repository(Generic[T, K], ABC):
    """Base repository interface following DDD patterns."""

    @abstractmethod
    async def get_by_id(self, entity_id: K) -> T | None:
        """
        Get entity by ID.

        Args:
            entity_id: Entity ID

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def add(self, entity: T) -> None:
        """
        Add a new entity.

        Args:
            entity: Entity to add
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> None:
        """
        Update an existing entity.

        Args:
            entity: Entity to update
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: K) -> None:
        """
        Delete an entity.

        Args:
            entity_id: Entity ID to delete
        """
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> list[T]:
        """
        Get all entities with pagination.

        Args:
            skip: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of entities
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Get total count of entities.

        Returns:
            Total number of entities
        """
        pass

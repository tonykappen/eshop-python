"""Base Repository interface for Domain-Driven Design."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

# Type variables for generic repository
T = TypeVar("T")  # Entity type
K = TypeVar("K")  # Key type (usually UUID or int)


class Repository(Generic[T, K], ABC):
    """Base repository interface following DDD patterns.

    Concrete subclasses may widen signatures (e.g. return the persisted
    entity, accept extra optional arguments for delete) — these methods
    are intentionally permissive to support those module-specific shapes.
    """

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
    async def add(self, entity: T) -> Any:
        """
        Add a new entity.

        Args:
            entity: Entity to add

        Returns:
            Implementation-defined (typically None or the persisted entity).
        """
        pass

    @abstractmethod
    async def update(self, entity: T) -> Any:
        """
        Update an existing entity.

        Args:
            entity: Entity to update

        Returns:
            Implementation-defined (typically None or the updated entity).
        """
        pass

    @abstractmethod
    async def delete(self, entity_id: K, *args: Any, **kwargs: Any) -> Any:
        """
        Delete an entity.

        Args:
            entity_id: Entity ID to delete
            *args: Implementation-specific positional arguments.
            **kwargs: Implementation-specific keyword arguments
                (e.g. ``deleted_by``, ``deletion_reason``).

        Returns:
            Implementation-defined (e.g. ``None`` or ``bool``).
        """
        pass

    @abstractmethod
    async def get_all(self, *args: Any, **kwargs: Any) -> Any:
        """
        Get all entities (signature is implementation-defined).

        Returns:
            Implementation-defined (e.g. ``list[T]`` or ``tuple[list[T], int]``).
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

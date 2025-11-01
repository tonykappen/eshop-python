"""Unit of Work implementation for catalog module."""

import logging
from typing import Any, TypeVar

from app.core.database.session import AsyncSession
from app.modules.catalog.application.transactions.commit_interceptors import (
    commit_interceptor_registry,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class UnitOfWork:
    """Unit of Work for managing transactions and repositories."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the Unit of Work.

        Args:
            session: Database session
        """
        self.session = session
        self._repositories: dict[type[Any], Any] = {}
        self._entities: list[Any] = []

    def get_repository(self, repository_type: type[T]) -> T:
        """
        Get repository instance.

        Args:
            repository_type: Type of repository to get

        Returns:
            Repository instance
        """
        if repository_type not in self._repositories:
            # This would be injected in a real implementation
            # For now, we'll create a placeholder
            self._repositories[repository_type] = None

        return self._repositories[repository_type]

    def add_entity(self, entity: Any) -> None:
        """
        Add entity to be tracked.

        Args:
            entity: Entity to track
        """
        self._entities.append(entity)

    def add_entities(self, entities: list[Any]) -> None:
        """
        Add multiple entities to be tracked.

        Args:
            entities: List of entities to track
        """
        self._entities.extend(entities)

    async def commit(self) -> None:
        """
        Commit the transaction with interceptors.

        Raises:
            Exception: If commit fails
        """
        try:
            # Execute before commit hooks
            await commit_interceptor_registry.execute_before_commit(
                self.session, self._entities
            )

            # Flush changes to database
            await self.session.flush()

            # Commit the transaction
            await self.session.commit()

            # Execute after commit hooks
            await commit_interceptor_registry.execute_after_commit(
                self.session, self._entities
            )

            logger.info(f"Successfully committed {len(self._entities)} entities")

        except Exception as e:
            # Execute rollback hooks
            await commit_interceptor_registry.execute_on_rollback(
                self.session, self._entities, e
            )

            # Rollback the transaction
            await self.session.rollback()

            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    async def rollback(self) -> None:
        """
        Rollback the transaction.
        """
        await self.session.rollback()
        logger.info("Transaction rolled back")

    async def __aenter__(self) -> "UnitOfWork":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()


class IUnitOfWork:
    """Interface for Unit of Work."""

    async def commit(self) -> None:
        """Commit the transaction."""
        ...

    async def rollback(self) -> None:
        """Rollback the transaction."""
        ...

    def get_repository(self, repository_type: type[T]) -> T:
        """Get repository instance."""
        ...

    def add_entity(self, entity: Any) -> None:
        """Add entity to be tracked."""
        ...

    def add_entities(self, entities: list[Any]) -> None:
        """Add multiple entities to be tracked."""
        ...

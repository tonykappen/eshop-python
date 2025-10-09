"""Commit interceptors for transaction hooks."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Protocol

from app.core.database.session import AsyncSession


class ICommitInterceptor(Protocol):
    """Protocol for commit interceptors."""

    async def before_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Called before commit.
        
        Args:
            session: Database session
            entities: List of entities being committed
        """
        ...

    async def after_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Called after successful commit.
        
        Args:
            session: Database session
            entities: List of entities that were committed
        """
        ...

    async def on_rollback(self, session: AsyncSession, entities: List[Any], error: Exception) -> None:
        """
        Called on rollback.
        
        Args:
            session: Database session
            entities: List of entities that were rolled back
            error: Exception that caused the rollback
        """
        ...


class CommitInterceptorRegistry:
    """Registry for commit interceptors."""

    def __init__(self):
        """Initialize the registry."""
        self._interceptors: List[ICommitInterceptor] = []

    def register(self, interceptor: ICommitInterceptor) -> None:
        """
        Register a commit interceptor.
        
        Args:
            interceptor: Interceptor to register
        """
        self._interceptors.append(interceptor)

    def unregister(self, interceptor: ICommitInterceptor) -> None:
        """
        Unregister a commit interceptor.
        
        Args:
            interceptor: Interceptor to unregister
        """
        if interceptor in self._interceptors:
            self._interceptors.remove(interceptor)

    def get_interceptors(self) -> List[ICommitInterceptor]:
        """
        Get all registered interceptors.
        
        Returns:
            List of registered interceptors
        """
        return self._interceptors.copy()

    async def execute_before_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Execute all before_commit hooks.
        
        Args:
            session: Database session
            entities: List of entities being committed
        """
        for interceptor in self._interceptors:
            try:
                await interceptor.before_commit(session, entities)
            except Exception as e:
                # Log error but don't fail the commit
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in before_commit interceptor: {e}")

    async def execute_after_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Execute all after_commit hooks.
        
        Args:
            session: Database session
            entities: List of entities that were committed
        """
        for interceptor in self._interceptors:
            try:
                await interceptor.after_commit(session, entities)
            except Exception as e:
                # Log error but don't fail the operation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in after_commit interceptor: {e}")

    async def execute_on_rollback(self, session: AsyncSession, entities: List[Any], error: Exception) -> None:
        """
        Execute all on_rollback hooks.
        
        Args:
            session: Database session
            entities: List of entities that were rolled back
            error: Exception that caused the rollback
        """
        for interceptor in self._interceptors:
            try:
                await interceptor.on_rollback(session, entities, error)
            except Exception as e:
                # Log error but don't fail the rollback
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in on_rollback interceptor: {e}")


# Global registry instance
commit_interceptor_registry = CommitInterceptorRegistry()



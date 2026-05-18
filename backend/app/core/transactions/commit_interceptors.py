"""Commit interceptors for transaction hooks."""

from typing import Any, Protocol

from app.core.database.session import AsyncSession
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class ICommitInterceptor(Protocol):
    """Protocol for commit interceptors."""

    is_critical: bool

    async def before_commit(
        self, session: AsyncSession, entities: list[Any]
    ) -> None: ...
    async def after_commit(
        self, session: AsyncSession, entities: list[Any]
    ) -> None: ...
    async def on_rollback(
        self, session: AsyncSession, entities: list[Any], error: Exception
    ) -> None: ...


class CommitInterceptor:
    """Base class for commit interceptors with critical/non-critical distinction."""

    is_critical: bool = False

    async def before_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        pass

    async def after_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        pass

    async def on_rollback(
        self, session: AsyncSession, entities: list[Any], error: Exception
    ) -> None:
        pass


class CommitInterceptorRegistry:
    """Registry for commit interceptors."""

    def __init__(self):
        self._interceptors: list[ICommitInterceptor] = []

    def register(self, interceptor: ICommitInterceptor) -> None:
        self._interceptors.append(interceptor)

    def unregister(self, interceptor: ICommitInterceptor) -> None:
        if interceptor in self._interceptors:
            self._interceptors.remove(interceptor)

    def get_interceptors(self) -> list[ICommitInterceptor]:
        return self._interceptors.copy()

    async def execute_before_commit(
        self, session: AsyncSession, entities: list[Any]
    ) -> None:
        """
        Execute all before_commit hooks.
        Critical interceptors that fail will re-raise, causing transaction rollback.
        Non-critical interceptors log errors and continue.
        """
        for interceptor in self._interceptors:
            try:
                await interceptor.before_commit(session, entities)
            except Exception as e:
                if getattr(interceptor, "is_critical", False):
                    logger.log_error_with_context(
                        "Critical before_commit interceptor failed — aborting transaction",
                        error=e,
                        context={"interceptor": type(interceptor).__name__},
                    )
                    raise
                logger.log_error_with_context(
                    "Non-critical before_commit interceptor failed — continuing",
                    error=e,
                    context={"interceptor": type(interceptor).__name__},
                )

    async def execute_after_commit(
        self, session: AsyncSession, entities: list[Any]
    ) -> None:
        """Execute all after_commit hooks. Failures are logged but never re-raised."""
        for interceptor in self._interceptors:
            try:
                await interceptor.after_commit(session, entities)
            except Exception as e:
                logger.log_error_with_context(
                    "Error in after_commit interceptor",
                    error=e,
                    context={"interceptor": type(interceptor).__name__},
                )

    async def execute_on_rollback(
        self, session: AsyncSession, entities: list[Any], error: Exception
    ) -> None:
        """Execute all on_rollback hooks. Failures are logged but never re-raised."""
        for interceptor in self._interceptors:
            try:
                await interceptor.on_rollback(session, entities, error)
            except Exception as e:
                logger.log_error_with_context(
                    "Error in on_rollback interceptor",
                    error=e,
                    context={"interceptor": type(interceptor).__name__},
                )


commit_interceptor_registry = CommitInterceptorRegistry()

"""Generic commit interceptor implementations."""

from typing import Any

from app.core.context.application_context import RequestContext
from app.core.database.session import AsyncSession
from app.core.logging.base_logger import BaseLogger
from app.core.transactions.commit_interceptors import ICommitInterceptor

logger = BaseLogger(__name__)


class AuditStampInterceptor(ICommitInterceptor):
    """Interceptor for adding audit stamps to entities."""

    def __init__(self, request_context: RequestContext):
        """
        Initialize the interceptor.

        Args:
            request_context: Request context for audit information
        """
        self.request_context = request_context

    async def before_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Add audit stamps before commit.

        Args:
            session: Database session
            entities: List of entities being committed
        """
        current_time = self.request_context.get_metadata("current_time")
        user_id = self.request_context.user_id

        for entity in entities:
            if hasattr(entity, "updated_at"):
                entity.updated_at = current_time

            if hasattr(entity, "updated_by") and user_id:
                entity.updated_by = user_id

            # For new entities, set created_at and created_by
            if hasattr(entity, "created_at") and not entity.created_at:
                entity.created_at = current_time

            if (
                hasattr(entity, "created_by")
                and user_id
                and not hasattr(entity, "created_by")
            ):
                entity.created_by = user_id

    async def after_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Called after successful commit.

        Args:
            session: Database session
            entities: List of entities that were committed
        """
        logger.log_with_context(
            "Audit stamps applied to entities",
            context={"entity_count": len(entities)}
        )

    async def on_rollback(
        self, session: AsyncSession, entities: list[Any], error: Exception
    ) -> None:
        """
        Called on rollback.

        Args:
            session: Database session
            entities: List of entities that were rolled back
            error: Exception that caused the rollback
        """
        logger.log_warning_with_context(
            "Rollback occurred, audit stamps not applied",
            context={"entity_count": len(entities), "error": str(error)}
        )


class CacheInvalidationInterceptor(ICommitInterceptor):
    """Interceptor for cache invalidation after commit."""

    def __init__(self, cache_service: Any = None):
        """
        Initialize the interceptor.

        Args:
            cache_service: Cache service for invalidation
        """
        self.cache_service = cache_service

    async def before_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Called before commit.

        Args:
            session: Database session
            entities: List of entities being committed
        """
        # Nothing to do before commit
        pass

    async def after_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Invalidate cache after successful commit.

        Args:
            session: Database session
            entities: List of entities that were committed
        """
        if not self.cache_service:
            return

        try:
            for entity in entities:
                # Invalidate cache for the entity
                if hasattr(entity, "id"):
                    cache_key = f"entity:{type(entity).__name__}:{entity.id}"
                    await self.cache_service.invalidate(cache_key)

            logger.log_with_context(
                "Cache invalidated for entities",
                context={"entity_count": len(entities)}
            )
        except Exception as e:
            logger.log_error_with_context(
                "Error invalidating cache",
                error=e
            )

    async def on_rollback(
        self, session: AsyncSession, entities: list[Any], error: Exception
    ) -> None:
        """
        Called on rollback.

        Args:
            session: Database session
            entities: List of entities that were rolled back
            error: Exception that caused the rollback
        """
        logger.log_with_context(
            "Rollback occurred, cache not invalidated",
            context={"entity_count": len(entities)}
        )

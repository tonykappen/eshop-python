"""Generic commit interceptor implementations."""

from datetime import UTC, datetime
from typing import Any

from app.core.context.application_context import RequestContext
from app.core.database.session import AsyncSession
from app.core.logging.base_logger import BaseLogger
from app.core.transactions.commit_interceptors import CommitInterceptor

logger = BaseLogger(__name__)


class AuditStampInterceptor(CommitInterceptor):
    """Interceptor for adding audit stamps to entities. Non-critical."""

    is_critical = False

    def __init__(self, request_context: RequestContext):
        self.request_context = request_context

    async def before_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        current_time = self.request_context.get_metadata(
            "current_time"
        ) or datetime.now(UTC).replace(tzinfo=None)
        user_id = self.request_context.user_id

        for entity in entities:
            if hasattr(entity, "updated_at"):
                entity.updated_at = current_time
            if hasattr(entity, "updated_by") and user_id:
                entity.updated_by = user_id
            if hasattr(entity, "created_at") and not entity.created_at:
                entity.created_at = current_time
            if (
                hasattr(entity, "created_by")
                and user_id
                and not getattr(entity, "created_by", None)
            ):
                entity.created_by = user_id

    async def after_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        logger.log_with_context(
            "Audit stamps applied", context={"entity_count": len(entities)}
        )

    async def on_rollback(
        self, session: AsyncSession, entities: list[Any], error: Exception
    ) -> None:
        logger.log_warning_with_context(
            "Rollback — audit stamps not applied",
            context={"entity_count": len(entities), "error": str(error)},
        )


class CacheInvalidationInterceptor(CommitInterceptor):
    """Interceptor for cache invalidation after commit. Non-critical."""

    is_critical = False

    def __init__(self, cache_service: Any = None):
        self.cache_service = cache_service

    async def after_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        if not self.cache_service:
            return

        try:
            for entity in entities:
                if hasattr(entity, "id"):
                    cache_key = f"entity:{type(entity).__name__}:{entity.id}"
                    await self.cache_service.invalidate(cache_key)

            logger.log_with_context(
                "Cache invalidated for entities",
                context={"entity_count": len(entities)},
            )
        except Exception as e:
            logger.log_error_with_context("Error invalidating cache", error=e)

    async def on_rollback(
        self, session: AsyncSession, entities: list[Any], error: Exception
    ) -> None:
        logger.log_with_context(
            "Rollback — cache not invalidated",
            context={"entity_count": len(entities)},
        )

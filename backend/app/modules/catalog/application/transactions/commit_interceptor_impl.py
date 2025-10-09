"""Concrete commit interceptor implementations."""

import logging
from typing import Any, List

from app.core.database.session import AsyncSession
from app.modules.catalog.application.context.request_context import RequestContext
from app.modules.catalog.application.transactions.commit_interceptors import ICommitInterceptor

logger = logging.getLogger(__name__)


class AuditStampInterceptor(ICommitInterceptor):
    """Interceptor for adding audit stamps to entities."""

    def __init__(self, request_context: RequestContext):
        """
        Initialize the interceptor.
        
        Args:
            request_context: Request context for audit information
        """
        self.request_context = request_context

    async def before_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Add audit stamps before commit.
        
        Args:
            session: Database session
            entities: List of entities being committed
        """
        current_time = self.request_context.get_metadata("current_time")
        user_id = self.request_context.user_id
        
        for entity in entities:
            if hasattr(entity, 'updated_at'):
                entity.updated_at = current_time
                
            if hasattr(entity, 'updated_by') and user_id:
                entity.updated_by = user_id
                
            # For new entities, set created_at and created_by
            if hasattr(entity, 'created_at') and not entity.created_at:
                entity.created_at = current_time
                
            if hasattr(entity, 'created_by') and user_id and not hasattr(entity, 'created_by'):
                entity.created_by = user_id

    async def after_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Called after successful commit.
        
        Args:
            session: Database session
            entities: List of entities that were committed
        """
        logger.info(f"Audit stamps applied to {len(entities)} entities")

    async def on_rollback(self, session: AsyncSession, entities: List[Any], error: Exception) -> None:
        """
        Called on rollback.
        
        Args:
            session: Database session
            entities: List of entities that were rolled back
            error: Exception that caused the rollback
        """
        logger.warning(f"Rollback occurred, audit stamps not applied to {len(entities)} entities: {error}")


class CacheInvalidationInterceptor(ICommitInterceptor):
    """Interceptor for cache invalidation after commit."""

    def __init__(self, cache_service: Any = None):
        """
        Initialize the interceptor.
        
        Args:
            cache_service: Cache service for invalidation
        """
        self.cache_service = cache_service

    async def before_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Called before commit.
        
        Args:
            session: Database session
            entities: List of entities being committed
        """
        # Nothing to do before commit
        pass

    async def after_commit(self, session: AsyncSession, entities: List[Any]) -> None:
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
                if hasattr(entity, 'id'):
                    cache_key = f"entity:{type(entity).__name__}:{entity.id}"
                    await self.cache_service.invalidate(cache_key)
                    
            logger.info(f"Cache invalidated for {len(entities)} entities")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

    async def on_rollback(self, session: AsyncSession, entities: List[Any], error: Exception) -> None:
        """
        Called on rollback.
        
        Args:
            session: Database session
            entities: List of entities that were rolled back
            error: Exception that caused the rollback
        """
        logger.info(f"Rollback occurred, cache not invalidated for {len(entities)} entities")


class DomainEventPublisherInterceptor(ICommitInterceptor):
    """Interceptor for publishing domain events after commit."""

    def __init__(self, event_publisher: Any = None):
        """
        Initialize the interceptor.
        
        Args:
            event_publisher: Event publisher service
        """
        self.event_publisher = event_publisher

    async def before_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Called before commit.
        
        Args:
            session: Database session
            entities: List of entities being committed
        """
        # Nothing to do before commit
        pass

    async def after_commit(self, session: AsyncSession, entities: List[Any]) -> None:
        """
        Publish domain events after successful commit.
        
        Args:
            session: Database session
            entities: List of entities that were committed
        """
        if not self.event_publisher:
            return
            
        try:
            for entity in entities:
                # Publish domain events for the entity
                if hasattr(entity, 'domain_events'):
                    for event in entity.domain_events:
                        await self.event_publisher.publish(event)
                        
            logger.info(f"Domain events published for {len(entities)} entities")
        except Exception as e:
            logger.error(f"Error publishing domain events: {e}")

    async def on_rollback(self, session: AsyncSession, entities: List[Any], error: Exception) -> None:
        """
        Called on rollback.
        
        Args:
            session: Database session
            entities: List of entities that were rolled back
            error: Exception that caused the rollback
        """
        logger.info(f"Rollback occurred, domain events not published for {len(entities)} entities")



"""Concrete commit interceptor implementations."""

import logging
from typing import Any

from app.core.database.session import AsyncSession
from app.modules.catalog.application.context.request_context import RequestContext
from app.modules.catalog.application.transactions.commit_interceptors import (
    ICommitInterceptor,
)

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
        logger.info(f"Audit stamps applied to {len(entities)} entities")

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
        logger.warning(
            f"Rollback occurred, audit stamps not applied to {len(entities)} entities: {error}"
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

            logger.info(f"Cache invalidated for {len(entities)} entities")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

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
        logger.info(
            f"Rollback occurred, cache not invalidated for {len(entities)} entities"
        )


class OutboxEnqueuerInterceptor(ICommitInterceptor):
    """Interceptor for enqueuing outbox messages before commit (inside transaction)."""

    def __init__(self):
        """Initialize the outbox enqueuer interceptor."""
        pass

    async def before_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Enqueue outbox messages for domain events that require reliable delivery.

        This runs INSIDE the transaction to ensure atomicity.

        Args:
            session: Database session (part of active transaction)
            entities: List of entities being committed
        """
        try:
            # Import here to avoid circular dependencies
            from app.core.messaging.outbox.outbox_service import OutboxService
            from app.modules.catalog.application.outbound_outbox_enqueuers.products.product_deleted_outbox_enqueuer import (
                ProductDeletedOutboxEnqueuer,
            )
            from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import (
                ProductDeletedDomainEvent,
            )
            from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import (
                OutboxORM,
            )

            # Collect domain events from entities
            domain_events = []
            for entity in entities:
                if hasattr(entity, "domain_events") and entity.domain_events:
                    domain_events.extend(entity.domain_events)
                    logger.debug(
                        f"Found {len(entity.domain_events)} domain events on entity {type(entity).__name__}: "
                        f"{[e.event_type for e in entity.domain_events]}"
                    )

            if not domain_events:
                logger.debug("No domain events found in entities, skipping outbox enqueuing")
                return

            logger.info(
                f"Collected {len(domain_events)} domain events for outbox processing: "
                f"{[e.event_type for e in domain_events]}"
            )

            # Create outbox service with current session (inside transaction)
            outbox_service = OutboxService(session, outbox_orm_class=OutboxORM)

            # Process events that require outbox (reliable delivery)
            for event in domain_events:
                if isinstance(event, ProductDeletedDomainEvent):
                    enqueuer = ProductDeletedOutboxEnqueuer(outbox_service)
                    await enqueuer.enqueue(event)
                    logger.debug(
                        f"Enqueued ProductDeleted event to outbox: {event.product_id}"
                    )

            logger.info(
                f"Outbox enqueuing completed for {len(domain_events)} domain events"
            )

        except Exception as e:
            logger.error(
                f"Error enqueuing outbox messages: {e}",
                exc_info=True,
            )
            # Re-raise to ensure transaction rollback on failure
            raise

    async def after_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Called after successful commit.

        Args:
            session: Database session
            entities: List of entities that were committed
        """
        # Nothing to do after commit
        pass

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
        logger.info(
            f"Rollback occurred, outbox messages not enqueued for {len(entities)} entities"
        )


class DomainEventPublisherInterceptor(ICommitInterceptor):
    """
    Interceptor for dispatching domain events after commit (two-phase processing).

    Phase 1 (before_commit): Outbox enqueuing handled by OutboxEnqueuerInterceptor
    Phase 2 (after_commit): Internal reactions + direct publishers
    """

    def __init__(self, event_publisher: Any = None, domain_event_dispatcher: Any = None):
        """
        Initialize the interceptor.

        Args:
            event_publisher: Event publisher service (for direct publishers)
            domain_event_dispatcher: Domain event dispatcher (for internal handlers)
        """
        self.event_publisher = event_publisher
        self.domain_event_dispatcher = domain_event_dispatcher

    async def before_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Called before commit.

        Args:
            session: Database session
            entities: List of entities being committed
        """
        # Nothing to do before commit - outbox enqueuing is handled by OutboxEnqueuerInterceptor
        pass

    async def after_commit(self, session: AsyncSession, entities: list[Any]) -> None:
        """
        Dispatch domain events after successful commit (two-phase processing).

        This handles:
        1. Internal domain event handlers (cache, metrics)
        2. Direct publishers (best-effort events like ProductPriceChanged)

        Args:
            session: Database session
            entities: List of entities that were committed
        """
        try:
            # Collect domain events from entities
            domain_events = []
            for entity in entities:
                if hasattr(entity, "domain_events") and entity.domain_events:
                    domain_events.extend(entity.domain_events)
                    logger.debug(
                        f"Collected {len(entity.domain_events)} domain events from entity {type(entity).__name__}"
                    )

            if not domain_events:
                logger.debug("No domain events to dispatch after commit")
                return

            logger.info(
                f"Dispatching {len(domain_events)} domain events after commit: {[type(e).__name__ for e in domain_events]}"
            )

            # Dispatch to domain event dispatcher (internal handlers)
            if self.domain_event_dispatcher:
                for event in domain_events:
                    await self.domain_event_dispatcher.dispatch(event)

            # Handle direct publishing for best-effort events (after commit)
            if self.event_publisher:
                from app.modules.catalog.application.outbound_direct_publishers.products.product_price_changed_direct_publisher import (
                    ProductPriceChangedDirectPublisher,
                )
                from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import (
                    ProductPriceChangedDomainEvent,
                )

                for event in domain_events:
                    if isinstance(event, ProductPriceChangedDomainEvent):
                        try:
                            publisher = ProductPriceChangedDirectPublisher(self.event_publisher)
                            await publisher.publish(event)
                            logger.debug(
                                f"Directly published ProductPriceChanged event: {event.product_id}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error in direct publish for ProductPriceChanged: {e}",
                                exc_info=True,
                            )
                            # Don't re-raise - best-effort delivery

            logger.info(
                f"Domain events dispatched for {len(entities)} entities ({len(domain_events)} events)"
            )
        except Exception as e:
            logger.error(f"Error dispatching domain events: {e}", exc_info=True)
            # Don't re-raise - domain event dispatch failures shouldn't break the commit

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
        logger.info(
            f"Rollback occurred, domain events not dispatched for {len(entities)} entities"
        )

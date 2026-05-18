"""Catalog-specific commit interceptor implementations."""

from typing import Any

from app.core.database.session import AsyncSession
from app.core.logging.base_logger import BaseLogger
from app.core.transactions.commit_interceptors import CommitInterceptor

logger = BaseLogger(__name__)


class OutboxEnqueuerInterceptor(CommitInterceptor):
    """Interceptor for enqueuing outbox messages before commit (inside transaction).
    Marked critical — failure aborts the transaction.
    """

    is_critical = True

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
            from app.modules.catalog.application.outbound_outbox_enqueuers.products.product_deleted_outbox_enqueuer import \
                ProductDeletedOutboxEnqueuer
            from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import \
                ProductDeletedDomainEvent
            from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import \
                OutboxORM

            # Collect domain events from entities
            domain_events = []
            for entity in entities:
                if hasattr(entity, "domain_events") and entity.domain_events:
                    domain_events.extend(entity.domain_events)
                    logger.log_debug_with_context(
                        f"Found {len(entity.domain_events)} domain events on entity {type(entity).__name__}",
                        context={
                            "event_types": [e.event_type for e in entity.domain_events]
                        },
                    )

            if not domain_events:
                logger.log_debug_with_context(
                    "No domain events found in entities, skipping outbox enqueuing"
                )
                return

            logger.log_with_context(
                f"Collected {len(domain_events)} domain events for outbox processing",
                "info",
                context={
                    "event_types": [e.event_type for e in domain_events],
                    "count": len(domain_events),
                },
            )

            # Create outbox service with current session (inside transaction)
            outbox_service = OutboxService(session, outbox_orm_class=OutboxORM)

            # Process events that require outbox (reliable delivery)
            for event in domain_events:
                if isinstance(event, ProductDeletedDomainEvent):
                    enqueuer = ProductDeletedOutboxEnqueuer(outbox_service)
                    await enqueuer.enqueue(event)
                    logger.log_debug_with_context(
                        "Enqueued ProductDeleted event to outbox",
                        context={"product_id": str(event.product_id)},
                    )

            logger.log_with_context(
                f"Outbox enqueuing completed for {len(domain_events)} domain events",
                "info",
                context={"event_count": len(domain_events)},
            )

        except Exception as e:
            logger.log_exception_detailed(
                "Error enqueuing outbox messages",
                exception=e,
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
        logger.log_with_context(
            f"Rollback occurred, outbox messages not enqueued for {len(entities)} entities",
            "info",
            context={"entity_count": len(entities)},
        )


class DomainEventPublisherInterceptor(CommitInterceptor):
    """
    Interceptor for dispatching domain events after commit (two-phase processing).
    Non-critical — failures in after_commit dispatch should not break anything.

    Phase 1 (before_commit): Outbox enqueuing handled by OutboxEnqueuerInterceptor
    Phase 2 (after_commit): Internal reactions + direct publishers
    """

    is_critical = False

    def __init__(self, message_bus: Any = None, domain_event_dispatcher: Any = None):
        self.message_bus = message_bus
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
                    logger.log_debug_with_context(
                        f"Collected {len(entity.domain_events)} domain events from entity {type(entity).__name__}",
                        context={
                            "entity_type": type(entity).__name__,
                            "event_count": len(entity.domain_events),
                        },
                    )

            if not domain_events:
                logger.log_debug_with_context(
                    "No domain events to dispatch after commit"
                )
                return

            logger.log_with_context(
                f"Dispatching {len(domain_events)} domain events after commit",
                "info",
                context={
                    "event_types": [type(e).__name__ for e in domain_events],
                    "count": len(domain_events),
                },
            )

            # Dispatch to domain event dispatcher (internal handlers)
            if self.domain_event_dispatcher:
                for event in domain_events:
                    await self.domain_event_dispatcher.dispatch(event)

            # Handle direct publishing for best-effort events (after commit)
            if self.message_bus:
                from app.modules.catalog.application.outbound_direct_publishers.products.product_price_changed_direct_publisher import \
                    ProductPriceChangedDirectPublisher
                from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import \
                    ProductPriceChangedDomainEvent

                for event in domain_events:
                    if isinstance(event, ProductPriceChangedDomainEvent):
                        try:
                            publisher = ProductPriceChangedDirectPublisher(
                                self.message_bus
                            )
                            await publisher.publish(event)
                            logger.log_debug_with_context(
                                "Directly published ProductPriceChanged event",
                                context={"product_id": str(event.product_id)},
                            )
                        except Exception as e:
                            logger.log_exception_detailed(
                                "Error in direct publish for ProductPriceChanged",
                                exception=e,
                            )
                            # Don't re-raise - best-effort delivery

            logger.log_with_context(
                f"Domain events dispatched for {len(entities)} entities ({len(domain_events)} events)",
                "info",
                context={
                    "entity_count": len(entities),
                    "event_count": len(domain_events),
                },
            )
        except Exception as e:
            logger.log_exception_detailed(
                "Error dispatching domain events", exception=e
            )
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
        logger.log_with_context(
            f"Rollback occurred, domain events not dispatched for {len(entities)} entities",
            "info",
            context={"entity_count": len(entities)},
        )

"""Legacy bus handler for ProductDeletedDomainEvent - now handled by OutboxEnqueuerInterceptor.

This handler is kept for backward compatibility but is no longer used.
Outbox enqueuing now happens in OutboxEnqueuerInterceptor (before commit).
Internal reactions are handled by ProductDeletedDomainEventHandler (after commit).
"""

import logging
from typing import Any

from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import (
    ProductDeletedDomainEvent,
)

logger = logging.getLogger(__name__)


class ProductDeletedDomainEventBusHandler:
    """
    Legacy bus handler for ProductDeletedDomainEvent.

    NOTE: This handler is deprecated. Outbox enqueuing is now handled by
    OutboxEnqueuerInterceptor in the before_commit hook. This handler is kept
    for backward compatibility but should not be registered.
    """

    def __init__(self, event_publisher: Any = None, outbox_service: Any = None):
        """
        Initialize the handler.

        Args:
            event_publisher: Event publisher service (not used)
            outbox_service: Outbox service (not used)
        """
        self.event_publisher = event_publisher
        self.outbox_service = outbox_service
        logger.warning(
            "ProductDeletedDomainEventBusHandler is deprecated. "
            "Use OutboxEnqueuerInterceptor instead."
        )

    async def handle(self, domain_event: ProductDeletedDomainEvent) -> None:
        """
        Handle product deleted domain event (deprecated).

        This method is no longer called. Outbox enqueuing happens in
        OutboxEnqueuerInterceptor before commit.

        Args:
            domain_event: Product deleted domain event
        """
        logger.warning(
            f"ProductDeletedDomainEventBusHandler.handle() called for product {domain_event.product_id}. "
            "This handler is deprecated and should not be used."
        )
        # Do nothing - outbox enqueuing is handled by interceptor

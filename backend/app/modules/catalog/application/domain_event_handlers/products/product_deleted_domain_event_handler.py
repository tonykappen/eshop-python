"""Internal handler for ProductDeletedDomainEvent (cache invalidation, metrics)."""

import logging

from app.core.domain.events import DomainEventHandler
from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import (
    ProductDeletedDomainEvent,
)

logger = logging.getLogger(__name__)


class ProductDeletedDomainEventHandler(DomainEventHandler[ProductDeletedDomainEvent]):
    """Internal handler for product deleted domain events (cache, metrics)."""

    async def handle(self, event: ProductDeletedDomainEvent) -> None:
        """
        Handle product deleted domain event for internal reactions.

        This handler only handles internal reactions (cache, metrics).
        Outbound messaging is handled by OutboxEnqueuerInterceptor (before commit).

        Args:
            event: The product deleted domain event
        """
        logger.info(
            f"Processing internal reactions for product deleted: {event.product_id}"
        )

        # Internal reactions (no integration event):
        # 1. Invalidate cache
        # 2. Update metrics
        # 3. Update internal read models

        try:
            # Invalidate cache
            # await self._invalidate_cache(event)

            # Update metrics
            # await self._update_metrics(event)

            logger.info(f"Internal reactions completed for product {event.product_id}")
        except Exception as e:
            logger.error(f"Error in internal reactions for product deleted: {e}")

    async def _invalidate_cache(self, event: ProductDeletedDomainEvent) -> None:
        """Invalidate cache for deleted product."""
        # Implementation would go here
        pass

    async def _update_metrics(self, event: ProductDeletedDomainEvent) -> None:
        """Update metrics for product deletion."""
        # Implementation would go here
        pass

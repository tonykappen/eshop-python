"""Delegates ProductPriceChangedDomainEvent to direct publisher (best-effort delivery)."""

import logging
from typing import Any

from app.modules.catalog.application.outbound_direct_publishers.products.product_price_changed_direct_publisher import (
    ProductPriceChangedDirectPublisher,
)
from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import (
    ProductPriceChangedDomainEvent,
)

logger = logging.getLogger(__name__)


class ProductPriceChangedDomainEventBusHandler:
    """Delegates ProductPriceChangedDomainEvent to direct publisher (best-effort delivery)."""

    def __init__(self, event_publisher: Any = None):
        """
        Initialize the handler.

        Args:
            event_publisher: Event publisher service for direct publishing
        """
        self.event_publisher = event_publisher
        self._direct_publisher: ProductPriceChangedDirectPublisher | None = None

    async def handle(self, domain_event: ProductPriceChangedDomainEvent) -> None:
        """
        Handle product price changed domain event and delegate to direct publisher.

        This is called AFTER commit for best-effort delivery.

        Args:
            domain_event: Product price changed domain event
        """
        logger.info(
            f"Delegating price changed domain event to direct publisher for product {domain_event.product_id}"
        )

        if not self.event_publisher:
            logger.warning(
                "No event publisher configured, product price changed integration event not published"
            )
            return

        try:
            # Create direct publisher and delegate
            if self._direct_publisher is None:
                self._direct_publisher = ProductPriceChangedDirectPublisher(
                    self.event_publisher
                )

            await self._direct_publisher.publish(domain_event)

        except Exception as e:
            logger.error(
                f"Error publishing product price changed integration event: {e}",
                exc_info=True,
            )
            # Don't re-raise - best-effort delivery means failures are acceptable

"""OrderCreatedDomainEventHandler - handles OrderCreatedDomainEvent."""

import logging

from app.core.domain.events import DomainEventHandler
from app.modules.ordering.domain.domain_events.orders.order_created_domain_event import \
    OrderCreatedDomainEvent

logger = logging.getLogger(__name__)


class OrderCreatedDomainEventHandler(DomainEventHandler[OrderCreatedDomainEvent]):
    """
    Handles OrderCreatedDomainEvent for internal reactions (metrics/cache).
    Matches .NET OrderCreatedEventHandler.
    """

    async def handle(self, event: OrderCreatedDomainEvent) -> None:
        """
        Handle the domain event - matches .NET Handle method.

        Args:
            event: The OrderCreatedDomainEvent
        """
        logger.info(
            "Domain Event handled: %s for OrderId: %s",
            event.event_type,
            event.order_id,
        )
        # Additional internal logic (metrics, cache warm-up) can be added here

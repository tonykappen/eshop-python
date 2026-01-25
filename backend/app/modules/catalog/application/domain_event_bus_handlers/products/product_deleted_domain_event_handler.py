"""Converts ProductDeletedDomainEvent → ProductDeletedIntegrationEvent + Outbox Pattern."""

import logging
from typing import Any
from uuid import UUID

from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import (
    ProductDeletedDomainEvent,
)

logger = logging.getLogger(__name__)


class ProductDeletedDomainEventBusHandler:
    """Converts ProductDeletedDomainEvent to ProductDeletedIntegrationEvent and writes to Outbox."""

    def __init__(self, event_publisher: Any = None, outbox_service: Any = None):
        """
        Initialize the handler.
        
        Args:
            event_publisher: Event publisher service
            outbox_service: Outbox service for reliable messaging
        """
        self.event_publisher = event_publisher
        self.outbox_service = outbox_service

    async def handle(self, domain_event: ProductDeletedDomainEvent) -> None:
        """
        Handle product deleted domain event and publish integration event via outbox.
        
        Args:
            domain_event: Product deleted domain event
        """
        logger.info(f"Converting deleted domain event to integration event for product {domain_event.product_id}")
        
        try:
            # Create integration event
            # Note: We need to create ProductDeletedIntegrationEvent
            # For now, we'll use a placeholder structure
            integration_event_data = {
                "event_type": "product.deleted.v1",
                "product_id": str(domain_event.product_id),
                "product_name": domain_event.product_name,
                "product_sku": domain_event.product_sku,
                "deleted_at": domain_event.occurred_at.isoformat() if hasattr(domain_event, 'occurred_at') else None,
                "metadata": {
                    "domain_event_id": str(domain_event.id),
                    "domain_event_type": domain_event.event_type,
                    "domain_event_version": str(domain_event.version),
                },
            }
            
            # Write to outbox for reliable delivery (required by blueprint)
            if self.outbox_service:
                await self.outbox_service.write_integration_event(integration_event_data)
                logger.info(f"Written product deleted integration event to outbox for product {domain_event.product_id}")
            elif self.event_publisher:
                # Fallback to direct publish (less reliable)
                await self.event_publisher.publish(integration_event_data)
                logger.info(f"Published product deleted integration event for product {domain_event.product_id}")
            else:
                logger.warning("No event publisher or outbox service configured, integration event not published")
                
        except Exception as e:
            logger.error(f"Error publishing product deleted integration event: {e}")
            # Don't re-raise the exception to avoid breaking the domain event processing













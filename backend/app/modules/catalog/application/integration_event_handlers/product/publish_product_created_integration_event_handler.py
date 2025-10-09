"""Handler for publishing product created integration events."""

import logging
from typing import Any

from app.modules.catalog.application.integration_events.product.product_created_integration_event_v1 import (
    ProductCreatedIntegrationEventV1,
)
from app.modules.catalog.domain.product.domain_events.product_created_domain_event import (
    ProductCreatedDomainEvent,
)

logger = logging.getLogger(__name__)


class PublishProductCreatedIntegrationEventHandler:
    """Handler for publishing product created integration events."""

    def __init__(self, event_publisher: Any = None):
        """
        Initialize the handler.
        
        Args:
            event_publisher: Event publisher service
        """
        self.event_publisher = event_publisher

    async def handle(self, domain_event: ProductCreatedDomainEvent) -> None:
        """
        Handle product created domain event and publish integration event.
        
        Args:
            domain_event: Product created domain event
        """
        logger.info(f"Handling product created domain event for product {domain_event.product_id}")
        
        try:
            # Create integration event
            integration_event = ProductCreatedIntegrationEventV1.create(
                product_id=domain_event.product_id,
                product_name=domain_event.product_name,
                product_sku=domain_event.product_sku,
                product_categories=domain_event.product.category,
                product_description=domain_event.product.description,
                product_image_file=domain_event.product.image_file,
                product_price_amount=float(domain_event.product.price.amount),
                product_price_currency=domain_event.product.price.currency,
                metadata={
                    "domain_event_id": str(domain_event.id),
                    "domain_event_type": domain_event.event_type,
                    "domain_event_version": str(domain_event.version),
                },
            )
            
            # Publish integration event
            if self.event_publisher:
                await self.event_publisher.publish(integration_event)
                logger.info(f"Published product created integration event {integration_event.event_id}")
            else:
                logger.warning("No event publisher configured, integration event not published")
                
        except Exception as e:
            logger.error(f"Error publishing product created integration event: {e}")
            # Don't re-raise the exception to avoid breaking the domain event processing



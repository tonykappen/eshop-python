"""Converts ProductPriceChangedDomainEvent → ProductPriceChangedIntegrationEvent."""

import logging
from typing import Any

from app.modules.catalog.application.integration_events.products.product_price_changed_integration_event_v1 import (
    ProductPriceChangedIntegrationEventV1,
)
from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import (
    ProductPriceChangedDomainEvent,
)

logger = logging.getLogger(__name__)


class ProductPriceChangedDomainEventBusHandler:
    """Converts ProductPriceChangedDomainEvent to ProductPriceChangedIntegrationEvent."""

    def __init__(self, event_publisher: Any = None, outbox_service: Any = None):
        """
        Initialize the handler.
        
        Args:
            event_publisher: Event publisher service
            outbox_service: Outbox service for reliable messaging
        """
        self.event_publisher = event_publisher
        self.outbox_service = outbox_service

    async def handle(self, domain_event: ProductPriceChangedDomainEvent) -> None:
        """
        Handle product price changed domain event and publish integration event.
        
        Args:
            domain_event: Product price changed domain event
        """
        logger.info(f"Converting price changed domain event to integration event for product {domain_event.product_id}")
        
        try:
            # Get old and new prices from the product
            # Note: The domain event should ideally contain old_price, but for now we'll extract from product
            product = domain_event.product
            new_price_amount = float(product.price.amount)
            
            # Create integration event
            # Note: We need old_price from somewhere - this should ideally be in the domain event
            # For now, we'll use a placeholder - in a real implementation, the domain event should include old_price
            integration_event = ProductPriceChangedIntegrationEventV1.create(
                product_id=domain_event.product_id,
                product_name=domain_event.product_name,
                product_sku=domain_event.product_sku,
                old_price_amount=0.0,  # TODO: Domain event should include old_price
                new_price_amount=new_price_amount,
                price_currency=product.price.currency,
                metadata={
                    "domain_event_id": str(domain_event.id),
                    "domain_event_type": domain_event.event_type,
                    "domain_event_version": str(domain_event.version),
                },
            )
            
            # Publish integration event via outbox pattern for reliability
            if self.outbox_service:
                # Write to outbox for reliable delivery
                await self.outbox_service.write_integration_event(integration_event)
                logger.info(f"Written price changed integration event to outbox: {integration_event.event_id}")
            elif self.event_publisher:
                # Direct publish (less reliable)
                await self.event_publisher.publish(integration_event)
                logger.info(f"Published product price changed integration event {integration_event.event_id}")
            else:
                logger.warning("No event publisher or outbox service configured, integration event not published")
                
        except Exception as e:
            logger.error(f"Error publishing product price changed integration event: {e}")
            # Don't re-raise the exception to avoid breaking the domain event processing













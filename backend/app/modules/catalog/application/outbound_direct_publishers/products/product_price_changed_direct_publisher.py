"""Direct publisher for ProductPriceChanged integration event (best-effort delivery)."""

from app.core.logging.base_logger import BaseLogger
from app.core.messaging.bus import IMessageBus
from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import \
    ProductPriceChangedIntegrationEventV1
from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import \
    ProductPriceChangedDomainEvent

logger = BaseLogger(__name__)


class ProductPriceChangedDirectPublisher:
    """Publishes ProductPriceChanged integration event directly to message broker (best-effort)."""

    def __init__(self, message_bus: IMessageBus):
        """
        Initialize the direct publisher.

        Args:
            message_bus: Message bus for direct publishing
        """
        self.message_bus = message_bus

    async def publish(self, domain_event: ProductPriceChangedDomainEvent) -> None:
        """
        Publish ProductPriceChanged integration event directly to message broker.

        This is called AFTER commit for best-effort delivery.
        If publish fails, event is lost (consumers can reconcile via API).

        Args:
            domain_event: Product price changed domain event
        """
        logger.log_with_context(
            "Publishing product price changed integration event",
            context={"product_id": str(domain_event.product_id)},
        )

        try:
            # Get old and new prices from the domain event
            product = domain_event.product
            new_price_amount = float(product.price.amount)

            # Get old price from domain event (now included in the event)
            old_price_amount = 0.0
            if domain_event.old_price:
                old_price_amount = float(domain_event.old_price.amount)
            else:
                logger.log_warning_with_context(
                    "Old price not available in domain event, using 0.0",
                    context={"product_id": str(domain_event.product_id)},
                )

            # Create integration event
            integration_event = ProductPriceChangedIntegrationEventV1.create(
                product_id=domain_event.product_id,
                product_name=domain_event.product_name,
                product_sku=domain_event.product_sku,
                old_price_amount=old_price_amount,
                new_price_amount=new_price_amount,
                price_currency=product.price.currency,
                metadata={
                    "domain_event_id": str(domain_event.event_id),
                    "domain_event_type": domain_event.event_type,
                    "domain_event_version": str(
                        getattr(domain_event, "version", "1.0")
                    ),
                },
            )

            # Publish directly to message broker (best-effort)
            # Routing key matches contract event_type (product.price_changed.v1) for bindings/observability
            await self.message_bus.publish(
                integration_event.to_dict(),
                topic=integration_event.event_type,
                exchange="catalog.events",
            )
            integration_event_id = str(integration_event.event_id)

            logger.log_with_context(
                "Successfully published product price changed integration event",
                context={
                    "product_id": str(domain_event.product_id),
                    "old_price": old_price_amount,
                    "new_price": new_price_amount,
                    "event_id": integration_event_id,
                },
            )

        except Exception as e:
            logger.log_exception_detailed(
                "Error publishing product price changed integration event", exception=e
            )
            # Don't re-raise - best-effort delivery means failures are acceptable
            # Consumers can reconcile state via get_product_by_id API

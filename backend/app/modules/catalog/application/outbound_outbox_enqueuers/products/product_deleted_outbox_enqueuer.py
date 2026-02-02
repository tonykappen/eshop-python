"""Outbox enqueuer for ProductDeleted integration event (reliable delivery)."""

from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.messaging.outbox.outbox_service import IOutboxService
from app.modules.catalog.contracts.products.integration_events.v1.product_deleted_integration_event import (
    ProductDeletedIntegrationEvent,
)
from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import (
    ProductDeletedDomainEvent,
)

logger = BaseLogger(__name__)


class ProductDeletedOutboxEnqueuer:
    """Enqueues ProductDeleted integration event to outbox for reliable delivery."""

    def __init__(self, outbox_service: IOutboxService):
        """
        Initialize the outbox enqueuer.

        Args:
            outbox_service: Outbox service for writing events (must be within transaction)
        """
        self.outbox_service = outbox_service

    async def enqueue(self, domain_event: ProductDeletedDomainEvent) -> None:
        """
        Enqueue ProductDeleted integration event to outbox.

        This must be called INSIDE the transaction to ensure atomicity.

        Args:
            domain_event: Product deleted domain event
        """
        logger.log_with_context(
            "Enqueuing product deleted integration event to outbox",
            context={"product_id": str(domain_event.product_id)}
        )

        try:
            # Map domain event to integration event contract
            integration_event = ProductDeletedIntegrationEvent.create(
                product_id=domain_event.product_id,
                product_name=domain_event.product_name,
                product_sku=domain_event.product_sku,
                deleted_at=domain_event.product.deleted_at if hasattr(domain_event.product, 'deleted_at') else None,
                deletion_reason=domain_event.product.deletion_reason if hasattr(domain_event.product, 'deletion_reason') else None,
                metadata={
                    "domain_event_id": str(domain_event.event_id),
                    "domain_event_type": domain_event.event_type,
                    "domain_event_version": str(getattr(domain_event, 'version', '1.0')),
                },
            )

            # Write to outbox (inside transaction)
            await self.outbox_service.write_integration_event(integration_event)

            logger.log_with_context(
                "Successfully enqueued product deleted integration event to outbox",
                context={"event_id": str(integration_event.event_id)}
            )

        except Exception as e:
            logger.log_exception_detailed(
                "Error enqueuing product deleted integration event to outbox",
                exception=e
            )
            # Re-raise to ensure transaction rollback on failure
            raise

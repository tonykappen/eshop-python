"""Handler for reacting to stock adjusted integration events."""

import logging
from typing import Any

from app.modules.catalog.application.integration_events.inventory.stock_adjusted_integration_event_v1 import (
    StockAdjustedIntegrationEventV1,
)

logger = logging.getLogger(__name__)


class ReactToStockAdjustedIntegrationEventHandler:
    """Handler for reacting to stock adjusted integration events."""

    def __init__(self, notification_service: Any = None, analytics_service: Any = None):
        """
        Initialize the handler.

        Args:
            notification_service: Notification service
            analytics_service: Analytics service
        """
        self.notification_service = notification_service
        self.analytics_service = analytics_service

    async def handle(self, integration_event: StockAdjustedIntegrationEventV1) -> None:
        """
        Handle stock adjusted integration event.

        Args:
            integration_event: Stock adjusted integration event
        """
        logger.info(
            f"Handling stock adjusted integration event for product {integration_event.product_id}"
        )

        try:
            # Update analytics
            if self.analytics_service:
                await self._update_analytics(integration_event)

            # Send notifications if needed
            if self.notification_service:
                await self._send_notifications(integration_event)

            logger.info(
                f"Successfully processed stock adjusted integration event {integration_event.event_id}"
            )

        except Exception as e:
            logger.error(f"Error processing stock adjusted integration event: {e}")
            # Don't re-raise the exception to avoid breaking the event processing

    async def _update_analytics(self, event: StockAdjustedIntegrationEventV1) -> None:
        """
        Update analytics with stock adjustment data.

        Args:
            event: Stock adjusted integration event
        """
        try:
            # Update inventory analytics
            analytics_data = {
                "product_id": str(event.product_id),
                "product_sku": event.product_sku,
                "adjustment": event.adjustment,
                "old_quantity": event.old_quantity,
                "new_quantity": event.new_quantity,
                "is_stock_increase": event.is_stock_increase,
                "is_stock_decrease": event.is_stock_decrease,
                "is_low_stock": event.is_low_stock,
                "is_out_of_stock": event.is_out_of_stock,
                "timestamp": event.occurred_at.isoformat(),
            }

            await self.analytics_service.record_inventory_adjustment(analytics_data)
            logger.debug(f"Updated analytics for stock adjustment: {event.product_sku}")

        except Exception as e:
            logger.error(f"Error updating analytics for stock adjustment: {e}")

    async def _send_notifications(self, event: StockAdjustedIntegrationEventV1) -> None:
        """
        Send notifications for stock adjustments.

        Args:
            event: Stock adjusted integration event
        """
        try:
            # Send low stock notification
            if event.is_low_stock:
                await self.notification_service.send_low_stock_alert(
                    product_id=event.product_id,
                    product_name=event.product_name,
                    product_sku=event.product_sku,
                    current_quantity=event.new_quantity,
                )
                logger.info(f"Sent low stock alert for product {event.product_sku}")

            # Send out of stock notification
            if event.is_out_of_stock:
                await self.notification_service.send_out_of_stock_alert(
                    product_id=event.product_id,
                    product_name=event.product_name,
                    product_sku=event.product_sku,
                )
                logger.info(f"Sent out of stock alert for product {event.product_sku}")

            # Send stock increase notification (for restocking)
            if event.is_stock_increase and event.old_quantity == 0:
                await self.notification_service.send_restocked_alert(
                    product_id=event.product_id,
                    product_name=event.product_name,
                    product_sku=event.product_sku,
                    new_quantity=event.new_quantity,
                )
                logger.info(f"Sent restocked alert for product {event.product_sku}")

        except Exception as e:
            logger.error(f"Error sending notifications for stock adjustment: {e}")

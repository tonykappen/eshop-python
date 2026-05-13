"""ProductPriceChangedIntegrationEventHandler - handles price changes from Catalog module."""

import logging
from typing import Any

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.mediator import IMediator
from app.core.messaging.integration_event import IIntegrationEventHandler, IntegrationEvent
from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_command import (
    UpdateItemPriceInBasketCommand,
)
from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import (
    ProductPriceChangedIntegrationEventV1,
)

logger = logging.getLogger(__name__)


class ProductPriceChangedIntegrationEventHandler(IIntegrationEventHandler):
    """
    Handles ProductPriceChangedIntegrationEvent to update product prices in the basket.
    Matches .NET ProductPriceChangedIntegrationEventHandler.
    """

    def __init__(self, mediator: IMediator) -> None:
        """
        Initialize handler.

        Args:
            mediator: Mediator for sending commands
        """
        self._mediator = mediator

    async def handle(self, event: IntegrationEvent) -> None:
        """
        Handle the integration event.

        Args:
            event: The ProductPriceChangedIntegrationEventV1 event.
        """
        if not isinstance(event, ProductPriceChangedIntegrationEventV1):
            logger.warning(
                f"Received unexpected event type: {type(event).__name__}. Expected ProductPriceChangedIntegrationEventV1."
            )
            return

        logger.info(
            "Integration Event handled: %s for ProductId: %s",
            event.event_type,
            event.product_id,
        )

        command = UpdateItemPriceInBasketCommand(
            product_id=event.product_id, price=event.new_price_amount
        )
        result = await self._mediator.send(command, CancellationToken())

        if not result.is_success:
            logger.error(
                "Failed to update price for product id: %s in basket",
                event.product_id,
            )
        else:
            logger.info(
                "Price for product id: %s updated in basket", event.product_id
            )

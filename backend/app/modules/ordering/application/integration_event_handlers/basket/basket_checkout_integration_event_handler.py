"""BasketCheckoutIntegrationEventHandler - handles basket checkout from Basket module."""

import logging
from uuid import uuid4

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.mediator import IMediator
from app.core.messaging.integration_event import (IIntegrationEventHandler,
                                                  IntegrationEvent)
from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import \
    BasketCheckoutIntegrationEvent
from app.modules.ordering.application.dtos.address_dto import AddressDto
from app.modules.ordering.application.dtos.order_dto import OrderDto
from app.modules.ordering.application.dtos.order_item_dto import OrderItemDto
from app.modules.ordering.application.dtos.payment_dto import PaymentDto
from app.modules.ordering.application.features.orders.command.create_order.create_order_command import \
    CreateOrderCommand

logger = logging.getLogger(__name__)


class BasketCheckoutIntegrationEventHandler(IIntegrationEventHandler):
    """
    Handles BasketCheckoutIntegrationEvent to create an order.
    Matches .NET BasketCheckoutIntegrationEventHandler.
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
        Handle the integration event - matches .NET Consume method.

        Args:
            event: The BasketCheckoutIntegrationEvent
        """
        if not isinstance(event, BasketCheckoutIntegrationEvent):
            logger.warning(
                f"Received unexpected event type: {type(event).__name__}. Expected BasketCheckoutIntegrationEvent."
            )
            return

        logger.info(
            "Integration Event handled: %s (user_name: %s)",
            event.event_type,
            event.user_name,
        )

        try:
            # Map event to CreateOrderCommand (matching .NET MapToCreateOrderCommand)
            create_order_command = self._map_to_create_order_command(event)

            # Send command through mediator (matching .NET sender.Send)
            await self._mediator.send(create_order_command, CancellationToken())
        except Exception as e:
            logger.error(
                f"Error handling BasketCheckoutIntegrationEvent: {e}", exc_info=True
            )
            raise

    def _map_to_create_order_command(
        self, message: BasketCheckoutIntegrationEvent
    ) -> CreateOrderCommand:
        """
        Map BasketCheckoutIntegrationEvent to CreateOrderCommand.
        Matches .NET MapToCreateOrderCommand method.

        Note: .NET version uses hardcoded items. We'll follow that pattern for now.
        TODO: Fetch actual basket items from basket repository.

        Args:
            message: BasketCheckoutIntegrationEvent

        Returns:
            CreateOrderCommand
        """
        # Create AddressDto (matching .NET pattern)
        address_dto = AddressDto(
            first_name=message.first_name,
            last_name=message.last_name,
            email_address=message.email_address,
            address_line=message.address_line,
            country=message.country,
            state=message.state,
            zip_code=message.zip_code,
        )

        # Create PaymentDto (matching .NET pattern)
        payment_dto = PaymentDto(
            card_name=message.card_name,
            card_number=message.card_number,
            expiration=message.expiration,
            cvv=message.cvv,
            payment_method=message.payment_method,
        )

        # Generate order ID (matching .NET Guid.NewGuid())
        order_id = uuid4()

        # Convert basket items to order items
        order_items = [
            OrderItemDto(
                order_id=order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
            )
            for item in message.items
        ]

        # Create OrderDto with actual basket items
        order_dto = OrderDto(
            id=order_id,
            customer_id=message.customer_id,
            order_name=message.user_name,
            shipping_address=address_dto,
            billing_address=address_dto,  # Same as shipping in .NET
            payment=payment_dto,
            items=order_items,
        )

        return CreateOrderCommand(order=order_dto)

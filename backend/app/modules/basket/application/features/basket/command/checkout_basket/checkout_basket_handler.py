"""CheckoutBasketHandler with 1-1 parity to .NET implementation."""

import logging
from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import (
    BasketCheckoutIntegrationEvent,
)
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .checkout_basket_command import CheckoutBasketCommand, CheckoutBasketResult

logger = logging.getLogger(__name__)


class CheckoutBasketCommandValidator:
    """Validator for CheckoutBasketCommand - matches .NET CheckoutBasketCommandValidator."""

    def validate(self, command: CheckoutBasketCommand) -> list[str]:
        """
        Validate the checkout basket command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not command.basket_checkout:
            errors.append("BasketCheckoutDto can't be null")

        if not command.basket_checkout.user_name or not command.basket_checkout.user_name.strip():
            errors.append("UserName is required")

        return errors


class CheckoutBasketHandler(
    IRequestHandler[CheckoutBasketCommand, CheckoutBasketResult]
):
    """Handler for CheckoutBasketCommand - matches .NET CheckoutBasketHandler."""

    def __init__(
        self, repository: IBasketRepository, outbox_service: Any
    ) -> None:
        """
        Initialize handler.

        Args:
            repository: Basket repository
            outbox_service: Outbox service for writing integration events
        """
        self.repository = repository
        self.outbox_service = outbox_service
        self.logger = BaseLogger(__name__)

    async def handle(
        self, command: CheckoutBasketCommand, cancellation_token: CancellationToken
    ) -> CheckoutBasketResult:
        """
        Handle the command - matches .NET Handle(CheckoutBasketCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            CheckoutBasketResult indicating success
        """
        # Validate command first
        validator = CheckoutBasketCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.core.exceptions.bad_request_exception import BadRequestException

            raise BadRequestException(message="; ".join(errors))

        # Check for cancellation
        cancellation_token.throw_if_cancellation_requested()

        try:
            # Get existing basket with total price
            basket = await self.repository.get_basket(
                command.basket_checkout.user_name, as_no_tracking=False
            )

            if basket is None:
                raise BasketNotFoundException(command.basket_checkout.user_name)

            # Convert basket items to event items
            from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import (
                BasketCheckoutItem,
            )
            
            event_items = [
                BasketCheckoutItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                )
                for item in basket.items
            ]

            # Set total price on basket checkout event message
            event_message = BasketCheckoutIntegrationEvent(
                user_name=command.basket_checkout.user_name,
                customer_id=command.basket_checkout.customer_id,
                total_price=basket.total_price,
                items=event_items,
                first_name=command.basket_checkout.first_name,
                last_name=command.basket_checkout.last_name,
                email_address=command.basket_checkout.email_address,
                address_line=command.basket_checkout.address_line,
                country=command.basket_checkout.country,
                state=command.basket_checkout.state,
                zip_code=command.basket_checkout.zip_code,
                card_name=command.basket_checkout.card_name,
                card_number=command.basket_checkout.card_number,
                expiration=command.basket_checkout.expiration,
                cvv=command.basket_checkout.cvv,
                payment_method=command.basket_checkout.payment_method,
            )

            # Write a message to the outbox
            await self.outbox_service.write_integration_event(event_message)

            # Delete the basket
            await self.repository.delete_basket(command.basket_checkout.user_name)

            # Save changes to commit the transaction (outbox write + basket deletion)
            await self.repository.save_changes_async(command.basket_checkout.user_name)

            return CheckoutBasketResult(is_success=True)

        except Exception as e:
            # Log the actual error for debugging
            self.logger.log_error_with_context(
                "Checkout basket failed",
                error=e,
                context={
                    "user_name": command.basket_checkout.user_name if command.basket_checkout else None,
                    "exception_type": type(e).__name__,
                    "exception_module": type(e).__module__,
                },
            )
            logger.error(f"Checkout failed for user {command.basket_checkout.user_name if command.basket_checkout else 'unknown'}: {e}", exc_info=True)
            # Rollback is handled by the unit of work
            return CheckoutBasketResult(is_success=False)

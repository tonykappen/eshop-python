"""CheckoutBasketHandler with 1-1 parity to .NET implementation."""

import logging
from collections.abc import Callable
from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.application.basket_handler_context import use_basket_context
from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import \
    BasketCheckoutIntegrationEvent
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .checkout_basket_command import (CheckoutBasketCommand,
                                      CheckoutBasketResult)

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

        if (
            not command.basket_checkout.user_name
            or not command.basket_checkout.user_name.strip()
        ):
            errors.append("UserName is required")

        return errors


class CheckoutBasketHandler(
    IRequestHandler[CheckoutBasketCommand, CheckoutBasketResult]
):
    """Handler for CheckoutBasketCommand - matches .NET CheckoutBasketHandler."""

    def __init__(
        self,
        repository: IBasketRepository | None = None,
        outbox_service: Any | None = None,
        context_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._repository = repository
        self._outbox_service = outbox_service
        self._context_factory = context_factory
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
            from app.core.exceptions.bad_request_exception import \
                BadRequestException

            raise BadRequestException(message="; ".join(errors))

        cancellation_token.throw_if_cancellation_requested()

        try:
            async with use_basket_context(
                self._context_factory,
                repository=self._repository,
                outbox_service=self._outbox_service,
            ) as ctx:
                return await self._checkout(command, ctx.repository, ctx.outbox_service)
        except Exception as e:
            self.logger.log_error_with_context(
                "Checkout basket failed",
                error=e,
                context={
                    "user_name": (
                        command.basket_checkout.user_name
                        if command.basket_checkout
                        else None
                    ),
                    "exception_type": type(e).__name__,
                    "exception_module": type(e).__module__,
                },
            )
            logger.error(
                f"Checkout failed for user {command.basket_checkout.user_name if command.basket_checkout else 'unknown'}: {e}",
                exc_info=True,
            )
            return CheckoutBasketResult(is_success=False)

    async def _checkout(
        self,
        command: CheckoutBasketCommand,
        repository: IBasketRepository,
        outbox_service: Any,
    ) -> CheckoutBasketResult:
        if outbox_service is None:
            raise RuntimeError("Checkout handler missing outbox service")

        basket = await repository.get_basket(
            command.basket_checkout.user_name, as_no_tracking=False
        )

        if basket is None:
            raise BasketNotFoundException(command.basket_checkout.user_name)

        from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import \
            BasketCheckoutItem

        event_items = [
            BasketCheckoutItem(
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
            )
            for item in basket.items
        ]

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

        await outbox_service.write_integration_event(event_message)
        await repository.delete_basket(command.basket_checkout.user_name)
        await repository.save_changes_async(command.basket_checkout.user_name)

        return CheckoutBasketResult(is_success=True)

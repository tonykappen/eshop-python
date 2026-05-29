"""RemoveItemFromBasketHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from typing import Any

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.application.basket_handler_context import use_basket_context
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .remove_item_from_basket_command import (RemoveItemFromBasketCommand,
                                              RemoveItemFromBasketResult)


class RemoveItemFromBasketCommandValidator:
    """Validator for RemoveItemFromBasketCommand - matches .NET RemoveItemFromBasketCommandValidator."""

    def validate(self, command: RemoveItemFromBasketCommand) -> list[str]:
        """
        Validate the remove item from basket command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not command.user_name or not command.user_name.strip():
            errors.append("UserName is required")

        if not command.product_id:
            errors.append("ProductId is required")

        return errors


class RemoveItemFromBasketHandler(
    IRequestHandler[RemoveItemFromBasketCommand, RemoveItemFromBasketResult]
):
    """Handler for RemoveItemFromBasketCommand - matches .NET RemoveItemFromBasketHandler."""

    def __init__(
        self,
        repository: IBasketRepository | None = None,
        context_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._repository = repository
        self._context_factory = context_factory

    async def handle(
        self,
        command: RemoveItemFromBasketCommand,
        cancellation_token: CancellationToken,
    ) -> RemoveItemFromBasketResult:
        """
        Handle the command - matches .NET Handle(RemoveItemFromBasketCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            RemoveItemFromBasketResult containing the basket ID
        """
        # Validate command first
        validator = RemoveItemFromBasketCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.core.exceptions.bad_request_exception import \
                BadRequestException

            raise BadRequestException(message="; ".join(errors))

        cancellation_token.throw_if_cancellation_requested()

        async with use_basket_context(
            self._context_factory, repository=self._repository
        ) as ctx:
            shopping_cart = await ctx.repository.get_basket(
                command.user_name, as_no_tracking=False
            )
            shopping_cart.remove_item(command.product_id)
            if hasattr(ctx.repository, "update_basket"):
                shopping_cart = await ctx.repository.update_basket(shopping_cart)
            await ctx.repository.save_changes_async(command.user_name)

        return RemoveItemFromBasketResult(id=shopping_cart.id)

"""UpdateItemPriceInBasketHandler with 1-1 parity to .NET implementation."""

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .update_item_price_in_basket_command import (
    UpdateItemPriceInBasketCommand,
    UpdateItemPriceInBasketResult,
)


class UpdateItemPriceInBasketCommandValidator:
    """Validator for UpdateItemPriceInBasketCommand - matches .NET UpdateItemPriceInBasketCommandValidator."""

    def validate(self, command: UpdateItemPriceInBasketCommand) -> list[str]:
        """
        Validate the update item price in basket command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not command.product_id:
            errors.append("ProductId is required")

        if command.price <= 0:
            errors.append("Price must be greater than 0")

        return errors


class UpdateItemPriceInBasketHandler(
    IRequestHandler[UpdateItemPriceInBasketCommand, UpdateItemPriceInBasketResult]
):
    """Handler for UpdateItemPriceInBasketCommand - matches .NET UpdateItemPriceInBasketHandler."""

    def __init__(self, repository: IBasketRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Basket repository (needs access to items)
        """
        self.repository = repository

    async def handle(
        self,
        command: UpdateItemPriceInBasketCommand,
        cancellation_token: CancellationToken,
    ) -> UpdateItemPriceInBasketResult:
        """
        Handle the command - matches .NET Handle(UpdateItemPriceInBasketCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            UpdateItemPriceInBasketResult indicating success
        """
        # Validate command first
        validator = UpdateItemPriceInBasketCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.core.exceptions.bad_request_exception import BadRequestException

            raise BadRequestException(message="; ".join(errors))

        # Check for cancellation
        cancellation_token.throw_if_cancellation_requested()

        # Find Shopping Cart Items with given ProductId and update their price
        # The repository implements update_items_price which queries items directly
        updated = await self.repository.update_items_price(command.product_id, command.price)

        if not updated:
            return UpdateItemPriceInBasketResult(is_success=False)

        return UpdateItemPriceInBasketResult(is_success=True)

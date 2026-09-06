"""AddItemIntoBasketHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.core.mediator.mediator import IMediator
from app.modules.basket.application.basket_handler_context import use_basket_context
from app.modules.basket.domain.entities.basket import ShoppingCart
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.basket.domain.repositories.basket import IBasketRepository
from app.modules.catalog.application.features.products.queries.get_product_by_id.get_product_by_id_query import \
    GetProductByIdQuery

from .add_item_into_basket_command import (AddItemIntoBasketCommand,
                                           AddItemIntoBasketResult)


class AddItemIntoBasketCommandValidator:
    """Validator for AddItemIntoBasketCommand - matches .NET AddItemIntoBasketCommandValidator."""

    def validate(self, command: AddItemIntoBasketCommand) -> list[str]:
        """
        Validate the add item into basket command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not command.user_name or not command.user_name.strip():
            errors.append("UserName is required")

        if not command.shopping_cart_item.product_id:
            errors.append("ProductId is required")

        if command.shopping_cart_item.quantity <= 0:
            errors.append("Quantity must be greater than 0")

        return errors


class AddItemIntoBasketHandler(
    IRequestHandler[AddItemIntoBasketCommand, AddItemIntoBasketResult]
):
    """Handler for AddItemIntoBasketCommand - matches .NET AddItemIntoBasketHandler."""

    def __init__(
        self,
        repository: IBasketRepository | None = None,
        context_factory: Callable[[], Any] | None = None,
        mediator: IMediator | None = None,
    ) -> None:
        self._repository = repository
        self._context_factory = context_factory
        self.mediator = mediator
        self.logger = BaseLogger(__name__)

    async def handle(
        self, command: AddItemIntoBasketCommand, cancellation_token: CancellationToken
    ) -> AddItemIntoBasketResult:
        """
        Handle the command - matches .NET Handle(AddItemIntoBasketCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            AddItemIntoBasketResult containing the basket ID
        """
        # Validate command first
        validator = AddItemIntoBasketCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.core.exceptions.bad_request_exception import \
                BadRequestException

            raise BadRequestException(message="; ".join(errors))

        # Check for cancellation
        cancellation_token.throw_if_cancellation_requested()

        # Before AddItem into SC, call Catalog Module GetProductById method
        if self.mediator is None:
            raise RuntimeError(
                "AddItemIntoBasketHandler requires a mediator for catalog lookups"
            )

        try:
            product_query = GetProductByIdQuery(
                id=command.shopping_cart_item.product_id
            )
            product_result: Any = await self.mediator.send(product_query, cancellation_token)

            # Validate product result
            if not product_result or not product_result.product:
                from app.core.exceptions.bad_request_exception import \
                    BadRequestException

                raise BadRequestException(
                    message=f"Product {command.shopping_cart_item.product_id} not found or invalid"
                )
        except Exception as e:
            # Import exception types
            from app.core.exceptions.bad_request_exception import \
                BadRequestException
            from app.core.exceptions.not_found_exception import (
                NotFoundError, NotFoundException)

            # Log the exception for debugging
            exception_type = type(e).__name__
            exception_module = type(e).__module__
            self.logger.log_error_with_context(
                "Error getting product for basket",
                error=e,
                context={
                    "product_id": str(command.shopping_cart_item.product_id),
                    "exception_type": exception_type,
                    "exception_module": exception_module,
                },
            )

            # Check if it's a NotFoundError or any subclass (which includes ProductNotFoundError)
            # ProductNotFoundError inherits from NotFoundError, so isinstance should work
            if isinstance(e, (NotFoundError, NotFoundException)):
                # Convert NotFoundError to BadRequestException for better user experience
                raise BadRequestException(
                    message=f"Product {command.shopping_cart_item.product_id} not found. Please ensure the product exists in the catalog."
                ) from e

            # If it's any other exception, check the exception name and message
            if "not found" in str(e).lower() or "NotFound" in exception_type:
                raise BadRequestException(
                    message=f"Product {command.shopping_cart_item.product_id} not found. Please ensure the product exists in the catalog."
                ) from e

            # Re-raise other exceptions
            raise

        async with use_basket_context(
            self._context_factory, repository=self._repository
        ) as ctx:
            shopping_cart = await self._mutate_basket(
                command, cancellation_token, ctx.repository, product_result
            )
            await ctx.repository.save_changes_async(command.user_name)

        return AddItemIntoBasketResult(id=shopping_cart.id)

    async def _mutate_basket(
        self,
        command: AddItemIntoBasketCommand,
        cancellation_token: CancellationToken,
        repository: IBasketRepository,
        product_result: Any,
    ) -> ShoppingCart:
        cancellation_token.throw_if_cancellation_requested()

        try:
            shopping_cart = await repository.get_basket(
                command.user_name, as_no_tracking=False
            )
            shopping_cart.add_item(
                product_id=command.shopping_cart_item.product_id,
                quantity=command.shopping_cart_item.quantity,
                color=command.shopping_cart_item.color,
                price=Decimal(str(product_result.product.price)),
                product_name=product_result.product.name,
            )
            if hasattr(repository, "update_basket"):
                shopping_cart = await repository.update_basket(shopping_cart)
        except BasketNotFoundException:
            shopping_cart = ShoppingCart.create(
                cart_id=uuid4(),
                user_name=command.user_name,
            )
            shopping_cart.add_item(
                product_id=command.shopping_cart_item.product_id,
                quantity=command.shopping_cart_item.quantity,
                color=command.shopping_cart_item.color,
                price=Decimal(str(product_result.product.price)),
                product_name=product_result.product.name,
            )
            shopping_cart = await repository.create_basket(shopping_cart)

        return shopping_cart

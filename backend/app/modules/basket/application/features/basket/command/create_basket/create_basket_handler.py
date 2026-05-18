"""CreateBasketHandler with 1-1 parity to .NET implementation."""

from decimal import Decimal
from uuid import uuid4

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.domain.entities.basket import ShoppingCart
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .create_basket_command import CreateBasketCommand, CreateBasketResult


class CreateBasketCommandValidator:
    """Validator for CreateBasketCommand - matches .NET CreateBasketCommandValidator."""

    def validate(self, command: CreateBasketCommand) -> list[str]:
        """
        Validate the create basket command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if (
            not command.shopping_cart.user_name
            or not command.shopping_cart.user_name.strip()
        ):
            errors.append("UserName is required")

        return errors


class CreateBasketHandler(IRequestHandler[CreateBasketCommand, CreateBasketResult]):
    """Handler for CreateBasketCommand - matches .NET CreateBasketHandler."""

    def __init__(self, repository: IBasketRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Basket repository
        """
        self.repository = repository

    async def handle(
        self, command: CreateBasketCommand, cancellation_token: CancellationToken
    ) -> CreateBasketResult:
        """
        Handle the command - matches .NET Handle(CreateBasketCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            CreateBasketResult containing the created basket ID
        """
        # Validate command first
        validator = CreateBasketCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.core.exceptions.bad_request_exception import \
                BadRequestException

            raise BadRequestException(message="; ".join(errors))

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Create new basket from command object
        shopping_cart = self._create_new_basket(command.shopping_cart)

        # Save to database
        await self.repository.create_basket(shopping_cart)

        # Return result
        return CreateBasketResult(id=shopping_cart.id)

    def _create_new_basket(self, shopping_cart_dto) -> ShoppingCart:
        """
        Create new basket from DTO - matches .NET CreateNewBasket(ShoppingCartDto shoppingCartDto).

        Args:
            shopping_cart_dto: Shopping cart DTO

        Returns:
            Created ShoppingCart entity
        """
        # Create new basket
        new_basket = ShoppingCart.create(
            cart_id=uuid4(),
            user_name=shopping_cart_dto.user_name,
        )

        # Add items from DTO
        for item in shopping_cart_dto.items:
            new_basket.add_item(
                product_id=item.product_id,
                quantity=item.quantity,
                color=item.color,
                price=Decimal(str(item.price)),
                product_name=item.product_name,
            )

        return new_basket

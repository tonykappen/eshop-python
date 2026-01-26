"""AddItemIntoBasketHandler with 1-1 parity to .NET implementation."""

from decimal import Decimal

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.core.mediator.mediator import IMediator
from app.modules.basket.domain.entities.basket import ShoppingCart
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.basket.domain.repositories.basket import IBasketRepository
from app.modules.catalog.application.features.products.queries.get_product_by_id.query import (
    GetProductByIdQuery,
)
from uuid import uuid4

from .add_item_into_basket_command import AddItemIntoBasketCommand, AddItemIntoBasketResult


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

    def __init__(self, repository: IBasketRepository, mediator: IMediator) -> None:
        """
        Initialize handler.

        Args:
            repository: Basket repository
            mediator: Mediator for sending queries to other modules
        """
        self.repository = repository
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
            from app.core.exceptions.bad_request_exception import BadRequestException

            raise BadRequestException(message="; ".join(errors))

        # Check for cancellation
        cancellation_token.throw_if_cancellation_requested()

        # Before AddItem into SC, call Catalog Module GetProductById method
        # Get latest product information and set Price and ProductName when adding item into SC
        try:
            product_query = GetProductByIdQuery(id=command.shopping_cart_item.product_id)
            product_result = await self.mediator.send(product_query, cancellation_token)
            
            # Validate product result
            if not product_result or not product_result.product:
                from app.core.exceptions.bad_request_exception import BadRequestException
                raise BadRequestException(
                    message=f"Product {command.shopping_cart_item.product_id} not found or invalid"
                )
        except Exception as e:
            # Import exception types
            from app.core.exceptions.not_found_exception import NotFoundError, NotFoundException
            from app.core.exceptions.bad_request_exception import BadRequestException
            
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

        # Get shopping cart (with tracking for updates) - matches .NET GetBasket(userName, false)
        # In .NET, this returns a tracked entity that can be modified and saved
        try:
            shopping_cart = await self.repository.get_basket(
                command.user_name, as_no_tracking=False
            )
            # Basket exists - add item to it (matches .NET shoppingCart.AddItem(...))
            shopping_cart.add_item(
                product_id=command.shopping_cart_item.product_id,
                quantity=command.shopping_cart_item.quantity,
                color=command.shopping_cart_item.color,
                price=Decimal(str(product_result.product.price)),
                product_name=product_result.product.name,
            )
            # Sync domain changes to tracked ORM object (matches .NET Entity Framework tracking)
            if hasattr(self.repository, 'update_basket'):
                shopping_cart = await self.repository.update_basket(shopping_cart)
        except BasketNotFoundException:
            # Basket doesn't exist, create it with the item already included
            # This matches .NET behavior where basket is created before adding items
            shopping_cart = ShoppingCart.create(
                cart_id=uuid4(),
                user_name=command.user_name,
            )
            # Add item before creating basket so it's included in the ORM
            shopping_cart.add_item(
                product_id=command.shopping_cart_item.product_id,
                quantity=command.shopping_cart_item.quantity,
                color=command.shopping_cart_item.color,
                price=Decimal(str(product_result.product.price)),
                product_name=product_result.product.name,
            )
            # Create basket with items already included
            # Items are already in the domain model, so they'll be created with the basket
            shopping_cart = await self.repository.create_basket(shopping_cart)
            # No need to update - items were created with the basket
        
        # Save changes - matches .NET repository.SaveChangesAsync(userName, cancellationToken)
        await self.repository.save_changes_async(command.user_name)

        return AddItemIntoBasketResult(id=shopping_cart.id)

"""CreateOrderHandler with 1-1 parity to .NET implementation."""

import random
from uuid import uuid4

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.ordering.domain.entities.order.order import Order
from app.modules.ordering.domain.repositories.order import IOrderRepository
from app.modules.ordering.domain.value_objects import Address, Payment

from .create_order_command import CreateOrderCommand, CreateOrderResult


class CreateOrderCommandValidator:
    """Validator for CreateOrderCommand - matches .NET CreateOrderCommandValidator."""

    def validate(self, command: CreateOrderCommand) -> list[str]:
        """
        Validate the create order command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not command.order.order_name or not command.order.order_name.strip():
            errors.append("OrderName is required")

        return errors


class CreateOrderHandler(IRequestHandler[CreateOrderCommand, CreateOrderResult]):
    """Handler for CreateOrderCommand - matches .NET CreateOrderHandler."""

    def __init__(self, repository: IOrderRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Order repository
        """
        self.repository = repository

    async def handle(
        self, command: CreateOrderCommand, cancellation_token: CancellationToken
    ) -> CreateOrderResult:
        """
        Handle the command - matches .NET Handle(CreateOrderCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            CreateOrderResult containing the created order ID
        """
        # Validate command first
        validator = CreateOrderCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.core.exceptions.bad_request_exception import \
                BadRequestException

            raise BadRequestException(message="; ".join(errors))

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Create new order from command
        order = self._create_new_order(command.order)

        # Save to database using real database session (no mocking)
        await self.repository.add(order)
        await self.repository.save_changes_async()

        return CreateOrderResult(id=order.id)

    def _create_new_order(self, order_dto) -> Order:
        """
        Create new order from DTO - matches .NET CreateNewOrder(OrderDto orderDto).

        Args:
            order_dto: Order DTO

        Returns:
            Created Order entity
        """
        # Create Address value objects
        shipping_address = Address.of(
            first_name=order_dto.shipping_address.first_name,
            last_name=order_dto.shipping_address.last_name,
            email_address=order_dto.shipping_address.email_address,
            address_line=order_dto.shipping_address.address_line,
            country=order_dto.shipping_address.country,
            state=order_dto.shipping_address.state,
            zip_code=order_dto.shipping_address.zip_code,
        )

        billing_address = Address.of(
            first_name=order_dto.billing_address.first_name,
            last_name=order_dto.billing_address.last_name,
            email_address=order_dto.billing_address.email_address,
            address_line=order_dto.billing_address.address_line,
            country=order_dto.billing_address.country,
            state=order_dto.billing_address.state,
            zip_code=order_dto.billing_address.zip_code,
        )

        # Create Payment value object
        payment = Payment.of(
            card_name=order_dto.payment.card_name,
            card_number=order_dto.payment.card_number,
            expiration=order_dto.payment.expiration,
            cvv=order_dto.payment.cvv,
            payment_method=order_dto.payment.payment_method,
        )

        # Create order with random suffix in order name (matching .NET pattern)
        order_name_with_suffix = f"{order_dto.order_name}_{random.randint(1, 10000)}"

        new_order = Order.create(
            id=uuid4(),
            customer_id=order_dto.customer_id,
            order_name=order_name_with_suffix,
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment=payment,
        )

        # Add items from DTO (matching .NET ForEach pattern)
        for item in order_dto.items:
            new_order.add(
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
            )

        return new_order

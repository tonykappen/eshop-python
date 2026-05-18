"""DeleteOrderHandler with 1-1 parity to .NET implementation."""

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.ordering.domain.exceptions.order import OrderNotFoundException
from app.modules.ordering.domain.repositories.order import IOrderRepository

from .delete_order_command import DeleteOrderCommand, DeleteOrderResult


class DeleteOrderCommandValidator:
    """Validator for DeleteOrderCommand - matches .NET DeleteOrderCommandValidator."""

    def validate(self, command: DeleteOrderCommand) -> list[str]:
        """
        Validate the delete order command.

        Args:
            command: The command to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if not command.order_id:
            errors.append("OrderId is required")

        return errors


class DeleteOrderHandler(IRequestHandler[DeleteOrderCommand, DeleteOrderResult]):
    """Handler for DeleteOrderCommand - matches .NET DeleteOrderHandler."""

    def __init__(self, repository: IOrderRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Order repository
        """
        self.repository = repository

    async def handle(
        self, command: DeleteOrderCommand, cancellation_token: CancellationToken
    ) -> DeleteOrderResult:
        """
        Handle the command - matches .NET Handle(DeleteOrderCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            DeleteOrderResult indicating success

        Raises:
            OrderNotFoundException: If order is not found
        """
        # Validate command first
        validator = DeleteOrderCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.core.exceptions.bad_request_exception import \
                BadRequestException

            raise BadRequestException(message="; ".join(errors))

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Find order using FindAsync pattern (matching .NET)
        order = await self.repository.get_by_id(command.order_id)

        if order is None:
            raise OrderNotFoundException(command.order_id)

        # Remove order using real database session (no mocking)
        await self.repository.remove(order)
        await self.repository.save_changes_async()

        return DeleteOrderResult(is_success=True)

"""DeleteBasketHandler with 1-1 parity to .NET implementation."""

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .delete_basket_command import DeleteBasketCommand, DeleteBasketResult


class DeleteBasketHandler(IRequestHandler[DeleteBasketCommand, DeleteBasketResult]):
    """Handler for DeleteBasketCommand - matches .NET DeleteBasketHandler."""

    def __init__(self, repository: IBasketRepository) -> None:
        """
        Initialize handler.

        Args:
            repository: Basket repository
        """
        self.repository = repository

    async def handle(
        self, command: DeleteBasketCommand, cancellation_token: CancellationToken
    ) -> DeleteBasketResult:
        """
        Handle the command - matches .NET Handle(DeleteBasketCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            DeleteBasketResult indicating success
        """
        # Check for cancellation
        cancellation_token.throw_if_cancellation_requested()

        # Delete basket
        await self.repository.delete_basket(command.user_name)

        return DeleteBasketResult(is_success=True)

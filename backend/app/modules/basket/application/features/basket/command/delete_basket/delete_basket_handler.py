"""DeleteBasketHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from typing import Any

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.basket.application.basket_handler_context import use_basket_context
from app.modules.basket.domain.repositories.basket import IBasketRepository

from .delete_basket_command import DeleteBasketCommand, DeleteBasketResult


class DeleteBasketHandler(IRequestHandler[DeleteBasketCommand, DeleteBasketResult]):
    """Handler for DeleteBasketCommand - matches .NET DeleteBasketHandler."""

    def __init__(
        self,
        repository: IBasketRepository | None = None,
        context_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._repository = repository
        self._context_factory = context_factory

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
        cancellation_token.throw_if_cancellation_requested()

        async with use_basket_context(
            self._context_factory, repository=self._repository
        ) as ctx:
            await ctx.repository.delete_basket(command.user_name)

        return DeleteBasketResult(is_success=True)

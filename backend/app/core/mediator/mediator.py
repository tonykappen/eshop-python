"""Main Mediator implementation with 1-1 parity to .NET MediatR."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from app.core.contracts.cqrs import ICommand, IQuery
from app.core.logging.base_logger import BaseLogger

from .behaviors import LoggingBehavior, ValidationBehavior
from .cancellation import CancellationToken
from .handler_registry import HandlerRegistry

TResponse = TypeVar("TResponse")


class IMediator(ABC):
    """Interface for mediator pattern - matches .NET ISender interface."""

    @abstractmethod
    async def send(
        self,
        request: ICommand[TResponse] | IQuery[TResponse],
        cancellation_token: CancellationToken,
    ) -> TResponse:
        """Send a command or query and get result - matches .NET ISender.Send()."""
        pass


class Mediator(IMediator):
    """Main mediator implementation with 1-1 parity to .NET MediatR."""

    def __init__(self, handler_registry: HandlerRegistry) -> None:
        self.handler_registry = handler_registry
        self.logger = BaseLogger(__name__)

        # Pipeline behaviors (matches .NET MediatR behaviors)
        self.behaviors: list[Any] = [ValidationBehavior(), LoggingBehavior()]

    async def send(
        self,
        request: ICommand[TResponse] | IQuery[TResponse],
        cancellation_token: CancellationToken,
    ) -> TResponse:
        """
        Send a command or query through the mediator pipeline.

        Matches .NET ISender.Send<TResponse>(IRequest<TResponse> request)
        """
        request_type = type(request)
        self.logger.log_debug_with_context(
            "Mediator processing request",
            context={"request_type": request_type.__name__},
        )

        # Get handler from registry
        handler = self.handler_registry.get_handler(request_type)
        if not handler:
            raise ValueError(
                f"No handler registered for request type: {request_type.__name__}"
            )

        # Execute through pipeline behaviors
        result = await self._execute_pipeline(request, handler, cancellation_token)

        self.logger.log_debug_with_context(
            "Mediator completed request",
            context={"request_type": request_type.__name__},
        )
        return result  # type: ignore

    async def send_command(
        self, command: ICommand[TResponse], cancellation_token: CancellationToken
    ) -> TResponse:
        """Send a command - matches .NET ISender.Send(ICommand<TResponse>)."""
        return await self.send(command, cancellation_token)

    async def send_query(
        self, query: IQuery[TResponse], cancellation_token: CancellationToken
    ) -> TResponse:
        """Send a query - matches .NET ISender.Send(IQuery<TResponse>)."""
        return await self.send(query, cancellation_token)

    async def _execute_pipeline(
        self, request: Any, handler: Any, cancellation_token: CancellationToken
    ) -> Any:
        """Execute request through pipeline behaviors - matches .NET MediatR pipeline."""
        # Start with the handler
        current_handler = handler

        # Apply behaviors in reverse order (last in, first out)
        for behavior in reversed(self.behaviors):
            current_handler = behavior.wrap(current_handler)

        # Execute the pipeline with cancellation token
        return await current_handler.handle(request, cancellation_token)

    def register_handler(self, request_type: type[Any], handler: Any) -> None:
        """Register a handler for a specific request type."""
        self.handler_registry.register_handler(request_type, handler)

    def register_behavior(self, behavior: Any) -> None:
        """Register a pipeline behavior."""
        self.behaviors.append(behavior)

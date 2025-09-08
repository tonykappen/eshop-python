"""Handler registry for mediator pattern with 1-1 parity to .NET MediatR."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class IRequestHandler(ABC, Generic[TRequest, TResponse]):
    """Base interface for request handlers - matches .NET IRequestHandler<TRequest, TResponse>."""

    @abstractmethod
    async def handle(
        self, request: TRequest, cancellation_token: CancellationToken
    ) -> TResponse:
        """Handle the request - matches .NET Handle(TRequest request, CancellationToken cancellationToken)."""
        pass


class HandlerRegistry:
    """Registry for request handlers with 1-1 parity to .NET MediatR."""

    def __init__(self) -> None:
        self.handlers: dict[type[Any], IRequestHandler[Any, Any]] = {}
        self.logger = BaseLogger(__name__)

    def register_handler(
        self, request_type: type[Any], handler: IRequestHandler[Any, Any]
    ) -> None:
        """Register a handler for a specific request type."""
        self.handlers[request_type] = handler
        self.logger.debug(
            f"Registered handler {type(handler).__name__} for request {request_type.__name__}"
        )

    def get_handler(self, request_type: type[Any]) -> IRequestHandler[Any, Any] | None:
        """Get handler for a specific request type."""
        return self.handlers.get(request_type)

    def register_handlers_from_assembly(self, assembly: Any) -> None:
        """Register all handlers from an assembly - matches .NET RegisterServicesFromAssemblies()."""
        # This would scan the assembly for IRequestHandler implementations
        # For now, we'll implement this in the extensions
        pass

    def clear(self) -> None:
        """Clear all registered handlers."""
        self.handlers.clear()
        self.logger.debug("Cleared all registered handlers")

    def get_registered_types(self) -> list[type[Any]]:
        """Get all registered request types."""
        return list(self.handlers.keys())

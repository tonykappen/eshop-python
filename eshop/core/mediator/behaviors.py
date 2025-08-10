"""Pipeline behaviors for mediator pattern with 1-1 parity to .NET MediatR."""

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from eshop.core.logging.logger import get_logger

from .cancellation import CancellationToken

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class IPipelineBehavior(ABC, Generic[TRequest, TResponse]):
    """Base interface for pipeline behaviors - matches .NET IPipelineBehavior<TRequest, TResponse>."""

    @abstractmethod
    async def handle(
        self, request: TRequest, next_handler: Callable[[], Any]
    ) -> TResponse:
        """Handle the request in the pipeline - matches .NET Handle(TRequest request, RequestHandlerDelegate<TResponse> next)."""
        pass

    def wrap(self, next_handler: Any) -> Any:
        """Wrap the next handler in this behavior."""
        return BehaviorWrapper(self, next_handler)


class BehaviorWrapper:
    """Wrapper for chaining behaviors together."""

    def __init__(
        self, behavior: IPipelineBehavior[Any, Any], next_handler: Any
    ) -> None:
        self.behavior = behavior
        self.next_handler = next_handler

    async def handle(self, request: Any, cancellation_token: CancellationToken) -> Any:
        """Handle request through this behavior."""

        def next_callable() -> Any:
            return self.next_handler.handle(request, cancellation_token)

        return await self.behavior.handle(request, next_callable)


class ValidationBehavior(IPipelineBehavior[TRequest, TResponse]):
    """Validation behavior - matches .NET ValidationBehavior<TRequest, TResponse>."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    async def handle(
        self, request: TRequest, next_handler: Callable[[], TResponse]
    ) -> TResponse:
        """Handle validation - matches .NET ValidationBehavior.Handle()."""
        # For now, we'll use Pydantic validation
        # In a full implementation, this would use FluentValidation equivalent
        if hasattr(request, "model_validate") and hasattr(request, "model_dump"):
            try:
                # Validate the request using Pydantic
                request.model_validate(request.model_dump())
            except Exception as validation_error:
                self.logger.error(
                    f"Validation failed for {type(request).__name__}: {validation_error}"
                )
                raise ValueError(
                    f"Validation failed: {validation_error}"
                ) from validation_error

        result = await next_handler()
        return result


class LoggingBehavior(IPipelineBehavior[TRequest, TResponse]):
    """Logging behavior - matches .NET LoggingBehavior<TRequest, TResponse>."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    async def handle(
        self, request: TRequest, next_handler: Callable[[], TResponse]
    ) -> TResponse:
        """Handle logging - matches .NET LoggingBehavior.Handle()."""
        request_type = type(request).__name__
        response_type = self._get_response_type(request)

        self.logger.info(
            "[START] Handle request=%s - Response=%s - RequestData=%s",
            request_type,
            response_type,
            str(request),
        )

        start_time = time.time()

        try:
            response = await next_handler()

            elapsed_time = time.time() - start_time

            # Log performance warning if request takes more than 3 seconds
            if elapsed_time > 3:
                self.logger.warning(
                    "[PERFORMANCE] The request %s took %.2f seconds.",
                    request_type,
                    elapsed_time,
                )

            self.logger.info("[END] Handled %s with %s", request_type, response_type)

            return response

        except Exception as e:
            self.logger.error("[ERROR] Failed to handle %s: %s", request_type, str(e))
            raise

    def _get_response_type(self, request: TRequest) -> str:
        """Get the expected response type for the request."""
        # Try to extract response type from generic parameters
        if hasattr(request, "__orig_bases__"):
            for base in request.__orig_bases__:
                if hasattr(base, "__args__") and len(base.__args__) > 1:
                    return str(base.__args__[1].__name__)

        return "Unknown"

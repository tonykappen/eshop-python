"""Validation behavior - validates commands before execution."""

from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.behaviors import IPipelineBehavior

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class ValidationBehavior(IPipelineBehavior[TRequest, TResponse]):
    """Validation behavior - validates commands/queries before execution."""

    def __init__(self) -> None:
        self.logger = BaseLogger(__name__)

    async def handle(
        self, request: TRequest, next_handler: Callable[[], Awaitable[TResponse]]
    ) -> TResponse:
        """
        Handle validation - validates the request before passing to next handler.
        
        Args:
            request: The request to validate
            next_handler: Next handler in the pipeline
            
        Returns:
            Response from the next handler
        """
        # Validate using Pydantic if the request is a Pydantic model
        if hasattr(request, "model_validate") and hasattr(request, "model_dump"):
            try:
                # Re-validate the request to ensure it's still valid
                request.model_validate(request.model_dump())
            except Exception as validation_error:
                self.logger.log_error_with_context(
                    "Validation failed for request",
                    error=validation_error,
                    context={"request_type": type(request).__name__},
                )
                raise ValueError(
                    f"Validation failed: {validation_error}"
                ) from validation_error

        result = await next_handler()
        return result

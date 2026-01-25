"""Logging behavior - logs commands/queries and their results."""

import time
from collections.abc import Awaitable, Callable
from typing import Any, Generic, TypeVar

from app.core.logging.base_logger import BaseLogger
from app.core.logging.trace_context import get_request_id, get_trace_id
from app.core.mediator.behaviors import IPipelineBehavior

TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class LoggingBehavior(IPipelineBehavior[TRequest, TResponse]):
    """Logging behavior - logs commands/queries and their results."""

    def __init__(self) -> None:
        self.logger = BaseLogger(__name__)

    async def handle(
        self, request: TRequest, next_handler: Callable[[], Awaitable[TResponse]]
    ) -> TResponse:
        """
        Handle logging - logs request handling start, completion, and errors.
        
        Args:
            request: The request being handled
            next_handler: Next handler in the pipeline
            
        Returns:
            Response from the next handler
        """
        request_type = type(request).__name__
        response_type = self._get_response_type(request)

        # Use shared trace context from contextvars (set by middleware)
        trace_id = get_trace_id()
        request_id = get_request_id()

        self.logger.log_with_context(
            "Starting request handling",
            context={
                "request_type": request_type,
                "response_type": response_type,
                "request_data": str(request),
                "trace_id": trace_id,
                "request_id": request_id,
            },
        )

        start_time = time.time()

        try:
            response = await next_handler()

            elapsed_time = time.time() - start_time

            # Log performance warning if request takes more than 3 seconds
            if elapsed_time > 3:
                self.logger.log_warning_with_context(
                    "Request performance warning",
                    context={
                        "request_type": request_type,
                        "elapsed_time": elapsed_time,
                        "trace_id": trace_id,
                        "request_id": request_id,
                    },
                )

            self.logger.log_with_context(
                "Request handling completed",
                context={
                    "request_type": request_type,
                    "response_type": response_type,
                    "elapsed_time": elapsed_time,
                    "trace_id": trace_id,
                    "request_id": request_id,
                },
            )

            return response

        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.log_error_with_context(
                "Request handling failed",
                error=e,
                context={
                    "request_type": request_type,
                    "elapsed_time": elapsed_time,
                    "trace_id": trace_id,
                    "request_id": request_id,
                },
            )
            raise

    def _get_response_type(self, request: TRequest) -> str:
        """Get the expected response type for the request."""
        request_type = type(request)

        # Check if the request class has generic type annotations
        if hasattr(request_type, "__orig_bases__"):
            for base in request_type.__orig_bases__:  # type: ignore[attr-defined]
                if hasattr(base, "__args__") and len(base.__args__) > 0:
                    response_type = base.__args__[0]
                    if hasattr(response_type, "__name__"):
                        return response_type.__name__  # type: ignore[no-any-return]
                    else:
                        return str(response_type)

        # Try to get from class annotations
        if hasattr(request_type, "__annotations__"):
            annotations = getattr(request_type, "__annotations__", {})
            for annotation_name, annotation_type in annotations.items():
                if "response" in annotation_name.lower():
                    if hasattr(annotation_type, "__name__"):
                        return annotation_type.__name__  # type: ignore[no-any-return]
                    else:
                        return str(annotation_type)  # type: ignore[no-any-return]

        # Fallback: try to infer from request type name
        request_name = request_type.__name__
        if request_name.endswith("Query"):
            return f"{request_name.replace('Query', 'Result')}"
        elif request_name.endswith("Command"):
            return f"{request_name.replace('Command', 'Result')}"

        return "Response"












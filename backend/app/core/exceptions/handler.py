"""Custom exception handler with 1-1 parity to .NET CustomExceptionHandler."""

import traceback
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

from app.core.exceptions.base import (
    BadRequestError,
    BaseError,
    ConfigurationError,
    ConflictError,
    ConnectionError,
    DatabaseError,
    ForbiddenError,
    InternalServerError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class CustomExceptionHandler:
    """Custom exception handler - matches .NET CustomExceptionHandler."""

    @staticmethod
    async def handle_exception(request: Request, exception: Exception) -> JSONResponse:
        """Handle exceptions and return appropriate HTTP responses."""
        # Log the error using base logger
        logger.log_exception(
            message="Exception occurred during request processing",
            exception=exception,
            context={
                "request_path": str(request.url.path),
                "request_method": request.method,
                "request_headers": dict(request.headers),
            }
        )

        # Map exception to HTTP status code and response details
        status_code, title, detail, extensions = CustomExceptionHandler._map_exception(
            exception
        )

        # Create problem details response (matches .NET ProblemDetails)
        # Generate traceId from request state or create a new one
        trace_id = getattr(request.state, "request_id", None)
        if not trace_id:
            import uuid

            trace_id = str(uuid.uuid4())

        problem_details = {
            "title": title,
            "detail": detail,
            "status": status_code,
            "instance": str(request.url.path),
            "traceId": trace_id,
        }

        # Add extensions if any
        if extensions:
            problem_details.update(extensions)

        # Add validation errors for Pydantic validation errors
        if isinstance(exception, PydanticValidationError):
            problem_details["validationErrors"] = [
                {
                    "field": error["loc"][0] if error["loc"] else "unknown",
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exception.errors()
            ]

        return JSONResponse(
            status_code=status_code,
            content=problem_details,
        )

    @staticmethod
    def _map_exception(exception: Exception) -> tuple[int, str, str, dict[str, Any]]:
        """Map exception to HTTP status code and response details."""
        if isinstance(exception, InternalServerError):
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, ValidationError):
            return (
                status.HTTP_400_BAD_REQUEST,
                exception.__class__.__name__,
                exception.message,
                {"validationErrors": exception.errors} if exception.errors else {},
            )

        elif isinstance(exception, BadRequestError):
            return (
                status.HTTP_400_BAD_REQUEST,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, NotFoundError):
            return (
                status.HTTP_404_NOT_FOUND,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, UnauthorizedError):
            return (
                status.HTTP_401_UNAUTHORIZED,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, ForbiddenError):
            return (
                status.HTTP_403_FORBIDDEN,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, ConflictError):
            return (
                status.HTTP_409_CONFLICT,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, DatabaseError):
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, ConnectionError):
            return (
                status.HTTP_503_SERVICE_UNAVAILABLE,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, ConfigurationError):
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                exception.__class__.__name__,
                exception.message,
                {"details": exception.details} if exception.details else {},
            )

        elif isinstance(exception, PydanticValidationError):
            return (
                status.HTTP_400_BAD_REQUEST,
                "ValidationError",
                "Request validation failed",
                {},
            )

        # Default case for unhandled exceptions
        else:
            return (
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                exception.__class__.__name__,
                str(exception),
                {"traceback": traceback.format_exc()},
            )


def add_exception_handlers(app: Any) -> None:
    """Add custom exception handlers to FastAPI app."""
    handler = CustomExceptionHandler()

    # Register exception handlers for all custom exceptions
    app.add_exception_handler(BaseError, handler.handle_exception)
    app.add_exception_handler(PydanticValidationError, handler.handle_exception)

    # Register general exception handler for unhandled exceptions
    app.add_exception_handler(Exception, handler.handle_exception)

    logger.log_info("Custom exception handlers registered")

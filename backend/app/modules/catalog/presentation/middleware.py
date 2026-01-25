"""Middleware for catalog module."""

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware for adding request ID to requests."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add request ID to request and response.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Add to request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware for request timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add timing information to requests.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Add timing headers
        response.headers["X-Response-Time"] = f"{duration:.4f}s"

        # Log timing
        logger.info(
            f"Request {request.method} {request.url.path} completed in {duration:.4f}s",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "duration": duration,
                "status_code": response.status_code,
            },
        )

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response information.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Log request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent"),
            },
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": getattr(request.state, "request_id", None),
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "response_time": response.headers.get("X-Response-Time"),
            },
        )

        return response


class AuthStubMiddleware(BaseHTTPMiddleware):
    """Stub middleware for authentication (for development)."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Add stub authentication information.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response: HTTP response
        """
        # Add stub user information to request state
        request.state.user_id = "stub-user-id"
        request.state.username = "stub-user"
        request.state.user_roles = ["user"]

        # Add stub tenant information
        request.state.tenant_id = "stub-tenant-id"
        request.state.tenant_name = "stub-tenant"

        # Process request
        response = await call_next(request)

        return response


class CatalogMiddleware:
    """Catalog module middleware collection."""

    @staticmethod
    def get_middleware_stack() -> list[BaseHTTPMiddleware]:
        """
        Get the middleware stack for catalog module.

        Returns:
            List of middleware instances
        """
        return [
            RequestIdMiddleware(),
            TimingMiddleware(),
            LoggingMiddleware(),
            AuthStubMiddleware(),
        ]

    @staticmethod
    def setup_middleware(app) -> None:
        """
        Set up middleware for the FastAPI app.

        Args:
            app: FastAPI application instance
        """
        middleware_stack = CatalogMiddleware.get_middleware_stack()

        for middleware in middleware_stack:
            app.add_middleware(type(middleware))

        logger.info(f"Added {len(middleware_stack)} middleware to catalog module")

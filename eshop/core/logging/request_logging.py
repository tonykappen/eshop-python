"""HTTP request/response auto-logging middleware."""

import time
import uuid
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic HTTP request/response logging."""

    def __init__(
        self,
        app: Any,
        log_request_body: bool = False,
        log_response_body: bool = False,
        exclude_paths: list[str] | None = None,
        exclude_health_checks: bool = True,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.exclude_paths = exclude_paths or []
        self.exclude_health_checks = exclude_health_checks

        # Add common health check paths to exclusion list
        if exclude_health_checks:
            self.exclude_paths.extend(
                [
                    "/health",
                    "/health/",
                    "/health/detailed",
                    "/health/database",
                    "/health/redis",
                    "/health/rabbitmq",
                    "/health/keycloak",
                    "/api/v1/health",
                    "/docs",
                    "/redoc",
                    "/openapi.json",
                ]
            )

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        """Process request and response with automatic logging."""

        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Extract request information
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
        }

        # Log request body if enabled (be careful with sensitive data)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body (this consumes the stream)
                body = await request.body()
                if body:
                    # Don't log if it looks like binary data
                    try:
                        request_info["body"] = body.decode("utf-8")[:1000]  # Limit size
                    except UnicodeDecodeError:
                        request_info["body"] = f"<binary data: {len(body)} bytes>"
            except Exception as e:
                request_info["body_error"] = str(e)

        # Log incoming request
        logger.info("HTTP Request", **request_info)

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Extract response information
            response_info = {
                "request_id": request_id,
                "status_code": response.status_code,
                "processing_time_ms": round(processing_time * 1000, 2),
                "response_headers": dict(response.headers),
            }

            # Log response body if enabled and small enough
            if self.log_response_body and hasattr(response, "body"):
                try:
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    ):
                        # Only log JSON responses and limit size
                        body_size = len(response.body) if response.body else 0
                        if body_size < 10000:  # 10KB limit
                            response_info["body"] = (
                                response.body.decode("utf-8") if response.body else None
                            )
                        else:
                            response_info["body"] = (
                                f"<large response: {body_size} bytes>"
                            )
                except Exception as e:
                    response_info["body_error"] = str(e)

            # Log response
            if response.status_code >= 400:
                logger.warning("HTTP Response (Error)", **response_info)
            else:
                logger.info("HTTP Response", **response_info)

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time

            # Log error
            logger.error(
                "HTTP Request Failed",
                request_id=request_id,
                processing_time_ms=round(processing_time * 1000, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers (common in load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"


def add_request_logging_middleware(
    app: Any,
    log_request_body: bool = False,
    log_response_body: bool = False,
    exclude_paths: list[str] | None = None,
    exclude_health_checks: bool = True,
) -> None:
    """Add request logging middleware to FastAPI app."""
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        exclude_paths=exclude_paths,
        exclude_health_checks=exclude_health_checks,
    )

    logger.info(
        "Request logging middleware added",
        log_request_body=log_request_body,
        log_response_body=log_response_body,
        exclude_health_checks=exclude_health_checks,
    )

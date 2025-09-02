"""HTTP request/response auto-logging middleware."""

import time
import uuid
from typing import Any, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import get_logger, log_security_event, _sanitize_log_data

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
        # Store request ID in request state for exception handling
        request.state.request_id = request_id
        start_time = time.time()

        # Extract user information from request state
        user = getattr(request.state, 'user', None)
        user_id = user.sub if user else None
        session_id = request_id  # Use request_id as session_id for now

        # Extract request information (sanitized)
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "user_id": user_id,
            "session_id": session_id[:6] if session_id else None,
            "authentication_method": self._get_auth_method(request),
            "authorization_outcome": "authenticated" if user else "unauthenticated",
        }

        # Log request body if enabled (be careful with sensitive data)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Read body (this consumes the stream)
                body = await request.body()
                if body:
                    # Don't log if it looks like binary data
                    try:
                        body_text = body.decode("utf-8")[:1000]  # Limit size
                        # Sanitize sensitive data in body
                        sanitized_body = _sanitize_log_data({"body": body_text})
                        request_info.update(sanitized_body)
                    except UnicodeDecodeError:
                        request_info["body"] = f"<binary data: {len(body)} bytes>"
            except Exception as e:
                request_info["body_error"] = str(e)

        # Log incoming request as security event
        await log_security_event(
            logger=logger,
            event_type="http_request",
            user_id=user_id,
            session_id=session_id,
            authentication_method=request_info["authentication_method"],
            authorization_outcome=request_info["authorization_outcome"],
            source_ip=request_info["client_ip"],
            user_agent=request_info["user_agent"],
            # Remove duplicate fields that are already in request_info
            method=request_info["method"],
            path=request_info["path"],
            client_ip=request_info["client_ip"],
            request_id=request_id,
        )

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
                "response_headers": self._sanitize_headers(dict(response.headers)),
                "user_id": user_id,
                "session_id": session_id[:6] if session_id else None,
                "authorization_outcome": "success" if response.status_code < 400 else "failure",
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
                            body_text = response.body.decode("utf-8") if response.body else None
                            # Sanitize sensitive data in response body
                            sanitized_body = _sanitize_log_data({"body": body_text})
                            response_info.update(sanitized_body)
                        else:
                            response_info["body"] = (
                                f"<large response: {body_size} bytes>"
                            )
                except Exception as e:
                    response_info["body_error"] = str(e)

            # Log response as security event
            await log_security_event(
                logger=logger,
                event_type="http_response",
                user_id=user_id,
                session_id=session_id,
                status_code=response.status_code,
                authorization_outcome=response_info["authorization_outcome"],
                processing_time_ms=response_info["processing_time_ms"],
                request_id=response_info["request_id"],
            )

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            processing_time = time.time() - start_time

            # Log error as security event
            await log_security_event(
                logger=logger,
                event_type="http_request_failed",
                user_id=user_id,
                session_id=session_id,
                status_code=500,
                authorization_outcome="failure",
                error=str(e),
                error_type=type(e).__name__,
                processing_time_ms=round(processing_time * 1000, 2),
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

    def _get_auth_method(self, request: Request) -> Optional[str]:
        """Determine authentication method used."""
        auth_header = request.headers.get("authorization", "")
        
        if auth_header.startswith("Bearer "):
            return "bearer_token"
        elif auth_header.startswith("Basic "):
            return "basic_auth"
        elif "cookie" in request.headers:
            return "session_cookie"
        elif request.headers.get("x-api-key"):
            return "api_key"
        
        return None

    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive information from headers."""
        sensitive_headers = [
            'authorization', 'cookie', 'x-api-key', 'x-client-secret',
            'x-auth-token', 'x-bearer-token'
        ]
        
        sanitized = {}
        for key, value in headers.items():
            if any(sensitive in key.lower() for sensitive in sensitive_headers):
                if isinstance(value, str) and len(value) > 0:
                    sanitized[key] = f"<REDACTED:{len(value)}>"
                else:
                    sanitized[key] = "<REDACTED>"
            else:
                sanitized[key] = value
        
        return sanitized


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

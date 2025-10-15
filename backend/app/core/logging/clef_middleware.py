"""CLEF-compliant HTTP request/response logging middleware with W3C trace correlation."""

import os
import socket
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging.clef_dispatcher import get_dispatcher
from app.core.logging.w3c_trace import (
    extract_or_generate_trace_context,
    format_traceparent,
)


def get_service_metadata() -> dict[str, Any]:
    """Get service metadata from environment."""
    return {
        "service": os.getenv("SERVICE_NAME", "eshop-api"),
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "env": os.getenv("ENVIRONMENT", "dev"),
    }


def get_host_metadata() -> dict[str, Any]:
    """Get host/container metadata."""
    return {
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "thread": "MainThread",  # Can be enhanced with actual thread name
        "node": os.getenv("NODE_NAME"),
        "container_id": os.getenv("HOSTNAME"),  # Often set to container ID
        "image": os.getenv("CONTAINER_IMAGE"),
    }


def create_clef_event(
    event_name: str,
    level: str,
    logger: str = "app.core.logging.request_logging",
    module: str = "app.core.logging.request_logging",
    function: str = "logging_middleware",
    line: int = 0,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create a CLEF-compliant log event.

    Args:
        event_name: Event name (e.g., "begin_request", "response_sent")
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger: Logger name
        module: Module name
        function: Function name
        line: Line number
        **kwargs: Additional fields to include in the event

    Returns:
        CLEF-formatted event dictionary
    """
    event = {
        "@t": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "@l": level.upper(),
        "@m": event_name,
        **get_service_metadata(),
        "logger": logger,
        "module": module,
        "function": function,
        "line": line,
        **get_host_metadata(),
    }

    # Add additional fields
    event.update(kwargs)

    # Remove None values
    event = {k: v for k, v in event.items() if v is not None}

    return event


class CLEFLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for CLEF-compliant request/response logging with W3C trace correlation.

    Emits:
    - begin_request: When request is received
    - response_sent: When response is sent (with timings and outcome)
    """

    def __init__(
        self,
        app: Any,
        exclude_paths: list[str] | None = None,
        exclude_health_checks: bool = True,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []

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

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request and response with CLEF logging."""

        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        dispatcher = get_dispatcher()
        if not dispatcher:
            # No dispatcher, skip logging
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Parse or generate W3C trace context
        traceparent_raw = request.headers.get("traceparent")
        tracestate = request.headers.get("tracestate")
        trace_ctx = extract_or_generate_trace_context(traceparent_raw, tracestate)

        # Store trace context in request state
        request.state.trace_context = trace_ctx

        # Set trace context in contextvars for propagation to all logs
        from app.core.logging.trace_context import set_trace_context

        set_trace_context(trace_ctx.trace_id, trace_ctx.span_id, request_id)

        # Extract identity/tenant/roles from JWT or other auth
        user = getattr(request.state, "user", None)
        auth_subject = user.sub if user and hasattr(user, "sub") else None
        user_id = user.sub if user and hasattr(user, "sub") else None
        tenant_id = getattr(user, "tenant_id", None) if user else None
        roles = getattr(user, "roles", []) if user else []
        token_id = getattr(user, "jti", None) if user else None

        # Extract request descriptors
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        scheme = request.url.scheme
        http_version = request.scope.get("http_version", "1.1")
        referer = request.headers.get("referer")
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else None

        # Calculate request size
        request_size = int(request.headers.get("content-length", 0))

        # Extract route and path params if available
        route = None
        path_params = {}
        if hasattr(request, "scope") and "route" in request.scope:
            route_obj = request.scope.get("route")
            if route_obj and hasattr(route_obj, "path"):
                route = route_obj.path
        if hasattr(request, "path_params"):
            path_params = dict(request.path_params)

        # Session ID prefix (first 6 chars of request_id)
        session_id_prefix = request_id[:6]

        # Start timer
        start_time = time.time()
        time.perf_counter()

        # EMIT begin_request event
        begin_event = create_clef_event(
            event_name="begin_request",
            level="INFO",
            logger="app.core.logging.request_logging",
            module="app.core.logging.clef_middleware",
            function="dispatch",
            line=124,
            request_id=request_id,
            traceparent_raw=traceparent_raw or format_traceparent(trace_ctx),
            tracestate=tracestate,
            trace_id=trace_ctx.trace_id,
            span_id=trace_ctx.span_id,
            parent_span_id=trace_ctx.parent_span_id,
            session_id_prefix=session_id_prefix,
            auth_subject=auth_subject,
            token_id=token_id,
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            client_ip=client_ip,
            user_agent=user_agent,
            scheme=scheme,
            http_version=http_version,
            referer=referer,
            method=method,
            path=path,
            route=route,
            path_params=path_params,
            query=query,
            request_size=request_size,
            dispatcher_lag_ms=0,  # Can be calculated if needed
        )

        await dispatcher.enqueue(begin_event)

        # Process request
        response = None
        exception_info = None

        try:
            response = await call_next(request)

        except Exception as e:
            # Capture exception
            exception_info = {
                "exc_type": type(e).__name__,
                "exc_message": str(e),
                "exc_stack": self._format_exception(e),
                "@x": self._format_exception(e),
            }
            # Re-raise to let error handlers deal with it
            raise

        finally:
            # Calculate timings
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Extract DB/cache timings from request state if available
            db_time_ms = getattr(request.state, "db_time_ms", 0)
            cache_time_ms = getattr(request.state, "cache_time_ms", 0)
            cache_hit = getattr(request.state, "cache_hit", None)
            app_time_ms = max(0, duration_ms - db_time_ms - cache_time_ms)

            # Extract policy info if available
            policy = {
                "rate_limited": getattr(request.state, "rate_limited", False),
                "retry_count": getattr(request.state, "retry_count", 0),
            }

            # Extract response info
            status_code = response.status_code if response else 500
            response_size = 0
            content_type = None

            if response:
                response_size = int(response.headers.get("content-length", 0))
                content_type = response.headers.get("content-type")

            # Determine log level based on status
            if status_code >= 500 or exception_info:
                level = "ERROR"
            elif status_code >= 400:
                level = "WARNING"
            else:
                level = "INFO"

            # Extract operation_id and controller if available
            operation_id = getattr(request.state, "operation_id", None)
            controller = getattr(request.state, "controller", None)

            # EMIT response_sent event
            response_event = create_clef_event(
                event_name="response_sent",
                level=level,
                logger="app.core.logging.request_logging",
                module="app.core.logging.clef_middleware",
                function="dispatch",
                line=124,
                request_id=request_id,
                traceparent_raw=traceparent_raw or format_traceparent(trace_ctx),
                tracestate=tracestate,
                trace_id=trace_ctx.trace_id,
                span_id=trace_ctx.span_id,
                parent_span_id=trace_ctx.parent_span_id,
                status_code=status_code,
                response_size=response_size,
                content_type=content_type,
                duration_ms=duration_ms,
                db_time_ms=db_time_ms,
                cache_time_ms=cache_time_ms,
                cache_hit=cache_hit,
                app_time_ms=app_time_ms,
                policy=policy,
                success=(status_code < 400 and not exception_info),
                dispatcher_lag_ms=0,
                operation_id=operation_id,
                controller=controller,
                **(exception_info or {}),
            )

            await dispatcher.enqueue(response_event)

            # Echo traceparent in response headers if we have a response
            if response:
                response.headers["traceparent"] = format_traceparent(trace_ctx)

            # Clear trace context after request
            from app.core.logging.trace_context import clear_trace_context

            clear_trace_context()

        return response

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

    def _format_exception(self, exc: Exception) -> str:
        """Format exception for logging."""
        import traceback

        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))


def add_clef_logging_middleware(
    app: Any,
    exclude_paths: list[str] | None = None,
    exclude_health_checks: bool = True,
) -> None:
    """Add CLEF logging middleware to FastAPI app."""
    app.add_middleware(
        CLEFLoggingMiddleware,
        exclude_paths=exclude_paths,
        exclude_health_checks=exclude_health_checks,
    )

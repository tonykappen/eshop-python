"""CLEF-compliant HTTP request/response logging middleware with W3C trace correlation."""

import inspect
import os
import socket
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging.base_logger import BaseLogger
from app.core.logging.clef_dispatcher import get_dispatcher
from app.core.logging.w3c_trace import (
    extract_or_generate_trace_context,
    format_traceparent,
)

logger = BaseLogger(__name__)


def get_service_metadata() -> dict[str, Any]:
    """Get service metadata from environment."""
    return {
        "service": os.getenv("SERVICE_NAME", "eshop-api"),
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "env": os.getenv("ENVIRONMENT", "dev"),
    }


def get_host_metadata() -> dict[str, Any]:
    """Get host/container metadata with all required fields."""
    hostname = socket.gethostname()

    # Get FQDN if available
    try:
        hostname_fqdn = socket.getfqdn()
    except Exception:
        hostname_fqdn = hostname

    # Get internal IP address
    try:
        # Get primary IP (not loopback)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = ""

    # Get port from environment (set by uvicorn or deployment)
    port = int(os.getenv("PORT", os.getenv("UVICORN_PORT", "8000")))

    # Get script name (entry point)
    script_name = os.getenv("SCRIPT_NAME", "app/main.py")

    return {
        "host": hostname,
        "hostname_fqdn": hostname_fqdn,
        "ip": ip,
        "port": port,
        "pid": os.getpid(),
        "thread": "MainThread",  # Can be enhanced with actual thread name
        "node": os.getenv("NODE_NAME"),
        "container_id": os.getenv("HOSTNAME"),  # Often set to container ID
        "image": os.getenv("CONTAINER_IMAGE"),
        "script_name": script_name,
    }


# Message templates for canonical event types (per Logging Developer Document 4.md)
MESSAGE_TEMPLATES: dict[str, str] = {
    # HTTP / Presentation Layer
    "begin_request": "Begin request {method} {path}",
    "response_sent": "Response sent {method} {path} → {status_code} in {duration_ms} ms",
    # Mediator / Application Layer
    "mediator_operation_started": "Mediator operation started {operation_name}",
    "mediator_operation_ended": "Mediator operation ended {operation_name} in {duration_ms} ms (success={success})",
    # Validation & Mapping
    "request_validation_started": "Request validation started {operation_name}",
    "request_validation_completed": "Request validation completed {operation_name} in {duration_ms} ms (success={success})",
    "domain_object_conversion": "Converted request DTO to domain object {operation_name}",
    "orm_object_conversion": "Converted domain object to ORM entity {entity_name}",
    # Background Tasks
    "background_task_started": "Background task started {task_name}",
    "background_task_completed": "Background task completed {task_name} in {duration_ms} ms (success={success})",
    # Domain Layer
    "domain_operation_started": "Domain operation started {operation_name} on {aggregate_type}",
    "domain_operation_ended": "Domain operation ended {operation_name} on {aggregate_type} in {duration_ms} ms (success={success})",
    "domain_event_published": "Domain event published {event_name} for {aggregate_type}",
    "domain_event_processed": "Domain event processed {event_name} by {handler_name} in {duration_ms} ms (success={success})",
    # Outbox Pattern
    "outbox_message_stored": "Outbox message stored {message_id} ({event_name})",
    "outbox_message_processed": "Outbox message processed {message_id} ({event_name}) → {destination} in {duration_ms} ms (success={success}, retries={retry_count})",
    # Integration Layer
    "integration_event_published": "Integration event published {event_name} to {destination}",
    "integration_event_processed": "Integration event processed {event_name} from {source} by {handler_name} in {duration_ms} ms (success={success})",
    # Database
    "db_query": "Database query executed {sql} in {duration_ms} ms (success={success})",
    # Cache Operations
    "cache_get_started": "Cache GET started {cache_key} ({scope})",
    "cache_get_completed": "Cache GET completed {cache_key} ({scope}) in {duration_ms} ms (hit={hit})",
    "cache_get_miss": "Cache MISS {cache_key} ({scope}) in {duration_ms} ms",
    "cache_set": "Cache SET {cache_key} ({scope}) in {duration_ms} ms",
    "cache_delete": "Cache DELETE {cache_key} ({scope})",
    "cache_clear": "Cache CLEAR {pattern} ({scope})",
    # Commit Lifecycle
    "db_interceptor_published": "Database commit started ({entity_count} entities)",
    "db_interceptor_processed": "Database commit completed in {duration_ms} ms (success={success}, {entity_count} entities)",
    "db_interceptor_rollback": "Database commit rolled back in {duration_ms} ms (error={error_type})",
}


def _get_message_template(message_name: str) -> str:
    """
    Get message template for a canonical event type.

    Args:
        message_name: Canonical event type name

    Returns:
        Message template with placeholders, or empty string if not found
    """
    return MESSAGE_TEMPLATES.get(message_name, "")


def _render_message(template: str, **kwargs: Any) -> str:
    """
    Render a message template with provided values.

    Args:
        template: Message template with placeholders like {method}
        **kwargs: Values to substitute in template

    Returns:
        Rendered message string
    """
    if not template:
        return ""

    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        # If template rendering fails, return template as-is
        return template


def create_clef_event(
    event_name: str,
    level: str,
    logger: str = "app.core.logging.request_logging",
    module: str = "app.core.logging.request_logging",
    function: str = "logging_middleware",
    line: int = 0,
    message_template: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Create a CLEF-compliant log event with message_name and @mt fields.

    Args:
        event_name: Canonical event name (message_name) - e.g., "begin_request", "response_sent"
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger: Logger name
        module: Module name
        function: Function name
        line: Line number
        message_template: Optional message template. If not provided, will look up from MESSAGE_TEMPLATES
        **kwargs: Additional fields to include in the event (used for message rendering)

    Returns:
        CLEF-formatted event dictionary with message_name, @mt, and rendered @m
    """
    # Get message template (use provided or lookup)
    template = message_template or _get_message_template(event_name)

    # Render the message if template exists
    rendered_message = _render_message(template, **kwargs) if template else event_name

    event = {
        "@t": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "@l": level.upper(),
        "@m": rendered_message,  # Rendered message
        "message_name": event_name,  # Canonical event type
        **get_service_metadata(),
        "logger": logger,
        "module": module,
        "function": function,
        "line": line,
        **get_host_metadata(),
    }

    # Only add @mt if template has a value (don't include empty string)
    # This prevents Seq from prioritizing empty @mt over @m
    if template and template.strip():
        event["@mt"] = template

    # Add additional fields
    event.update(kwargs)

    # Keep all values including None for consistent structure
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
        exclude_health_checks: bool = False,
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []

        # Health checks are now logged by default
        # Only exclude if explicitly requested
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
        from app.core.logging.trace_context import (
            set_http_request_context,
            set_identity_context,
            set_operation_context,
            set_trace_context,
        )

        set_trace_context(trace_ctx.trace_id, trace_ctx.span_id, request_id)

        # Initialize operation_id and controller early to avoid UnboundLocalError
        operation_id = None
        controller = None

        # Extract identity/tenant/roles from JWT or other auth
        # Note: User may not be available yet if auth middleware runs after this one
        # We'll re-extract in the finally block after call_next to ensure we have the user
        user = getattr(request.state, "user", None)
        auth_subject = user.sub if user and hasattr(user, "sub") else None
        user_id = auth_subject  # Use auth_subject for consistency

        # Extract Keycloak-specific fields (per document requirements)
        kc_user_id = user.sub if user and hasattr(user, "sub") else None
        kc_user_name = getattr(user, "preferred_username", None) if user else None

        tenant_id = getattr(user, "tenant_id", None) if user else None
        roles = getattr(user, "roles", []) if user else []
        token_id = getattr(user, "jti", None) if user else None

        # Get session_id from Keycloak (sid claim) or fallback to request_id
        session_id = getattr(user, "sid", None) if user else None
        if not session_id:
            session_id = request_id  # Fallback to request_id if no Keycloak session

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
        # operation_id and controller already initialized above

        # Try to get route from request scope (may not be available yet)
        if hasattr(request, "scope") and "route" in request.scope:
            route_obj = request.scope.get("route")
            if route_obj:
                if hasattr(route_obj, "path"):
                    route = route_obj.path
                # Extract operation_id from route name if available
                if hasattr(route_obj, "name") and route_obj.name:
                    operation_id = route_obj.name

        if hasattr(request, "path_params"):
            path_params = dict(request.path_params)

        # Extract operation_id and controller from path if not already set
        # Derive from path: /api/v1/products/ -> get_products
        if not operation_id and path:
            # Clean path: remove leading/trailing slashes and split
            clean_path = path.strip("/")
            if clean_path:
                path_parts = [
                    p for p in clean_path.split("/") if p
                ]  # Remove empty parts
                if path_parts:
                    # Get the last meaningful part (e.g., "products" from "/api/v1/products/")
                    last_part = path_parts[-1]
                    # Create operation_id: method + resource (e.g., "get_products")
                    operation_id = f"{method.lower()}_{last_part}".replace(
                        "-", "_"
                    ).lower()
                    # Remove trailing underscores and clean up
                    operation_id = operation_id.strip("_")

        # Extract controller from route or handler
        # This will be set by handlers, but we can try to infer from path
        if not controller and path:
            # Try to extract controller from path: /api/v1/products -> Products
            path_parts = [
                p for p in path.strip("/").split("/") if p
            ]  # Remove empty parts
            if len(path_parts) >= 2:
                # Use last meaningful part (skip "api", "v1", etc.)
                controller = path_parts[-1]
                # Capitalize for controller name (e.g., "products" -> "Products")
                controller = controller.replace("-", "_").title().replace("_", "")
            elif len(path_parts) == 1:
                controller = path_parts[0].replace("-", "_").title().replace("_", "")

        # Set operation context for propagation to all logs (after extraction)
        set_operation_context(operation_id=operation_id, controller=controller)

        # Session ID prefix (first 6 chars of request_id or session_id)
        session_id_prefix = (
            session_id[:6] if session_id and len(session_id) >= 6 else request_id[:6]
        )

        # Set identity context EARLY so all logs during request processing have access to it
        # This will be updated in the finally block if user becomes available later
        set_identity_context(
            kc_user_id=kc_user_id,
            kc_user_name=kc_user_name,
            user_id=user_id,
            auth_subject=auth_subject,
            roles=roles,
            token_id=token_id,
            session_id=session_id,
            tenant_id=tenant_id,
        )

        # Set HTTP request context in contextvars for propagation to all logs
        set_http_request_context(
            method=method,
            path=path,
            client_ip=client_ip,
            user_agent=user_agent,
            scheme=scheme,
            http_version=http_version,
            referer=referer,
            route=route,
            path_params=path_params,
            query=query,
            request_size=request_size,
            parent_span_id=trace_ctx.parent_span_id,
            traceparent_raw=traceparent_raw or format_traceparent(trace_ctx),
            tracestate=tracestate,
            session_id_prefix=session_id_prefix,
        )

        # Start timer
        start_time = time.time()
        time.perf_counter()

        # Get actual location info for consistent logging structure
        frame = inspect.currentframe()
        try:
            # Get the current frame (dispatch method) info
            if frame:
                module_name = frame.f_globals.get(
                    "__name__", "app.core.logging.clef_middleware"
                )
                function_name = frame.f_code.co_name
                line_number = frame.f_lineno
            else:
                module_name = "app.core.logging.clef_middleware"
                function_name = "dispatch"
                line_number = 205
        finally:
            del frame

        # EMIT begin_request event
        begin_event = create_clef_event(
            event_name="begin_request",
            level="INFO",
            logger=module_name,
            module=module_name,
            function=function_name,
            line=line_number,
            # Template rendering parameters
            method=method,
            path=path,
            # Additional fields
            request_id=request_id,
            traceparent_raw=traceparent_raw or format_traceparent(trace_ctx),
            tracestate=tracestate,
            trace_id=trace_ctx.trace_id,
            span_id=trace_ctx.span_id,
            parent_span_id=trace_ctx.parent_span_id,
            session_id=session_id,  # Keycloak session ID or request_id
            session_id_prefix=(
                session_id[:6]
                if session_id and len(session_id) >= 6
                else request_id[:6]
            ),
            auth_subject=auth_subject,
            kc_user_id=kc_user_id,  # Keycloak user ID
            kc_user_name=kc_user_name,  # Keycloak username
            token_id=token_id,
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles,
            operation_id=operation_id,
            controller=controller,
            client_ip=client_ip,
            user_agent=user_agent,
            scheme=scheme,
            http_version=http_version,
            referer=referer,
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
            try:
                # Re-extract user info AFTER call_next (auth middleware has now run)
                # This ensures we have the user for response_sent event
                user = getattr(request.state, "user", None)
                if user:
                    # Update identity fields with actual user data
                    auth_subject = user.sub if hasattr(user, "sub") else auth_subject
                    user_id = auth_subject
                    kc_user_id = user.sub if hasattr(user, "sub") else None
                    kc_user_name = getattr(user, "preferred_username", None)
                    tenant_id = getattr(user, "tenant_id", None)
                    roles = getattr(user, "roles", [])
                    token_id = getattr(user, "jti", None)
                    # Get session_id from Keycloak (sid claim) or fallback to request_id
                    session_id = getattr(user, "sid", None) or request_id

                # Set identity context for propagation to all logs
                set_identity_context(
                    kc_user_id=kc_user_id,
                    kc_user_name=kc_user_name,
                    user_id=user_id,
                    auth_subject=auth_subject,
                    roles=roles,
                    token_id=token_id,
                    session_id=session_id,
                    tenant_id=tenant_id,
                )

                # Update operation_id and controller from request state if set by handlers
                # Use the values from outer scope (defined earlier) as defaults
                current_operation_id = (
                    getattr(request.state, "operation_id", None) or operation_id
                )
                current_controller = (
                    getattr(request.state, "controller", None) or controller
                )
                set_operation_context(
                    operation_id=current_operation_id, controller=current_controller
                )

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

                # Use ERROR level for any error condition (4xx or 5xx)
                # This provides consistent error visibility in logs
                if status_code >= 400 or exception_info:
                    level = "ERROR"
                else:
                    level = "INFO"

                # Extract operation_id and controller if available (may have been set by handlers)
                operation_id = getattr(request.state, "operation_id", operation_id)
                controller = getattr(request.state, "controller", controller)

                # Determine data_source based on cache hit and DB usage
                if cache_hit is True:
                    data_source = "cache"
                elif db_time_ms > 0:
                    data_source = "db"
                else:
                    data_source = "none"

                # Get actual location info for consistent logging structure
                frame = inspect.currentframe()
                try:
                    # Get the current frame (dispatch method) info
                    if frame:
                        module_name = frame.f_globals.get(
                            "__name__", "app.core.logging.clef_middleware"
                        )
                        function_name = frame.f_code.co_name
                        line_number = frame.f_lineno
                    else:
                        module_name = "app.core.logging.clef_middleware"
                        function_name = "dispatch"
                        line_number = 295
                finally:
                    del frame

                # EMIT response_sent event
                success_value = status_code < 400 and not exception_info
                response_event = create_clef_event(
                    event_name="response_sent",
                    level=level,
                    logger=module_name,
                    module=module_name,
                    function=function_name,
                    line=line_number,
                    # Template rendering parameters
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    # Additional fields
                    request_id=request_id,
                    traceparent_raw=traceparent_raw or format_traceparent(trace_ctx),
                    tracestate=tracestate,
                    trace_id=trace_ctx.trace_id,
                    span_id=trace_ctx.span_id,
                    parent_span_id=trace_ctx.parent_span_id,
                    session_id=session_id,  # Keycloak session ID or request_id
                    session_id_prefix=(
                        session_id[:6]
                        if session_id and len(session_id) >= 6
                        else request_id[:6]
                    ),
                    auth_subject=auth_subject,
                    kc_user_id=kc_user_id,  # Keycloak user ID
                    kc_user_name=kc_user_name,  # Keycloak username
                    token_id=token_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    roles=roles,
                    response_size=response_size,
                    content_type=content_type,
                    db_time_ms=db_time_ms,
                    cache_time_ms=cache_time_ms,
                    cache_hit=cache_hit,
                    app_time_ms=app_time_ms,
                    data_source=data_source,  # "db", "cache", or "none"
                    policy=policy,
                    success=success_value,
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
            except Exception as log_exc:
                logger.log_warning_with_context(
                    "Failed to emit response_sent CLEF event",
                    context={"error": str(log_exc), "path": path, "method": method},
                )
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
    exclude_health_checks: bool = False,
) -> None:
    """Add CLEF logging middleware to FastAPI app."""
    app.add_middleware(
        CLEFLoggingMiddleware,
        exclude_paths=exclude_paths,
        exclude_health_checks=exclude_health_checks,
    )

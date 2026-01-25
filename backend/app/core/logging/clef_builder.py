"""CLEF event builder that ensures all required fields are present according to the template."""

import os
import socket
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.logging.trace_context import get_request_id, get_span_id, get_trace_id


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


def build_clef_event(
    event_name: str,
    level: str,
    logger: str,
    module: str,
    function: str,
    line: int,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Build a complete CLEF-compliant event with all required fields.

    This function ensures that ALL fields from the CLEF template are present,
    using empty strings or None for fields that don't apply to the specific log type.

    Args:
        event_name: Event name (e.g., "begin_request", "response_sent", or custom message)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger: Logger name
        module: Module name
        function: Function name
        line: Line number
        **kwargs: Additional fields to merge into the event

    Returns:
        Complete CLEF-formatted event dictionary with all required fields
    """
    # Get current timestamp
    timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    # Get service and host metadata
    service_meta = get_service_metadata()
    host_meta = get_host_metadata()

    # Get trace context from contextvars (may be None for non-HTTP logs)
    trace_id = get_trace_id()
    span_id = get_span_id()
    request_id = get_request_id()

    # Generate request_id if not available (for non-HTTP logs)
    if not request_id:
        request_id = str(uuid.uuid4())

    # Generate trace_id and span_id if not available (for non-HTTP logs)
    # Use empty string representation (all zeros) when not in HTTP context
    if not trace_id:
        trace_id = "0" * 32  # Empty trace ID (32 hex chars)
    if not span_id:
        span_id = "0" * 16  # Empty span ID (16 hex chars)

    # Build base CLEF event with ALL required fields
    # Required fields per Logging.Developer.Document.md section 4.1
    event: dict[str, Any] = {
        # CLEF standard fields (required)
        "@t": timestamp,
        "@l": level.upper(),
        "@m": event_name,
        # Service metadata (required)
        "service": service_meta["service"],
        "version": service_meta["version"],
        "env": service_meta["env"],
        # Source information (required)
        "logger": logger,
        "module": module,
        "function": function,
        "line": line,
        # W3C correlation (required - use empty values if not available)
        "request_id": request_id,
        "trace_id": trace_id,
        "span_id": span_id,
        # Host/process metadata (required)
        "host": host_meta["host"],
        "pid": host_meta["pid"],
        "thread": host_meta.get("thread", "MainThread"),
    }

    # 4.2 W3C correlation - ALL fields present (empty if not available)
    event["traceparent_raw"] = (
        kwargs.get("traceparent_raw")
        if kwargs.get("traceparent_raw") is not None
        else ""
    )
    event["tracestate"] = (
        kwargs.get("tracestate") if kwargs.get("tracestate") is not None else ""
    )
    event["parent_span_id"] = (
        kwargs.get("parent_span_id") if kwargs.get("parent_span_id") is not None else ""
    )

    # 4.3 Identity & tenancy - ALL fields present (empty if not available)
    event["session_id_prefix"] = (
        kwargs.get("session_id_prefix")
        if kwargs.get("session_id_prefix") is not None
        else ""
    )
    event["auth_subject"] = (
        kwargs.get("auth_subject") if kwargs.get("auth_subject") is not None else ""
    )
    event["token_id"] = (
        kwargs.get("token_id") if kwargs.get("token_id") is not None else ""
    )
    event["user_id"] = (
        kwargs.get("user_id") if kwargs.get("user_id") is not None else ""
    )
    event["tenant_id"] = (
        kwargs.get("tenant_id") if kwargs.get("tenant_id") is not None else ""
    )
    event["roles"] = kwargs.get("roles") if kwargs.get("roles") is not None else []

    # 4.4 Client & request - ALL fields present (empty if not available)
    event["client_ip"] = (
        kwargs.get("client_ip") if kwargs.get("client_ip") is not None else ""
    )
    event["user_agent"] = (
        kwargs.get("user_agent") if kwargs.get("user_agent") is not None else ""
    )
    event["scheme"] = kwargs.get("scheme") if kwargs.get("scheme") is not None else ""
    event["http_version"] = (
        kwargs.get("http_version") if kwargs.get("http_version") is not None else ""
    )
    event["referer"] = (
        kwargs.get("referer") if kwargs.get("referer") is not None else ""
    )
    event["method"] = kwargs.get("method") if kwargs.get("method") is not None else ""
    event["path"] = kwargs.get("path") if kwargs.get("path") is not None else ""
    event["route"] = kwargs.get("route") if kwargs.get("route") is not None else ""
    event["path_params"] = (
        kwargs.get("path_params") if kwargs.get("path_params") is not None else {}
    )
    event["query"] = kwargs.get("query") if kwargs.get("query") is not None else ""
    event["request_size"] = (
        kwargs.get("request_size") if kwargs.get("request_size") is not None else 0
    )

    # 4.5 Response & timings - ALL fields present (empty/0 if not available)
    event["status_code"] = (
        kwargs.get("status_code") if kwargs.get("status_code") is not None else 0
    )
    event["response_size"] = (
        kwargs.get("response_size") if kwargs.get("response_size") is not None else 0
    )
    event["content_type"] = (
        kwargs.get("content_type") if kwargs.get("content_type") is not None else ""
    )
    event["duration_ms"] = (
        kwargs.get("duration_ms") if kwargs.get("duration_ms") is not None else 0.0
    )
    event["db_time_ms"] = (
        kwargs.get("db_time_ms") if kwargs.get("db_time_ms") is not None else 0.0
    )
    event["cache_time_ms"] = (
        kwargs.get("cache_time_ms") if kwargs.get("cache_time_ms") is not None else 0.0
    )
    event["cache_hit"] = (
        kwargs.get("cache_hit") if kwargs.get("cache_hit") is not None else False
    )
    event["app_time_ms"] = (
        kwargs.get("app_time_ms") if kwargs.get("app_time_ms") is not None else 0.0
    )

    # 4.6 Policy - ALL fields present
    policy = kwargs.get("policy", {})
    event["policy"] = {
        "rate_limited": (
            policy.get("rate_limited")
            if policy.get("rate_limited") is not None
            else False
        ),
        "retry_count": (
            policy.get("retry_count") if policy.get("retry_count") is not None else 0
        ),
        "limit": policy.get("limit") if policy.get("limit") is not None else 0,
        "remaining": (
            policy.get("remaining") if policy.get("remaining") is not None else 0
        ),
        "reset_at": (
            policy.get("reset_at") if policy.get("reset_at") is not None else ""
        ),
    }

    # Success flag
    event["success"] = (
        kwargs.get("success") if kwargs.get("success") is not None else False
    )

    # 4.7 Exceptions - ALL fields present (empty if not available)
    event["exc_type"] = (
        kwargs.get("exc_type") if kwargs.get("exc_type") is not None else ""
    )
    event["exc_message"] = (
        kwargs.get("exc_message") if kwargs.get("exc_message") is not None else ""
    )
    event["exc_stack"] = (
        kwargs.get("exc_stack") if kwargs.get("exc_stack") is not None else ""
    )
    event["@x"] = kwargs.get("@x") if kwargs.get("@x") is not None else ""

    # 4.8 Host / process / infra - ALL fields present (empty if not available)
    event["node"] = host_meta.get("node") if host_meta.get("node") is not None else ""
    event["container_id"] = (
        host_meta.get("container_id")
        if host_meta.get("container_id") is not None
        else ""
    )
    event["image"] = (
        host_meta.get("image") if host_meta.get("image") is not None else ""
    )

    # 4.9 Dispatcher health - ALL fields present
    event["dispatcher_lag_ms"] = (
        kwargs.get("dispatcher_lag_ms")
        if kwargs.get("dispatcher_lag_ms") is not None
        else 0.0
    )
    event["sampled"] = (
        kwargs.get("sampled") if kwargs.get("sampled") is not None else False
    )

    # 4.10 Routing/meta - ALL fields present (empty if not available)
    event["operation_id"] = (
        kwargs.get("operation_id") if kwargs.get("operation_id") is not None else ""
    )
    event["controller"] = (
        kwargs.get("controller") if kwargs.get("controller") is not None else ""
    )

    # Merge any additional fields from kwargs (overrides defaults above)
    for key, value in kwargs.items():
        if key not in event:
            event[key] = value

    # Per user request: ALL fields should be present, even if empty
    # We've already set defaults for all fields above, so just return the event
    # Remove any None values that might have been set (shouldn't happen now, but just in case)
    cleaned_event: dict[str, Any] = {}
    for k, v in event.items():
        if v is not None:
            cleaned_event[k] = v
        else:
            # Set appropriate defaults for None values
            if k in [
                "client_ip",
                "method",
                "path",
                "user_agent",
                "scheme",
                "http_version",
                "referer",
                "route",
                "query",
                "content_type",
                "traceparent_raw",
                "tracestate",
                "parent_span_id",
                "session_id_prefix",
                "auth_subject",
                "token_id",
                "tenant_id",
                "operation_id",
                "controller",
                "node",
                "container_id",
                "image",
                "exc_type",
                "exc_message",
                "exc_stack",
                "@x",
            ]:
                cleaned_event[k] = ""
            elif k in ["user_id", "status_code", "request_size", "response_size"]:
                cleaned_event[k] = 0
            elif k in [
                "duration_ms",
                "db_time_ms",
                "cache_time_ms",
                "app_time_ms",
                "dispatcher_lag_ms",
            ]:
                cleaned_event[k] = 0.0
            elif k in ["cache_hit", "success", "sampled", "rate_limited"]:
                cleaned_event[k] = False
            elif k == "roles":
                cleaned_event[k] = []
            elif k == "path_params":
                cleaned_event[k] = {}
            elif k == "policy":
                cleaned_event[k] = {
                    "rate_limited": False,
                    "retry_count": 0,
                    "limit": 0,
                    "remaining": 0,
                    "reset_at": "",
                }
            else:
                # For any other fields, keep as empty string
                cleaned_event[k] = ""

    return cleaned_event

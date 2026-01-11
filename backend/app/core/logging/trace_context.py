"""Trace context propagation using contextvars."""

from contextvars import ContextVar
from typing import Any

# Context variables for trace propagation
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_span_id: ContextVar[str | None] = ContextVar("span_id", default=None)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)

# Identity context variables
_kc_user_id: ContextVar[str | None] = ContextVar("kc_user_id", default=None)
_kc_user_name: ContextVar[str | None] = ContextVar("kc_user_name", default=None)
_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)
_auth_subject: ContextVar[str | None] = ContextVar("auth_subject", default=None)
_roles: ContextVar[list[str]] = ContextVar("roles", default=[])
_token_id: ContextVar[str | None] = ContextVar("token_id", default=None)
_session_id: ContextVar[str | None] = ContextVar("session_id", default=None)
_tenant_id: ContextVar[str | None] = ContextVar("tenant_id", default=None)

# Operation context variables
_operation_id: ContextVar[str | None] = ContextVar("operation_id", default=None)
_controller: ContextVar[str | None] = ContextVar("controller", default=None)

# HTTP request context variables
_method: ContextVar[str | None] = ContextVar("method", default=None)
_path: ContextVar[str | None] = ContextVar("path", default=None)
_client_ip: ContextVar[str | None] = ContextVar("client_ip", default=None)
_user_agent: ContextVar[str | None] = ContextVar("user_agent", default=None)
_scheme: ContextVar[str | None] = ContextVar("scheme", default=None)
_http_version: ContextVar[str | None] = ContextVar("http_version", default=None)
_referer: ContextVar[str | None] = ContextVar("referer", default=None)
_route: ContextVar[str | None] = ContextVar("route", default=None)
_path_params: ContextVar[dict[str, Any] | None] = ContextVar("path_params", default=None)
_query: ContextVar[str | None] = ContextVar("query", default=None)
_request_size: ContextVar[int | None] = ContextVar("request_size", default=None)
_parent_span_id: ContextVar[str | None] = ContextVar("parent_span_id", default=None)
_traceparent_raw: ContextVar[str | None] = ContextVar("traceparent_raw", default=None)
_tracestate: ContextVar[str | None] = ContextVar("tracestate", default=None)
_session_id_prefix: ContextVar[str | None] = ContextVar("session_id_prefix", default=None)


def set_trace_context(trace_id: str, span_id: str, request_id: str) -> None:
    """Set the current trace context."""
    _trace_id.set(trace_id)
    _span_id.set(span_id)
    _request_id.set(request_id)


def set_identity_context(
    kc_user_id: str | None = None,
    kc_user_name: str | None = None,
    user_id: str | None = None,
    auth_subject: str | None = None,
    roles: list[str] | None = None,
    token_id: str | None = None,
    session_id: str | None = None,
    tenant_id: str | None = None,
) -> None:
    """Set identity context for propagation to all logs."""
    if kc_user_id is not None:
        _kc_user_id.set(kc_user_id)
    if kc_user_name is not None:
        _kc_user_name.set(kc_user_name)
    if user_id is not None:
        _user_id.set(user_id)
    if auth_subject is not None:
        _auth_subject.set(auth_subject)
    if roles is not None:
        _roles.set(roles)
    if token_id is not None:
        _token_id.set(token_id)
    if session_id is not None:
        _session_id.set(session_id)
    if tenant_id is not None:
        _tenant_id.set(tenant_id)


def set_operation_context(operation_id: str | None = None, controller: str | None = None) -> None:
    """Set operation context for propagation to all logs."""
    if operation_id is not None:
        _operation_id.set(operation_id)
    if controller is not None:
        _controller.set(controller)


def set_http_request_context(
    method: str | None = None,
    path: str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    scheme: str | None = None,
    http_version: str | None = None,
    referer: str | None = None,
    route: str | None = None,
    path_params: dict[str, Any] | None = None,
    query: str | None = None,
    request_size: int | None = None,
    parent_span_id: str | None = None,
    traceparent_raw: str | None = None,
    tracestate: str | None = None,
    session_id_prefix: str | None = None,
) -> None:
    """Set HTTP request context for propagation to all logs."""
    if method is not None:
        _method.set(method)
    if path is not None:
        _path.set(path)
    if client_ip is not None:
        _client_ip.set(client_ip)
    if user_agent is not None:
        _user_agent.set(user_agent)
    if scheme is not None:
        _scheme.set(scheme)
    if http_version is not None:
        _http_version.set(http_version)
    if referer is not None:
        _referer.set(referer)
    if route is not None:
        _route.set(route)
    if path_params is not None:
        _path_params.set(path_params)
    if query is not None:
        _query.set(query)
    if request_size is not None:
        _request_size.set(request_size)
    if parent_span_id is not None:
        _parent_span_id.set(parent_span_id)
    if traceparent_raw is not None:
        _traceparent_raw.set(traceparent_raw)
    if tracestate is not None:
        _tracestate.set(tracestate)
    if session_id_prefix is not None:
        _session_id_prefix.set(session_id_prefix)


def get_trace_id() -> str | None:
    """Get the current trace ID."""
    return _trace_id.get()


def get_span_id() -> str | None:
    """Get the current span ID."""
    return _span_id.get()


def get_request_id() -> str | None:
    """Get the current request ID."""
    return _request_id.get()


def get_kc_user_id() -> str | None:
    """Get the current Keycloak user ID."""
    return _kc_user_id.get()


def get_kc_user_name() -> str | None:
    """Get the current Keycloak username."""
    return _kc_user_name.get()


def get_user_id() -> str | None:
    """Get the current user ID."""
    return _user_id.get()


def get_auth_subject() -> str | None:
    """Get the current auth subject."""
    return _auth_subject.get()


def get_roles() -> list[str]:
    """Get the current user roles."""
    return _roles.get() or []


def get_token_id() -> str | None:
    """Get the current token ID."""
    return _token_id.get()


def get_session_id() -> str | None:
    """Get the current session ID."""
    return _session_id.get()


def get_tenant_id() -> str | None:
    """Get the current tenant ID."""
    return _tenant_id.get()


def get_operation_id() -> str | None:
    """Get the current operation ID."""
    return _operation_id.get()


def get_controller() -> str | None:
    """Get the current controller."""
    return _controller.get()


def get_method() -> str | None:
    """Get the current HTTP method."""
    return _method.get()


def get_path() -> str | None:
    """Get the current HTTP path."""
    return _path.get()


def get_client_ip() -> str | None:
    """Get the current client IP."""
    return _client_ip.get()


def get_user_agent() -> str | None:
    """Get the current user agent."""
    return _user_agent.get()


def get_scheme() -> str | None:
    """Get the current scheme."""
    return _scheme.get()


def get_http_version() -> str | None:
    """Get the current HTTP version."""
    return _http_version.get()


def get_referer() -> str | None:
    """Get the current referer."""
    return _referer.get()


def get_route() -> str | None:
    """Get the current route."""
    return _route.get()


def get_path_params() -> dict[str, Any] | None:
    """Get the current path params."""
    return _path_params.get()


def get_query() -> str | None:
    """Get the current query string."""
    return _query.get()


def get_request_size() -> int | None:
    """Get the current request size."""
    return _request_size.get()


def get_parent_span_id() -> str | None:
    """Get the current parent span ID."""
    return _parent_span_id.get()


def get_traceparent_raw() -> str | None:
    """Get the current traceparent raw value."""
    return _traceparent_raw.get()


def get_tracestate() -> str | None:
    """Get the current tracestate."""
    return _tracestate.get()


def get_session_id_prefix() -> str | None:
    """Get the current session ID prefix."""
    return _session_id_prefix.get()


def clear_trace_context() -> None:
    """Clear the current trace context."""
    _trace_id.set(None)
    _span_id.set(None)
    _request_id.set(None)
    _kc_user_id.set(None)
    _kc_user_name.set(None)
    _user_id.set(None)
    _auth_subject.set(None)
    _roles.set([])
    _token_id.set(None)
    _session_id.set(None)
    _tenant_id.set(None)
    _operation_id.set(None)
    _controller.set(None)
    _method.set(None)
    _path.set(None)
    _client_ip.set(None)
    _user_agent.set(None)
    _scheme.set(None)
    _http_version.set(None)
    _referer.set(None)
    _route.set(None)
    _path_params.set(None)
    _query.set(None)
    _request_size.set(None)
    _parent_span_id.set(None)
    _traceparent_raw.set(None)
    _tracestate.set(None)
    _session_id_prefix.set(None)
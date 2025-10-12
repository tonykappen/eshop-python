"""Trace context propagation using contextvars."""

from contextvars import ContextVar

# Context variables for trace propagation
_trace_id: ContextVar[str | None] = ContextVar("trace_id", default=None)
_span_id: ContextVar[str | None] = ContextVar("span_id", default=None)
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_trace_context(trace_id: str, span_id: str, request_id: str) -> None:
    """Set the current trace context."""
    _trace_id.set(trace_id)
    _span_id.set(span_id)
    _request_id.set(request_id)


def get_trace_id() -> str | None:
    """Get the current trace ID."""
    return _trace_id.get()


def get_span_id() -> str | None:
    """Get the current span ID."""
    return _span_id.get()


def get_request_id() -> str | None:
    """Get the current request ID."""
    return _request_id.get()


def clear_trace_context() -> None:
    """Clear the current trace context."""
    _trace_id.set(None)
    _span_id.set(None)
    _request_id.set(None)

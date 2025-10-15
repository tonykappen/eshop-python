"""W3C Trace Context correlation utilities."""

import re
import secrets
from typing import NamedTuple


class TraceContext(NamedTuple):
    """W3C Trace Context parsed from traceparent header."""

    trace_id: str
    span_id: str
    trace_flags: str
    parent_span_id: str | None = None
    tracestate: str | None = None


def parse_traceparent(traceparent: str | None) -> TraceContext | None:
    """
    Parse W3C traceparent header.

    Format: 00-{trace-id}-{parent-id}-{trace-flags}
    Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
    """
    if not traceparent:
        return None

    try:
        parts = traceparent.strip().split("-")
        if len(parts) != 4:
            return None

        version, trace_id, parent_span_id, trace_flags = parts

        # Validate format
        if version != "00":
            return None

        if len(trace_id) != 32 or not re.match(r"^[0-9a-f]{32}$", trace_id):
            return None

        if len(parent_span_id) != 16 or not re.match(r"^[0-9a-f]{16}$", parent_span_id):
            return None

        if len(trace_flags) != 2 or not re.match(r"^[0-9a-f]{2}$", trace_flags):
            return None

        # Generate new span_id for this service
        span_id = generate_span_id()

        return TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=trace_flags,
            parent_span_id=parent_span_id,
            tracestate=None,
        )
    except Exception:
        return None


def generate_trace_id() -> str:
    """Generate a new W3C-compliant trace ID (32 hex chars)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate a new W3C-compliant span ID (16 hex chars)."""
    return secrets.token_hex(8)


def generate_traceparent(
    trace_id: str | None = None,
    span_id: str | None = None,
    trace_flags: str = "01",
) -> str:
    """
    Generate a W3C traceparent header.

    Args:
        trace_id: Existing trace ID or None to generate new one
        span_id: Existing span ID or None to generate new one
        trace_flags: Trace flags (default "01" = sampled)

    Returns:
        traceparent header string
    """
    if not trace_id:
        trace_id = generate_trace_id()

    if not span_id:
        span_id = generate_span_id()

    return f"00-{trace_id}-{span_id}-{trace_flags}"


def extract_or_generate_trace_context(
    traceparent: str | None, tracestate: str | None = None
) -> TraceContext:
    """
    Extract trace context from headers or generate new one.

    Args:
        traceparent: W3C traceparent header value
        tracestate: W3C tracestate header value

    Returns:
        TraceContext with trace_id, span_id, and optional parent_span_id
    """
    ctx = parse_traceparent(traceparent)

    if ctx:
        # Update with tracestate if provided
        return ctx._replace(tracestate=tracestate)

    # Generate new context
    return TraceContext(
        trace_id=generate_trace_id(),
        span_id=generate_span_id(),
        trace_flags="01",
        parent_span_id=None,
        tracestate=tracestate,
    )


def format_traceparent(ctx: TraceContext) -> str:
    """Format TraceContext back into traceparent header."""
    return f"00-{ctx.trace_id}-{ctx.span_id}-{ctx.trace_flags}"

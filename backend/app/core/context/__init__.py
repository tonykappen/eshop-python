"""Context module for request context management."""

# Export all context functions
from app.core.context.application_context import RequestContext
from app.core.context.request_context import (clear_trace_context, get_baggage,
                                              get_request_id, get_span_id,
                                              get_trace_context, get_trace_id,
                                              set_http_request_context,
                                              set_identity_context,
                                              set_operation_context,
                                              set_trace_context)

__all__ = [
    "get_trace_id",
    "get_span_id",
    "get_request_id",
    "get_trace_context",
    "get_baggage",
    "set_trace_context",
    "set_identity_context",
    "set_operation_context",
    "set_http_request_context",
    "clear_trace_context",
    "RequestContext",
]

"""Middleware package for FastAPI application."""

from app.core.middleware.auth_middleware import (
    add_auth_middleware,
    get_current_user_optional_from_request,
    get_current_user_required,
)
from app.core.middleware.metrics_middleware import (
    MetricsMiddleware,
    add_metrics_middleware,
)
from app.core.middleware.tracing_middleware import (
    TracingMiddleware,
    add_tracing_middleware,
)

__all__ = [
    # Auth middleware
    "add_auth_middleware",
    "get_current_user_optional_from_request",
    "get_current_user_required",
    # Tracing middleware
    "TracingMiddleware",
    "add_tracing_middleware",
    # Metrics middleware
    "MetricsMiddleware",
    "add_metrics_middleware",
]

"""Tracing middleware - Extracts traceparent + baggage, starts OTEL span."""

import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging.base_logger import BaseLogger
from app.core.logging.trace_context import set_trace_context
from app.core.logging.w3c_trace import (
    extract_or_generate_trace_context,
    format_traceparent,
)
from app.core.observability.baggage import BaggageManager
from app.core.observability.tracing import TracingProvider

logger = BaseLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for OpenTelemetry tracing.

    Extracts traceparent and baggage headers, creates OTEL spans for HTTP requests,
    and propagates trace context to downstream services.
    """

    def __init__(
        self,
        app: Any,
        service_name: str = "eshop-api",
        exclude_paths: list[str] | None = None,
        exclude_health_checks: bool = True,
    ):
        """
        Initialize tracing middleware.

        Args:
            app: FastAPI application
            service_name: Service name for tracer
            exclude_paths: Paths to exclude from tracing
            exclude_health_checks: Whether to exclude health check endpoints
        """
        super().__init__(app)
        self.service_name = service_name
        self.tracer = TracingProvider.get_tracer(service_name)
        self.exclude_paths = exclude_paths or []

        if exclude_health_checks:
            self.exclude_paths.extend(
                [
                    "/health",
                    "/ready",
                    "/liveness",
                    "/metrics",
                    "/docs",
                    "/openapi.json",
                    "/redoc",
                ]
            )

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process request with tracing.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            HTTP response with trace context
        """
        # Skip tracing for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Extract traceparent and baggage from headers
        traceparent_raw = request.headers.get("traceparent")
        tracestate = request.headers.get("tracestate")
        baggage_header = request.headers.get("baggage", "")

        # Extract or generate trace context
        trace_ctx = extract_or_generate_trace_context(traceparent_raw, tracestate)

        # Extract baggage
        baggage = BaggageManager.extract_baggage(dict(request.headers))

        # Store trace context in request state for use by other middleware/handlers
        request.state.trace_context = trace_ctx
        request.state.baggage = baggage

        # Set trace context in contextvars for propagation
        request_id = getattr(request.state, "request_id", None) or str(
            trace_ctx.span_id
        )
        set_trace_context(trace_ctx.trace_id, trace_ctx.span_id, request_id)

        # Start OTEL span if tracer is available
        span = None
        span_context = None
        if self.tracer:
            try:
                # Create span name from HTTP method and path
                span_name = f"{request.method} {request.url.path}"

                # Start span using tracer (OTEL API)
                # Note: This uses the OTEL Python SDK API
                # If using a different OTEL SDK, adapt accordingly
                from opentelemetry import trace

                # Get current span context for parent
                current_span = trace.get_current_span()

                # Start new span (OTEL SDK uses context managers)
                span = self.tracer.start_span(
                    name=span_name,
                    kind=trace.SpanKind.SERVER,
                    context=current_span.get_span_context() if current_span else None,
                )

                # Set span attributes (OTEL semantic conventions)
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.url", str(request.url))
                span.set_attribute("http.route", request.url.path)
                span.set_attribute("http.scheme", request.url.scheme)
                span.set_attribute("http.target", request.url.path)
                span.set_attribute(
                    "http.user_agent", request.headers.get("user-agent", "")
                )
                span.set_attribute("http.request_id", request_id)

                # Add baggage as span attributes
                for key, value in baggage.items():
                    span.set_attribute(f"baggage.{key}", value)

                # Set trace context in span
                span.set_attribute("trace.trace_id", trace_ctx.trace_id)
                span.set_attribute("trace.span_id", trace_ctx.span_id)
                if trace_ctx.parent_span_id:
                    span.set_attribute("trace.parent_span_id", trace_ctx.parent_span_id)

                logger.log_debug_with_context(
                    "Started OTEL span",
                    context={
                        "span_name": span_name,
                        "trace_id": trace_ctx.trace_id,
                        "span_id": trace_ctx.span_id,
                    },
                )
            except ImportError:
                # OTEL SDK not installed - gracefully degrade
                logger.log_debug_with_context(
                    "OpenTelemetry SDK not available, skipping span creation",
                    context={"trace_id": trace_ctx.trace_id},
                )
                span = None
            except Exception as e:
                logger.log_warning_with_context(
                    "Failed to start OTEL span (OTEL may not be configured)",
                    context={"error": str(e), "error_type": type(e).__name__},
                )
                span = None

        # Process request
        start_time = time.time()
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Update span with response information
            if span:
                try:
                    span.set_attribute("http.status_code", response.status_code)
                    span.set_attribute(
                        "http.response_size",
                        int(response.headers.get("content-length", 0)),
                    )
                    span.set_attribute("http.duration_ms", round(duration * 1000, 2))

                    # Mark span as error if status >= 400
                    from opentelemetry import trace

                    if response.status_code >= 400:
                        span.set_status(
                            trace.Status(
                                trace.StatusCode.ERROR, f"HTTP {response.status_code}"
                            )
                        )
                    else:
                        span.set_status(trace.Status(trace.StatusCode.OK))
                except ImportError:
                    # OTEL SDK not installed - skip
                    pass
                except Exception as e:
                    logger.log_warning_with_context(
                        "Failed to update span with response",
                        context={"error": str(e)},
                    )

            # Add traceparent to response headers for downstream services
            if trace_ctx:
                response.headers["traceparent"] = format_traceparent(trace_ctx)

            # Add baggage to response if modified
            if baggage:
                baggage_header = BaggageManager.inject_baggage(baggage)
                if baggage_header:
                    response.headers["baggage"] = baggage_header

            return response

        except Exception as e:
            # Update span with error information
            if span:
                try:
                    from opentelemetry import trace

                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                except ImportError:
                    # OTEL SDK not installed - skip
                    pass
                except Exception:
                    pass

            # Re-raise the exception
            raise

        finally:
            # End span
            if span:
                try:
                    span.end()
                    logger.log_debug_with_context(
                        "Ended OTEL span",
                        context={
                            "trace_id": trace_ctx.trace_id,
                            "span_id": trace_ctx.span_id,
                        },
                    )
                except Exception as e:
                    logger.log_warning_with_context(
                        "Failed to end OTEL span",
                        context={"error": str(e)},
                    )


def add_tracing_middleware(
    app: Any,
    service_name: str = "eshop-api",
    exclude_paths: list[str] | None = None,
    exclude_health_checks: bool = True,
) -> None:
    """
    Add tracing middleware to FastAPI app.

    Args:
        app: FastAPI application
        service_name: Service name for tracer
        exclude_paths: Paths to exclude from tracing
        exclude_health_checks: Whether to exclude health check endpoints
    """
    app.add_middleware(
        TracingMiddleware,
        service_name=service_name,
        exclude_paths=exclude_paths,
        exclude_health_checks=exclude_health_checks,
    )
    logger.log_with_context(
        "Tracing middleware added",
        "info",
        context={"service_name": service_name},
    )

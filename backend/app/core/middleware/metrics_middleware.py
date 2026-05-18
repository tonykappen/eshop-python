"""Metrics middleware - Counts requests & measures latency."""

import time
from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.observability.metrics import MetricsRegistry
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = BaseLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for HTTP request metrics.

    Counts requests and measures latency using Prometheus/OTEL metrics.
    """

    def __init__(
        self,
        app: Any,
        service_name: str = "eshop-api",
        exclude_paths: list[str] | None = None,
        exclude_health_checks: bool = True,
    ):
        """
        Initialize metrics middleware.

        Args:
            app: FastAPI application
            service_name: Service name for metrics
            exclude_paths: Paths to exclude from metrics
            exclude_health_checks: Whether to exclude health check endpoints
        """
        super().__init__(app)
        self.service_name = service_name
        self.meter = MetricsRegistry.get_meter(service_name)
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

        # Initialize metrics attributes to None (will be set in _initialize_metrics)
        self.request_counter = None
        self.request_duration = None
        self.active_requests = None

        # Initialize metrics if meter is available
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """Initialize Prometheus/OTEL metrics."""
        if not self.meter:
            logger.log_warning_with_context(
                "Meter not available, metrics will not be recorded",
                context={"service_name": self.service_name},
            )
            # Ensure attributes are None when meter is not available
            self.request_counter = None
            self.request_duration = None
            self.active_requests = None
            return

        try:
            # HTTP request counter
            self.request_counter = self.meter.create_counter(
                name="http_requests_total",
                description="Total number of HTTP requests",
                unit="1",
            )

            # HTTP request duration histogram
            self.request_duration = self.meter.create_histogram(
                name="http_request_duration_seconds",
                description="HTTP request duration in seconds",
                unit="s",
            )

            # Active requests gauge
            self.active_requests = self.meter.create_up_down_counter(
                name="http_active_requests",
                description="Number of active HTTP requests",
                unit="1",
            )

            logger.log_with_context(
                "Metrics initialized",
                "info",
                context={"service_name": self.service_name},
            )
        except Exception as e:
            logger.log_error_with_context(
                "Failed to initialize metrics",
                error=e,
                context={"service_name": self.service_name},
            )
            self.request_counter = None
            self.request_duration = None
            self.active_requests = None

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """
        Process request with metrics collection.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            HTTP response
        """
        # Skip metrics for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Increment active requests
        if self.active_requests:
            try:
                self.active_requests.add(
                    1,
                    attributes={
                        "method": request.method,
                        "path": request.url.path,
                    },
                )
            except Exception as e:
                logger.log_warning_with_context(
                    "Failed to increment active requests",
                    context={"error": str(e)},
                )

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            self._record_metrics(request, response, duration, success=True)

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration = time.time() - start_time

            # Record metrics with error status
            self._record_metrics(request, None, duration, success=False, error=str(e))

            # Re-raise the exception
            raise

        finally:
            # Decrement active requests
            if self.active_requests:
                try:
                    self.active_requests.add(
                        -1,
                        attributes={
                            "method": request.method,
                            "path": request.url.path,
                        },
                    )
                except Exception as e:
                    logger.log_warning_with_context(
                        "Failed to decrement active requests",
                        context={"error": str(e)},
                    )

    def _record_metrics(
        self,
        request: Request,
        response: Response | None,
        duration: float,
        success: bool,
        error: str | None = None,
    ) -> None:
        """
        Record HTTP request metrics.

        Args:
            request: HTTP request
            response: HTTP response (None if error)
            duration: Request duration in seconds
            success: Whether request was successful
            error: Error message if request failed
        """
        if not self.request_counter or not self.request_duration:
            return

        try:
            # Prepare attributes for metrics
            status_code = response.status_code if response else 500
            status_class = f"{status_code // 100}xx"

            attributes = {
                "method": request.method,
                "path": request.url.path,
                "route": getattr(request.state, "route", request.url.path),
                "status_code": str(status_code),
                "status_class": status_class,
                "service": self.service_name,
            }

            # Add error information if available
            if error:
                attributes["error"] = error
                attributes["error_type"] = "exception"

            # Increment request counter
            self.request_counter.add(1, attributes=attributes)

            # Record request duration
            self.request_duration.record(duration, attributes=attributes)

            logger.log_debug_with_context(
                "Recorded HTTP metrics",
                context={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration": duration,
                },
            )

        except Exception as e:
            logger.log_warning_with_context(
                "Failed to record metrics",
                context={"error": str(e), "error_type": type(e).__name__},
            )


def add_metrics_middleware(
    app: Any,
    service_name: str = "eshop-api",
    exclude_paths: list[str] | None = None,
    exclude_health_checks: bool = True,
) -> None:
    """
    Add metrics middleware to FastAPI app.

    Args:
        app: FastAPI application
        service_name: Service name for metrics
        exclude_paths: Paths to exclude from metrics
        exclude_health_checks: Whether to exclude health check endpoints
    """
    app.add_middleware(
        MetricsMiddleware,
        service_name=service_name,
        exclude_paths=exclude_paths,
        exclude_health_checks=exclude_health_checks,
    )
    logger.log_with_context(
        "Metrics middleware added",
        "info",
        context={"service_name": service_name},
    )

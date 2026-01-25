"""OpenTelemetry tracing configuration for catalog module."""

import logging
from typing import Any

from opentelemetry import trace
from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class CatalogTracingConfig(BaseSettings):
    """Tracing configuration for catalog module."""

    # Tracing enabled
    enable_tracing: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_TRACING",
        description="Enable OpenTelemetry tracing",
    )

    # Service information
    service_name: str = Field(
        default="catalog-service",
        alias="CATALOG_SERVICE_NAME",
        description="Service name for tracing",
    )

    service_version: str = Field(
        default="1.0.0",
        alias="CATALOG_SERVICE_VERSION",
        description="Service version for tracing",
    )

    # Sampling configuration
    sampling_ratio: float = Field(
        default=1.0,
        alias="CATALOG_SAMPLING_RATIO",
        description="Sampling ratio (0.0 to 1.0)",
    )

    # Export configuration
    enable_jaeger: bool = Field(
        default=False, alias="CATALOG_ENABLE_JAEGER", description="Enable Jaeger export"
    )

    jaeger_endpoint: str = Field(
        default="http://localhost:14268/api/traces",
        alias="CATALOG_JAEGER_ENDPOINT",
        description="Jaeger endpoint",
    )

    enable_zipkin: bool = Field(
        default=False, alias="CATALOG_ENABLE_ZIPKIN", description="Enable Zipkin export"
    )

    zipkin_endpoint: str = Field(
        default="http://localhost:9411/api/v2/spans",
        alias="CATALOG_ZIPKIN_ENDPOINT",
        description="Zipkin endpoint",
    )

    enable_otlp: bool = Field(
        default=False, alias="CATALOG_ENABLE_OTLP", description="Enable OTLP export"
    )

    otlp_endpoint: str = Field(
        default="http://localhost:4317",
        alias="CATALOG_OTLP_ENDPOINT",
        description="OTLP endpoint",
    )

    # Instrumentation
    instrument_requests: bool = Field(
        default=True,
        alias="CATALOG_INSTRUMENT_REQUESTS",
        description="Instrument HTTP requests",
    )

    instrument_database: bool = Field(
        default=True,
        alias="CATALOG_INSTRUMENT_DATABASE",
        description="Instrument database operations",
    )

    instrument_redis: bool = Field(
        default=True,
        alias="CATALOG_INSTRUMENT_REDIS",
        description="Instrument Redis operations",
    )

    instrument_rabbitmq: bool = Field(
        default=True,
        alias="CATALOG_INSTRUMENT_RABBITMQ",
        description="Instrument RabbitMQ operations",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class CatalogTracer:
    """Catalog module tracer with OpenTelemetry."""

    def __init__(self, config: CatalogTracingConfig):
        """
        Initialize the catalog tracer.

        Args:
            config: Tracing configuration
        """
        self.config = config
        self.tracer = None
        self._setup_tracing()

    def _setup_tracing(self) -> None:
        """Set up OpenTelemetry tracing."""
        if not self.config.enable_tracing:
            logger.info("Tracing is disabled")
            return

        try:
            from opentelemetry import trace
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            # Set up resource
            resource = Resource.create(
                {
                    "service.name": self.config.service_name,
                    "service.version": self.config.service_version,
                }
            )

            # Set up tracer provider
            trace.set_tracer_provider(TracerProvider(resource=resource))
            self.tracer = trace.get_tracer(self.config.service_name)

            # Set up exporters
            self._setup_exporters()

            logger.info("OpenTelemetry tracing configured successfully")

        except ImportError:
            logger.warning("OpenTelemetry not available, tracing disabled")
        except Exception as e:
            logger.error(f"Error setting up tracing: {e}")

    def _setup_exporters(self) -> None:
        """Set up trace exporters."""
        try:

            # Jaeger exporter
            if self.config.enable_jaeger:
                self._setup_jaeger_exporter()

            # Zipkin exporter
            if self.config.enable_zipkin:
                self._setup_zipkin_exporter()

            # OTLP exporter
            if self.config.enable_otlp:
                self._setup_otlp_exporter()

        except Exception as e:
            logger.error(f"Error setting up exporters: {e}")

    def _setup_jaeger_exporter(self) -> None:
        """Set up Jaeger exporter."""
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.jaeger.thrift import JaegerExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )

            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

            logger.info("Jaeger exporter configured")

        except Exception as e:
            logger.error(f"Error setting up Jaeger exporter: {e}")

    def _setup_zipkin_exporter(self) -> None:
        """Set up Zipkin exporter."""
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.zipkin.json import ZipkinExporter
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            zipkin_exporter = ZipkinExporter(
                endpoint=self.config.zipkin_endpoint,
            )

            span_processor = BatchSpanProcessor(zipkin_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

            logger.info("Zipkin exporter configured")

        except Exception as e:
            logger.error(f"Error setting up Zipkin exporter: {e}")

    def _setup_otlp_exporter(self) -> None:
        """Set up OTLP exporter."""
        try:
            from opentelemetry import trace
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )
            from opentelemetry.sdk.trace.export import BatchSpanProcessor

            otlp_exporter = OTLPSpanExporter(
                endpoint=self.config.otlp_endpoint,
            )

            span_processor = BatchSpanProcessor(otlp_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)

            logger.info("OTLP exporter configured")

        except Exception as e:
            logger.error(f"Error setting up OTLP exporter: {e}")

    def get_tracer(self):
        """Get the tracer instance."""
        return self.tracer

    def create_span(self, name: str, **kwargs: Any) -> Any:
        """
        Create a new span.

        Args:
            name: Span name
            **kwargs: Additional span attributes

        Returns:
            Span context manager
        """
        if not self.tracer:
            # Return a no-op context manager if tracing is disabled
            from contextlib import nullcontext

            return nullcontext()

        return self.tracer.start_span(name, **kwargs)

    def add_span_attributes(self, span: Any, attributes: dict[str, Any]) -> None:
        """
        Add attributes to a span.

        Args:
            span: Span instance
            attributes: Attributes to add
        """
        if span:
            for key, value in attributes.items():
                span.set_attribute(key, value)

    def record_exception(self, span: Any, exception: Exception) -> None:
        """
        Record an exception in a span.

        Args:
            span: Span instance
            exception: Exception to record
        """
        if span:
            span.record_exception(exception)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


# Global configuration and tracer instances
catalog_tracing_config = CatalogTracingConfig()
catalog_tracer = CatalogTracer(catalog_tracing_config)

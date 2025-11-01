"""Prometheus/OpenTelemetry metrics configuration for catalog module."""

import logging

from pydantic import Field
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class CatalogMetricsConfig(BaseSettings):
    """Metrics configuration for catalog module."""

    # Metrics enabled
    enable_metrics: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_METRICS",
        description="Enable metrics collection",
    )

    # Service information
    service_name: str = Field(
        default="catalog-service",
        alias="CATALOG_SERVICE_NAME",
        description="Service name for metrics",
    )

    service_version: str = Field(
        default="1.0.0",
        alias="CATALOG_SERVICE_VERSION",
        description="Service version for metrics",
    )

    # Prometheus configuration
    enable_prometheus: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_PROMETHEUS",
        description="Enable Prometheus metrics",
    )

    prometheus_port: int = Field(
        default=8001,
        alias="CATALOG_PROMETHEUS_PORT",
        description="Prometheus metrics port",
    )

    prometheus_path: str = Field(
        default="/metrics",
        alias="CATALOG_PROMETHEUS_PATH",
        description="Prometheus metrics path",
    )

    # Custom metrics
    enable_custom_metrics: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_CUSTOM_METRICS",
        description="Enable custom business metrics",
    )

    # Database metrics
    enable_database_metrics: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_DATABASE_METRICS",
        description="Enable database operation metrics",
    )

    # Cache metrics
    enable_cache_metrics: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_CACHE_METRICS",
        description="Enable cache operation metrics",
    )

    # Message queue metrics
    enable_messaging_metrics: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_MESSAGING_METRICS",
        description="Enable messaging operation metrics",
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class CatalogMetrics:
    """Catalog module metrics with Prometheus."""

    def __init__(self, config: CatalogMetricsConfig):
        """
        Initialize the catalog metrics.

        Args:
            config: Metrics configuration
        """
        self.config = config
        self.metrics = {}
        self._setup_metrics()

    def _setup_metrics(self) -> None:
        """Set up Prometheus metrics."""
        if not self.config.enable_metrics:
            logger.info("Metrics are disabled")
            return

        try:
            from prometheus_client import (  # noqa: F401
                CollectorRegistry,
                Counter,
                Gauge,
                Histogram,
                Info,
                generate_latest,
            )

            # Create custom registry
            self.registry = CollectorRegistry()

            # Service info
            self.service_info = Info(
                "catalog_service_info",
                "Catalog service information",
                registry=self.registry,
            )
            self.service_info.info(
                {
                    "service_name": self.config.service_name,
                    "service_version": self.config.service_version,
                }
            )

            # HTTP metrics
            if self.config.enable_custom_metrics:
                self._setup_http_metrics()
                self._setup_business_metrics()

            # Database metrics
            if self.config.enable_database_metrics:
                self._setup_database_metrics()

            # Cache metrics
            if self.config.enable_cache_metrics:
                self._setup_cache_metrics()

            # Messaging metrics
            if self.config.enable_messaging_metrics:
                self._setup_messaging_metrics()

            logger.info("Prometheus metrics configured successfully")

        except ImportError:
            logger.warning("Prometheus client not available, metrics disabled")
        except Exception as e:
            logger.error(f"Error setting up metrics: {e}")

    def _setup_http_metrics(self) -> None:
        """Set up HTTP metrics."""
        from prometheus_client import Counter, Histogram

        self.http_requests_total = Counter(
            "catalog_http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.http_request_duration = Histogram(
            "catalog_http_request_duration_seconds",
            "HTTP request duration",
            ["method", "endpoint"],
            registry=self.registry,
        )

    def _setup_business_metrics(self) -> None:
        """Set up business metrics."""
        from prometheus_client import Counter, Gauge, Histogram  # noqa: F401

        # Product metrics
        self.products_created_total = Counter(
            "catalog_products_created_total",
            "Total products created",
            ["category"],
            registry=self.registry,
        )

        self.products_updated_total = Counter(
            "catalog_products_updated_total",
            "Total products updated",
            ["category"],
            registry=self.registry,
        )

        self.products_deleted_total = Counter(
            "catalog_products_deleted_total",
            "Total products deleted",
            ["category"],
            registry=self.registry,
        )

        # Product price metrics
        self.product_price_changes_total = Counter(
            "catalog_product_price_changes_total",
            "Total product price changes",
            ["category"],
            registry=self.registry,
        )

        self.product_price_change_amount = Histogram(
            "catalog_product_price_change_amount",
            "Product price change amount",
            ["category"],
            registry=self.registry,
        )

        # Inventory metrics
        self.inventory_adjustments_total = Counter(
            "catalog_inventory_adjustments_total",
            "Total inventory adjustments",
            ["adjustment_type"],
            registry=self.registry,
        )

        self.inventory_low_stock_events_total = Counter(
            "catalog_inventory_low_stock_events_total",
            "Total low stock events",
            ["product_category"],
            registry=self.registry,
        )

        self.inventory_out_of_stock_events_total = Counter(
            "catalog_inventory_out_of_stock_events_total",
            "Total out of stock events",
            ["product_category"],
            registry=self.registry,
        )

        # Current inventory levels
        self.inventory_levels = Gauge(
            "catalog_inventory_levels",
            "Current inventory levels",
            ["product_id", "product_sku", "category"],
            registry=self.registry,
        )

    def _setup_database_metrics(self) -> None:
        """Set up database metrics."""
        from prometheus_client import Counter, Histogram

        self.database_queries_total = Counter(
            "catalog_database_queries_total",
            "Total database queries",
            ["operation", "table"],
            registry=self.registry,
        )

        self.database_query_duration = Histogram(
            "catalog_database_query_duration_seconds",
            "Database query duration",
            ["operation", "table"],
            registry=self.registry,
        )

        self.database_errors_total = Counter(
            "catalog_database_errors_total",
            "Total database errors",
            ["operation", "table", "error_type"],
            registry=self.registry,
        )

    def _setup_cache_metrics(self) -> None:
        """Set up cache metrics."""
        from prometheus_client import Counter, Histogram

        self.cache_operations_total = Counter(
            "catalog_cache_operations_total",
            "Total cache operations",
            ["operation", "cache_type"],
            registry=self.registry,
        )

        self.cache_operation_duration = Histogram(
            "catalog_cache_operation_duration_seconds",
            "Cache operation duration",
            ["operation", "cache_type"],
            registry=self.registry,
        )

        self.cache_hits_total = Counter(
            "catalog_cache_hits_total",
            "Total cache hits",
            ["cache_type"],
            registry=self.registry,
        )

        self.cache_misses_total = Counter(
            "catalog_cache_misses_total",
            "Total cache misses",
            ["cache_type"],
            registry=self.registry,
        )

    def _setup_messaging_metrics(self) -> None:
        """Set up messaging metrics."""
        from prometheus_client import Counter, Histogram

        self.messages_published_total = Counter(
            "catalog_messages_published_total",
            "Total messages published",
            ["message_type", "topic"],
            registry=self.registry,
        )

        self.messages_consumed_total = Counter(
            "catalog_messages_consumed_total",
            "Total messages consumed",
            ["message_type", "topic"],
            registry=self.registry,
        )

        self.message_processing_duration = Histogram(
            "catalog_message_processing_duration_seconds",
            "Message processing duration",
            ["message_type", "topic"],
            registry=self.registry,
        )

        self.message_processing_errors_total = Counter(
            "catalog_message_processing_errors_total",
            "Total message processing errors",
            ["message_type", "topic", "error_type"],
            registry=self.registry,
        )

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ) -> None:
        """
        Record HTTP request metrics.

        Args:
            method: HTTP method
            endpoint: Endpoint path
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        if hasattr(self, "http_requests_total"):
            self.http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()

        if hasattr(self, "http_request_duration"):
            self.http_request_duration.labels(method=method, endpoint=endpoint).observe(
                duration
            )

    def record_product_created(self, category: str) -> None:
        """
        Record product creation.

        Args:
            category: Product category
        """
        if hasattr(self, "products_created_total"):
            self.products_created_total.labels(category=category).inc()

    def record_product_updated(self, category: str) -> None:
        """
        Record product update.

        Args:
            category: Product category
        """
        if hasattr(self, "products_updated_total"):
            self.products_updated_total.labels(category=category).inc()

    def record_product_deleted(self, category: str) -> None:
        """
        Record product deletion.

        Args:
            category: Product category
        """
        if hasattr(self, "products_deleted_total"):
            self.products_deleted_total.labels(category=category).inc()

    def record_price_change(self, category: str, change_amount: float) -> None:
        """
        Record product price change.

        Args:
            category: Product category
            change_amount: Price change amount
        """
        if hasattr(self, "product_price_changes_total"):
            self.product_price_changes_total.labels(category=category).inc()

        if hasattr(self, "product_price_change_amount"):
            self.product_price_change_amount.labels(category=category).observe(
                change_amount
            )

    def record_inventory_adjustment(self, adjustment_type: str) -> None:
        """
        Record inventory adjustment.

        Args:
            adjustment_type: Type of adjustment (increase, decrease)
        """
        if hasattr(self, "inventory_adjustments_total"):
            self.inventory_adjustments_total.labels(
                adjustment_type=adjustment_type
            ).inc()

    def record_low_stock_event(self, product_category: str) -> None:
        """
        Record low stock event.

        Args:
            product_category: Product category
        """
        if hasattr(self, "inventory_low_stock_events_total"):
            self.inventory_low_stock_events_total.labels(
                product_category=product_category
            ).inc()

    def record_out_of_stock_event(self, product_category: str) -> None:
        """
        Record out of stock event.

        Args:
            product_category: Product category
        """
        if hasattr(self, "inventory_out_of_stock_events_total"):
            self.inventory_out_of_stock_events_total.labels(
                product_category=product_category
            ).inc()

    def update_inventory_level(
        self, product_id: str, product_sku: str, category: str, level: int
    ) -> None:
        """
        Update inventory level gauge.

        Args:
            product_id: Product ID
            product_sku: Product SKU
            category: Product category
            level: Current inventory level
        """
        if hasattr(self, "inventory_levels"):
            self.inventory_levels.labels(
                product_id=product_id, product_sku=product_sku, category=category
            ).set(level)

    def get_metrics(self) -> str:
        """
        Get metrics in Prometheus format.

        Returns:
            Metrics in Prometheus format
        """
        try:
            from prometheus_client import generate_latest

            return generate_latest(self.registry).decode("utf-8")
        except Exception as e:
            logger.error(f"Error generating metrics: {e}")
            return ""


# Global configuration and metrics instances
catalog_metrics_config = CatalogMetricsConfig()
catalog_metrics = CatalogMetrics(catalog_metrics_config)

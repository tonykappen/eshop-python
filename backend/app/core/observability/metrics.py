"""Global OTEL/Prometheus metric registry."""

from typing import Any

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class MetricsRegistry:
    """OTEL/Prometheus metric registry."""

    _meter_provider: Any = None
    _meter: Any = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, meter_provider: Any = None) -> None:
        """
        Initialize the meter provider.

        Args:
            meter_provider: Optional meter provider instance
        """
        if meter_provider:
            cls._meter_provider = meter_provider
            cls._initialized = True
            logger.log_with_context(
                "[OK] Metrics provider initialized",
                "info",
            )
        else:
            cls._meter_provider = None
            cls._initialized = False
            logger.log_with_context(
                "[NOOP] Metrics initialized as no-op — no provider configured",
                "info",
            )

    @classmethod
    def is_active(cls) -> bool:
        """True when a real meter provider was configured via initialize()."""
        return cls._initialized

    @classmethod
    def get_meter(cls, name: str) -> Any:
        """
        Get a meter instance.

        Args:
            name: Meter name

        Returns:
            Meter instance
        """
        if cls._meter_provider:
            return cls._meter_provider.get_meter(name)
        logger.log_warning_with_context("Meter provider not initialized, returning None")
        return None

    @classmethod
    def shutdown(cls) -> None:
        """Shutdown the meter provider."""
        if cls._meter_provider:
            # Shutdown logic would go here
            logger.log_with_context("Meter provider shut down")
        cls._meter_provider = None
        cls._meter = None
        cls._initialized = False

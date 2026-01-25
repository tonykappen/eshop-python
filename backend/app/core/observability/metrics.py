"""Global OTEL/Prometheus metric registry."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MetricsRegistry:
    """OTEL/Prometheus metric registry."""

    _meter_provider: Any = None
    _meter: Any = None

    @classmethod
    def initialize(cls, meter_provider: Any = None) -> None:
        """
        Initialize the meter provider.

        Args:
            meter_provider: Optional meter provider instance
        """
        if meter_provider:
            cls._meter_provider = meter_provider
            logger.info("Meter provider initialized")
        else:
            logger.warning("No meter provider provided, using default")

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
        logger.warning("Meter provider not initialized, returning None")
        return None

    @classmethod
    def shutdown(cls) -> None:
        """Shutdown the meter provider."""
        if cls._meter_provider:
            # Shutdown logic would go here
            logger.info("Meter provider shut down")

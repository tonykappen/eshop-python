"""Global OTEL TracerProvider setup."""

from typing import Any

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class TracingProvider:
    """OTEL TracerProvider setup and management."""

    _tracer_provider: Any = None
    _tracer: Any = None
    _initialized: bool = False

    @classmethod
    def initialize(cls, tracer_provider: Any = None) -> None:
        """
        Initialize the tracer provider.

        Args:
            tracer_provider: Optional tracer provider instance
        """
        if tracer_provider:
            cls._tracer_provider = tracer_provider
            cls._initialized = True
            logger.log_with_context(
                "[OK] Tracing provider initialized",
                "info",
            )
        else:
            cls._tracer_provider = None
            cls._initialized = False
            logger.log_with_context(
                "[NOOP] Tracing initialized as no-op — no provider configured",
                "info",
            )

    @classmethod
    def is_active(cls) -> bool:
        """True when a real tracer provider was configured via initialize()."""
        return cls._initialized

    @classmethod
    def get_tracer(cls, name: str) -> Any:
        """
        Get a tracer instance.

        Args:
            name: Tracer name

        Returns:
            Tracer instance
        """
        if cls._tracer_provider:
            return cls._tracer_provider.get_tracer(name)
        logger.log_warning_with_context(
            "Tracer provider not initialized, returning None"
        )
        return None

    @classmethod
    def shutdown(cls) -> None:
        """Shutdown the tracer provider."""
        if cls._tracer_provider:
            # Shutdown logic would go here
            logger.log_with_context("Tracer provider shut down")
        cls._tracer_provider = None
        cls._tracer = None
        cls._initialized = False

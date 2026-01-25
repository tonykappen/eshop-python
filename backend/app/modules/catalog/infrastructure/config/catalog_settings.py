"""Pydantic BaseSettings for Catalog BC - centralized configuration."""


from pydantic_settings import BaseSettings

from app.modules.catalog.infrastructure.catalog_logging import CatalogLoggingConfig
from app.modules.catalog.infrastructure.observability.catalog_metrics import (
    CatalogMetricsConfig,
)
from app.modules.catalog.infrastructure.observability.catalog_tracing import (
    CatalogTracingConfig,
)

# Import existing config classes to maintain backward compatibility
from app.modules.catalog.infrastructure.persistence.db_context import (
    CatalogDatabaseConfig,
)


class CatalogSettings(BaseSettings):
    """
    Unified catalog module settings.

    This class aggregates all catalog module configuration settings
    for convenient access. Individual config classes are still available
    for component-specific configuration.

    Environment variables should be prefixed with CATALOG_* for catalog-specific
    settings, or use the specific prefixes for each sub-configuration.
    """

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow reading from nested config classes
        extra = "allow"

    def __init__(self, **kwargs):
        """
        Initialize catalog settings.

        Creates instances of all sub-configurations and makes them
        available as properties.
        """
        super().__init__(**kwargs)

        # Initialize sub-configurations
        self._database_config = CatalogDatabaseConfig()
        self._logging_config = CatalogLoggingConfig()
        self._metrics_config = CatalogMetricsConfig()
        self._tracing_config = CatalogTracingConfig()

    @property
    def database(self) -> CatalogDatabaseConfig:
        """Get database configuration."""
        return self._database_config

    @property
    def logging(self) -> CatalogLoggingConfig:
        """Get logging configuration."""
        return self._logging_config

    @property
    def metrics(self) -> CatalogMetricsConfig:
        """Get metrics configuration."""
        return self._metrics_config

    @property
    def tracing(self) -> CatalogTracingConfig:
        """Get tracing configuration."""
        return self._tracing_config


# Global settings instance for convenient access
# Usage: from app.modules.catalog.infrastructure.config import catalog_settings
catalog_settings = CatalogSettings()


# Re-export individual config classes for backward compatibility
# This allows existing code to continue working:
# from app.modules.catalog.infrastructure.config import CatalogDatabaseConfig
__all__ = [
    "CatalogSettings",
    "CatalogDatabaseConfig",
    "CatalogLoggingConfig",
    "CatalogMetricsConfig",
    "CatalogTracingConfig",
    "catalog_settings",
]

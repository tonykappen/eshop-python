"""Pydantic BaseSettings for Catalog BC - centralized configuration."""

# Import existing config classes to maintain backward compatibility
from app.modules.catalog.infrastructure.persistence.db_context import \
    CatalogDatabaseConfig
from pydantic_settings import BaseSettings


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

    @property
    def database(self) -> CatalogDatabaseConfig:
        """Get database configuration."""
        return self._database_config


# Global settings instance for convenient access
# Usage: from app.modules.catalog.infrastructure.config import catalog_settings
catalog_settings = CatalogSettings()


# Re-export individual config classes for backward compatibility
# This allows existing code to continue working:
# from app.modules.catalog.infrastructure.config import CatalogDatabaseConfig
__all__ = [
    "CatalogSettings",
    "CatalogDatabaseConfig",
    "catalog_settings",
]

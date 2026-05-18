"""Catalog module configuration package."""

# Re-export all configuration classes for convenient imports
from app.modules.catalog.infrastructure.config.catalog_settings import (
    CatalogDatabaseConfig, CatalogSettings)

__all__ = [
    "CatalogSettings",
    "CatalogDatabaseConfig",
]

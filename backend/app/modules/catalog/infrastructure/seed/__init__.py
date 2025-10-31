"""Catalog module seeding package."""

from app.modules.catalog.infrastructure.seed.catalog_data_seeder import (
    CatalogDataSeeder,
)
from app.modules.catalog.infrastructure.seed.initial_data import CatalogInitialData

__all__ = ["CatalogDataSeeder", "CatalogInitialData"]

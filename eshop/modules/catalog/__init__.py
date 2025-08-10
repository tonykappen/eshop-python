"""Catalog module initialization."""

from eshop.core.database.seeding import register_seeder
from eshop.modules.catalog.infrastructure.seed.catalog_data_seeder import (
    CatalogDataSeeder,
)

# Register the catalog seeder
register_seeder(CatalogDataSeeder)

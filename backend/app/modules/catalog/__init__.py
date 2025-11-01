"""Catalog module initialization."""

# Database seeding will be enabled when SQLAlchemy is available
try:
    from app.core.database.seeding import register_seeder
    from app.modules.catalog.infrastructure.seed.catalog_data_seeder import (
        CatalogDataSeeder,
    )

    # Register the catalog seeder
    register_seeder(CatalogDataSeeder)
except ImportError:
    # Skip seeding if dependencies are not available
    pass

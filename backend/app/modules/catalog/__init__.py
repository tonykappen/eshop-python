"""Catalog module initialization."""

# Database seeding will be enabled when SQLAlchemy is available
try:
    from app.core.database.seeding import register_seeder
    from app.modules.catalog.infrastructure.seeding.products.catalog_data_seeder import (
        CatalogDataSeeder,
    )

    # Register the catalog seeder
    register_seeder(CatalogDataSeeder)
except ImportError:
    # Skip seeding if dependencies are not available
    pass

# Outbox worker registration is done explicitly at application startup via
# register_outbox_workers() in main.py, which calls register_outbox_worker() from
# app.modules.catalog.outbox_registration. Do not rely on import side effects here.

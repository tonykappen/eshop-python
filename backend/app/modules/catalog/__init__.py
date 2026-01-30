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

# Import outbox publisher worker to ensure it registers itself with the global registry
# This ensures the worker is available for lifecycle management
try:
    from app.modules.catalog.workers.outbox_publisher_worker import (  # noqa: F401
        outbox_publisher_worker,
    )
except ImportError:
    # Skip if worker dependencies are not available
    pass

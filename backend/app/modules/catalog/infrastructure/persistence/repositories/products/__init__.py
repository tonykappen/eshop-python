"""Product repositories package."""

# Export SQL implementations
# Export Redis cached implementations
from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import \
    CachedProductRepository
from app.modules.catalog.infrastructure.persistence.repositories.products.sql.sql_category_repository import \
    SqlCategoryRepository
from app.modules.catalog.infrastructure.persistence.repositories.products.sql.sql_inventory_repository import \
    SqlInventoryRepository
from app.modules.catalog.infrastructure.persistence.repositories.products.sql.sql_product_repository import \
    SqlProductRepository

__all__ = [
    "SqlProductRepository",
    "SqlCategoryRepository",
    "SqlInventoryRepository",
    "CachedProductRepository",
]

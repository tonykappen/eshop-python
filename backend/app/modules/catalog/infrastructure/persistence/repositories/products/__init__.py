"""Product repositories package."""

# Export SQL implementations
from app.modules.catalog.infrastructure.persistence.repositories.products.sql.sql_product_repository import (
    SqlProductRepository,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.sql.sql_category_repository import (
    SqlCategoryRepository,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.sql.sql_inventory_repository import (
    SqlInventoryRepository,
)

# Export Redis cached implementations
from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import (
    CachedProductRepository,
)

__all__ = [
    "SqlProductRepository",
    "SqlCategoryRepository",
    "SqlInventoryRepository",
    "CachedProductRepository",
]

"""Redis cached repository implementations."""

from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import (
    CachedProductRepository,
)

__all__ = [
    "CachedProductRepository",
]

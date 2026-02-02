"""Redis + JSON decorator for product repo."""

from uuid import UUID

from app.core.logging.base_logger import BaseLogger
from app.modules.catalog.application.services.catalog_cache_patterns import (
    CatalogCachePatterns,
)
from app.modules.catalog.application.services.catalog_cache_service import (
    CatalogCacheService,
)
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.repositories.product.product_repository import (
    ProductRepository,
)

logger = BaseLogger(__name__)


class CachedProductRepository(ProductRepository):
    """Redis + JSON decorator for product repository with cache-aside pattern."""

    def __init__(
        self,
        repository: ProductRepository,
        cache_service: CatalogCacheService,
        cache_patterns: CatalogCachePatterns | None = None,
        default_ttl: int = 3600,
    ):
        """
        Initialize cached product repository.

        Args:
            repository: Underlying SQL repository implementation
            cache_service: Cache service for Redis operations
            cache_patterns: Cache key patterns (optional, creates default if not provided)
            default_ttl: Default TTL for cache entries in seconds
        """
        self._repository = repository
        self._cache = cache_service
        self._cache_patterns = cache_patterns or CatalogCachePatterns()
        self._default_ttl = default_ttl

    async def get_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID with cache-aside pattern."""
        # Try cache first
        cache_key = self._cache_patterns.product_key(product_id)
        cached_data = await self._cache.get_product(product_id)

        if cached_data:
            try:
                logger.log_with_context(
                    "Cache hit: Product retrieved from cache",
                    context={
                        "product_id": str(product_id),
                        "cache_key": cache_key,
                        "cache_status": "hit",
                        "source": "cache"
                    }
                )
                return self._deserialize_product(cached_data)
            except Exception as e:
                logger.log_warning_with_context(
                    f"Failed to deserialize cached product {product_id}: {e}",
                    context={
                        "product_id": str(product_id),
                        "cache_key": cache_key,
                        "cache_status": "deserialization_error"
                    }
                )

        # Cache miss - get from repository
        logger.log_with_context(
            "Cache miss: Product not found in cache, querying database",
            context={
                "product_id": str(product_id),
                "cache_key": cache_key,
                "cache_status": "miss",
                "source": "database"
            }
        )
        product = await self._repository.get_by_id(product_id)

        if product:
            # Cache the result
            await self._cache.set_product(
                product_id, self._serialize_product(product), self._default_ttl
            )
            logger.log_with_context(
                "Product cached after database retrieval",
                context={
                    "product_id": str(product_id),
                    "cache_key": cache_key,
                    "cache_status": "stored",
                    "ttl": self._default_ttl
                }
            )
        else:
            logger.log_debug_with_context(
                "Product not found in database, nothing to cache",
                context={
                    "product_id": str(product_id),
                    "cache_key": cache_key,
                    "cache_status": "not_found"
                }
            )

        return product

    async def get_by_sku(self, sku: str) -> Product | None:
        """Get product by SKU (not cached, as SKU lookups are less frequent)."""
        return await self._repository.get_by_sku(sku)

    async def get_by_name(self, name: str) -> Product | None:
        """Get product by name (not cached)."""
        return await self._repository.get_by_name(name)

    async def get_by_category(
        self, category: str, page: int = 1, page_size: int = 10
    ) -> list[Product] | tuple[list[Product], int]:
        """Get products by category with caching."""
        # Try cache first
        cache_key = self._cache_patterns.product_list_key(category, page, page_size)
        cached_data = await self._cache.get_products_list(
            page, page_size, {"category": category}
        )

        if cached_data:
            try:
                products = [
                    self._deserialize_product(p)
                    for p in cached_data.get("products", [])
                ]
                total_count = cached_data.get("total_count", len(products))
                logger.log_with_context(
                    "Cache hit: Products by category retrieved from cache",
                    context={
                        "category": category,
                        "page": page,
                        "page_size": page_size,
                        "cache_key": cache_key,
                        "cache_status": "hit",
                        "source": "cache",
                        "product_count": len(products),
                        "total_count": total_count
                    }
                )
                if "total_count" in cached_data:
                    return products, cached_data["total_count"]
                return products
            except Exception as e:
                logger.log_warning_with_context(
                    f"Failed to deserialize cached product list: {e}",
                    context={
                        "category": category,
                        "page": page,
                        "page_size": page_size,
                        "cache_key": cache_key,
                        "cache_status": "deserialization_error"
                    }
                )

        # Cache miss - get from repository
        logger.log_with_context(
            "Cache miss: Products by category not found in cache, querying database",
            context={
                "category": category,
                "page": page,
                "page_size": page_size,
                "cache_key": cache_key,
                "cache_status": "miss",
                "source": "database"
            }
        )
        result = await self._repository.get_by_category(category, page, page_size)

        if isinstance(result, tuple):
            products, total_count = result
            # Cache the result
            await self._cache.set_products_list(
                page,
                page_size,
                {
                    "products": [self._serialize_product(p) for p in products],
                    "total_count": total_count,
                },
                {"category": category},
                self._default_ttl,
            )
            logger.log_with_context(
                "Products by category cached after database retrieval",
                context={
                    "category": category,
                    "page": page,
                    "page_size": page_size,
                    "cache_key": cache_key,
                    "cache_status": "stored",
                    "ttl": self._default_ttl,
                    "product_count": len(products),
                    "total_count": total_count
                }
            )
            return products, total_count
        else:
            # Cache the result
            await self._cache.set_products_list(
                page,
                page_size,
                {"products": [self._serialize_product(p) for p in result]},
                {"category": category},
                self._default_ttl,
            )
            logger.log_with_context(
                "Products by category cached after database retrieval",
                context={
                    "category": category,
                    "page": page,
                    "page_size": page_size,
                    "cache_key": cache_key,
                    "cache_status": "stored",
                    "ttl": self._default_ttl,
                    "product_count": len(result)
                }
            )
            return result

    async def search_by_name(self, search_term: str) -> list[Product]:
        """Search products by name (not cached due to dynamic nature)."""
        return await self._repository.search_by_name(search_term)

    async def get_all(
        self, page: int = 1, page_size: int = 10, skip: int | None = None, limit: int | None = None
    ) -> tuple[list[Product], int]:
        """
        Get all products with pagination (cached).
        
        Matches SqlProductRepository signature: get_all(page, page_size) -> tuple[list[Product], int]
        Also supports interface signature: get_all(skip, limit) by converting to page/page_size.
        """
        # Handle both signatures: (page, page_size) or (skip, limit)
        if skip is not None and limit is not None:
            # Convert skip/limit to page/page_size
            actual_page = (skip // limit) + 1 if limit > 0 else 1
            actual_page_size = limit
        else:
            # Use page/page_size directly
            actual_page = page
            actual_page_size = page_size

        # Try cache first
        cache_key = self._cache_patterns.product_list_key(None, actual_page, actual_page_size)
        cached_data = await self._cache.get_products_list(actual_page, actual_page_size, None)

        if cached_data:
            try:
                products = [
                    self._deserialize_product(p)
                    for p in cached_data.get("products", [])
                ]
                total_count = cached_data.get("total_count", len(products))
                logger.log_with_context(
                    "Cache hit: Products list retrieved from cache",
                    context={
                        "page": actual_page,
                        "page_size": actual_page_size,
                        "cache_key": cache_key,
                        "cache_status": "hit",
                        "source": "cache",
                        "product_count": len(products),
                        "total_count": total_count
                    }
                )
                return products, total_count
            except Exception as e:
                logger.log_warning_with_context(
                    f"Failed to deserialize cached product list: {e}",
                    context={
                        "page": actual_page,
                        "page_size": actual_page_size,
                        "cache_key": cache_key,
                        "cache_status": "deserialization_error"
                    }
                )

        # Cache miss - get from repository
        logger.log_with_context(
            "Cache miss: Products list not found in cache, querying database",
            context={
                "page": actual_page,
                "page_size": actual_page_size,
                "cache_key": cache_key,
                "cache_status": "miss",
                "source": "database"
            }
        )
        # SqlProductRepository.get_all() takes page/page_size and returns tuple[list[Product], int]
        result = await self._repository.get_all(actual_page, actual_page_size)
        
        # Handle tuple return (products, total_count)
        if isinstance(result, tuple):
            products, total_count = result
        else:
            # Fallback if it's just a list
            products = result if isinstance(result, list) else [result]
            total_count = len(products)

        # Cache the result
        await self._cache.set_products_list(
            actual_page,
            actual_page_size,
            {"products": [self._serialize_product(p) for p in products], "total_count": total_count},
            None,
            self._default_ttl,
        )
        logger.log_with_context(
            "Products list cached after database retrieval",
            context={
                "page": actual_page,
                "page_size": actual_page_size,
                "cache_key": cache_key,
                "cache_status": "stored",
                "ttl": self._default_ttl,
                "product_count": len(products),
                "total_count": total_count
            }
        )

        return products, total_count

    async def count(self) -> int:
        """Get total count of products (not cached)."""
        return await self._repository.count()

    async def exists_by_sku(self, sku: str) -> bool:
        """Check if product exists by SKU (not cached)."""
        return await self._repository.exists_by_sku(sku)

    async def exists_by_name(self, name: str) -> bool:
        """Check if product exists by name (not cached)."""
        return await self._repository.exists_by_name(name)

    async def exists(self, product_id: UUID) -> bool:
        """Check if product exists (not cached)."""
        return await self._repository.exists(product_id)

    async def add(self, product: Product) -> Product:
        """Add a new product and invalidate cache."""
        result = await self._repository.add(product)
        # Invalidate product lists cache
        await self._cache.invalidate_products_list()
        return result

    async def update(self, product: Product) -> Product:
        """Update a product and invalidate cache."""
        result = await self._repository.update(product)
        # Invalidate this product and product lists
        await self._cache.invalidate_product(product.id)
        await self._cache.invalidate_products_list()
        return result

    async def delete(
        self,
        product_id: UUID,
        deleted_by: UUID | None = None,
        deletion_reason: str | None = None,
    ) -> bool:
        """Delete a product and invalidate cache."""
        result = await self._repository.delete(product_id, deleted_by, deletion_reason)
        if result:
            # Invalidate this product and product lists
            await self._cache.invalidate_product(product_id)
            await self._cache.invalidate_products_list()
        return result

    async def get_deleted_by_id(self, product_id: UUID) -> Product | None:
        """Get deleted product by ID (not cached)."""
        return await self._repository.get_deleted_by_id(product_id)

    async def search(
        self, search_term: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """Search products (not cached due to dynamic nature)."""
        return await self._repository.search(search_term, page, page_size)

    async def get_deleted_products(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """Get deleted products (not cached)."""
        return await self._repository.get_deleted_products(page, page_size)

    async def restore_product(
        self, product_id: UUID, restored_by: UUID | None = None
    ) -> bool:
        """Restore a deleted product and invalidate cache."""
        result = await self._repository.restore_product(product_id, restored_by)
        if result:
            # Invalidate this product and product lists
            await self._cache.invalidate_product(product_id)
            await self._cache.invalidate_products_list()
        return result

    def _serialize_product(self, product: Product) -> dict:
        """Serialize product to dictionary for caching."""
        return {
            "id": str(product.id),
            "name": product.name,
            "sku": str(product.sku),
            "category": product.category,
            "description": product.description,
            "image_file": product.image_file,
            "price_amount": str(product.price.amount),
            "price_currency": product.price.currency,
            "version": product.version,
            "created_at": (
                product.created_at.isoformat() if product.created_at else None
            ),
            "last_modified": (
                product.last_modified.isoformat() if product.last_modified else None
            ),
        }

    def _deserialize_product(self, data: dict) -> Product:
        """Deserialize product from dictionary."""
        from datetime import datetime
        from decimal import Decimal

        from app.modules.catalog.domain.entities.product.product import Product
        from app.modules.catalog.domain.value_objects import SKU, Money

        return Product(
            id=UUID(data["id"]),
            name=data["name"],
            sku=SKU(value=data["sku"]),
            category=data["category"],
            description=data.get("description"),
            image_file=data.get("image_file"),
            price=Money(
                amount=Decimal(data["price_amount"]),
                currency=data["price_currency"],
            ),
            version=data.get("version", 1),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            last_modified=(
                datetime.fromisoformat(data["last_modified"])
                if data.get("last_modified")
                else None
            ),
        )

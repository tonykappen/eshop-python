"""Redis cache service implementation for catalog module."""

import json
from typing import Any
from uuid import UUID

import redis.asyncio as redis

from app.config.settings import settings
from app.core.cache.patterns import ICacheService
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class RedisCacheService(ICacheService):
    """Redis implementation of cache service."""

    def __init__(self, redis_client: redis.Redis | None = None):
        """Initialize Redis cache service."""
        self.redis_client = redis_client or self._create_redis_client()
        self.default_ttl = 3600  # 1 hour default TTL

    def _create_redis_client(self) -> redis.Redis:
        """Create Redis client with configuration."""
        return redis.Redis.from_url(
            settings.redis_connection_string,
            decode_responses=True,
            encoding="utf-8",
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None

            # Try to deserialize JSON, fallback to string
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.log_error_with_context(f"Failed to get cache key {key}", error=e)
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        try:
            # Serialize value to JSON if it's not a string
            if not isinstance(value, str):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = value

            ttl = ttl or self.default_ttl
            await self.redis_client.setex(key, ttl, serialized_value)
            logger.debug(f"Cached key {key} with TTL {ttl}")
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Deleted cache key {key}")
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            result = await self.redis_client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str, batch_cap: int = 500) -> None:
        """Invalidate all keys matching pattern using SCAN (never KEYS).

        Args:
            pattern: Redis glob pattern to match.
            batch_cap: Maximum keys to delete per SCAN cycle to limit latency.
        """
        try:
            deleted = 0
            cursor: int | bytes = 0
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor, match=pattern, count=100
                )
                if keys:
                    batch = keys[:batch_cap - deleted] if (deleted + len(keys)) > batch_cap else keys
                    if batch:
                        pipe = self.redis_client.pipeline()
                        for key in batch:
                            pipe.delete(key)
                        await pipe.execute()
                        deleted += len(batch)
                if cursor == 0 or deleted >= batch_cap:
                    break
            if deleted:
                logger.debug(f"Invalidated {deleted} keys matching pattern {pattern}")
        except Exception as e:
            logger.error(f"Failed to invalidate pattern {pattern}: {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        try:
            await self.redis_client.close()
            logger.debug("Redis connection closed")
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {e}")


class CatalogCacheService:
    """Catalog-specific cache service with domain-specific methods."""

    def __init__(self, cache_service: RedisCacheService):
        """Initialize catalog cache service."""
        self.cache = cache_service
        self.cache_patterns = CatalogCachePatterns()

    async def get_product(self, product_id: UUID) -> dict | None:
        """Get product from cache."""
        key = self.cache_patterns.product_key(product_id)
        return await self.cache.get(key)

    async def set_product(
        self, product_id: UUID, product_data: dict, ttl: int | None = None
    ) -> None:
        """Cache product data."""
        key = self.cache_patterns.product_key(product_id)
        await self.cache.set(key, product_data, ttl)

    async def get_products_list(
        self, page: int, size: int, filters: dict | None = None
    ) -> dict | None:
        """Get products list from cache."""
        key = self.cache_patterns.products_list_key(page, size, filters)
        return await self.cache.get(key)

    async def set_products_list(
        self,
        page: int,
        size: int,
        products_data: dict,
        filters: dict | None = None,
        ttl: int | None = None,
    ) -> None:
        """Cache products list."""
        key = self.cache_patterns.products_list_key(page, size, filters)
        await self.cache.set(key, products_data, ttl)

    async def invalidate_product(self, product_id: UUID) -> None:
        """Invalidate all cache entries for a product."""
        patterns = [
            self.cache_patterns.product_key(product_id),
            "catalog:products:list:*",  # All product lists (since any list might contain this product)
        ]
        for pattern in patterns:
            await self.cache.invalidate_pattern(pattern)

    async def invalidate_products_list(self) -> None:
        """Invalidate all products list cache."""
        await self.cache.invalidate_pattern("catalog:products:list:*")

    async def invalidate_all_catalog(self) -> None:
        """Invalidate all catalog cache."""
        await self.cache.invalidate_pattern("catalog:*")


class CatalogCachePatterns:
    """Cache key patterns for catalog module."""

    @staticmethod
    def product_key(product_id: UUID) -> str:
        """Build cache key for a product."""
        return f"catalog:product:{product_id}"

    @staticmethod
    def products_list_key(page: int, size: int, filters: dict | None = None) -> str:
        """Build cache key for products list."""
        key = f"catalog:products:list:page:{page}:size:{size}"
        if filters:
            # Sort filters for consistent key generation
            sorted_filters = sorted(filters.items())
            filter_str = ":".join(f"{k}={v}" for k, v in sorted_filters)
            key = f"{key}:filters:{filter_str}"
        return key

    @staticmethod
    def category_key(category_id: UUID) -> str:
        """Build cache key for a category."""
        return f"catalog:category:{category_id}"

    @staticmethod
    def categories_list_key() -> str:
        """Build cache key for categories list."""
        return "catalog:categories:list"

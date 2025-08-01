"""Cache patterns: Cache Aside and Cache Invalidation."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar
from uuid import UUID

T = TypeVar("T")


class ICacheService(ABC):
    """Base interface for cache services."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def invalidate_pattern(self, pattern: str) -> None:
        """Invalidate all keys matching pattern."""
        pass


class CacheAsidePattern:
    """Cache Aside pattern implementation."""

    def __init__(self, cache_service: ICacheService):
        self.cache = cache_service

    async def get_or_set(self, key: str, fetch_func, ttl: int | None = None) -> Any:
        """Get from cache or fetch and set if not exists."""
        # Try to get from cache first
        cached_value = await self.cache.get(key)
        if cached_value is not None:
            return cached_value

        # If not in cache, fetch from source
        value = await fetch_func()

        # Store in cache for next time
        if value is not None:
            await self.cache.set(key, value, ttl)

        return value

    async def invalidate_and_refetch(
        self, key: str, fetch_func, ttl: int | None = None
    ) -> Any:
        """Invalidate cache and refetch data."""
        await self.cache.delete(key)
        return await self.get_or_set(key, fetch_func, ttl)


class CacheInvalidationPattern:
    """Cache Invalidation pattern implementation."""

    def __init__(self, cache_service: ICacheService):
        self.cache = cache_service

    async def invalidate_entity(self, entity_type: str, entity_id: UUID) -> None:
        """Invalidate cache for a specific entity."""
        pattern = f"{entity_type}:{entity_id}:*"
        await self.cache.invalidate_pattern(pattern)

    async def invalidate_collection(self, entity_type: str) -> None:
        """Invalidate cache for all entities of a type."""
        pattern = f"{entity_type}:*"
        await self.cache.invalidate_pattern(pattern)

    async def invalidate_user_data(self, user_id: UUID) -> None:
        """Invalidate all cache data for a specific user."""
        pattern = f"user:{user_id}:*"
        await self.cache.invalidate_pattern(pattern)

    async def invalidate_related_data(
        self, entity_type: str, entity_id: UUID, related_types: list[str]
    ) -> None:
        """Invalidate cache for entity and related entities."""
        # Invalidate the main entity
        await self.invalidate_entity(entity_type, entity_id)

        # Invalidate related entities
        for related_type in related_types:
            pattern = f"{related_type}:*:{entity_id}:*"
            await self.cache.invalidate_pattern(pattern)


class CacheKeyBuilder:
    """Helper for building consistent cache keys."""

    @staticmethod
    def entity_key(entity_type: str, entity_id: UUID, suffix: str = "") -> str:
        """Build cache key for an entity."""
        key = f"{entity_type}:{entity_id}"
        if suffix:
            key = f"{key}:{suffix}"
        return key

    @staticmethod
    def collection_key(entity_type: str, filters: dict = None) -> str:
        """Build cache key for a collection."""
        key = f"{entity_type}:collection"
        if filters:
            # Sort filters for consistent key generation
            sorted_filters = sorted(filters.items())
            filter_str = ":".join(f"{k}={v}" for k, v in sorted_filters)
            key = f"{key}:{filter_str}"
        return key

    @staticmethod
    def user_key(user_id: UUID, resource: str) -> str:
        """Build cache key for user-specific data."""
        return f"user:{user_id}:{resource}"

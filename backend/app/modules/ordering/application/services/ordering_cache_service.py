"""Ordering cache service for higher-level caching operations."""

from uuid import UUID

from app.core.cache.patterns import ICacheService
from app.modules.ordering.application.dtos.order_dto import OrderDto
from app.modules.ordering.application.services.ordering_cache_patterns import \
    OrderingCachePatterns


class OrderingCacheService:
    """Higher-level ordering caching service built on core cache."""

    def __init__(self, cache_service: ICacheService) -> None:
        """
        Initialize cache service.

        Args:
            cache_service: Core cache service implementation
        """
        self._cache_service = cache_service
        self._patterns = OrderingCachePatterns()

    async def get_order(self, order_id: UUID) -> OrderDto | None:
        """
        Get order from cache.

        Args:
            order_id: Order ID

        Returns:
            OrderDto if found in cache, None otherwise
        """
        key = self._patterns.order_key(order_id)
        raw = await self._cache_service.get(key)
        if raw is None:
            return None
        if isinstance(raw, OrderDto):
            return raw
        return OrderDto.model_validate(raw)

    async def set_order(self, order: OrderDto, ttl: int = 3600) -> None:
        """
        Cache an order.

        Args:
            order: Order DTO to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        key = self._patterns.order_key(order.id)
        await self._cache_service.set(key, order, ttl)

    async def invalidate_order(self, order_id: UUID) -> None:
        """
        Invalidate cached order.

        Args:
            order_id: Order ID
        """
        key = self._patterns.order_key(order_id)
        await self._cache_service.delete(key)

    async def invalidate_orders_list(self) -> None:
        """Invalidate all orders list cache entries."""
        # In a real implementation, you might want to track all list keys
        # For now, we'll use a pattern-based invalidation
        pass

"""Basket cache service - higher-level caching service for basket operations."""

from app.core.cache.patterns import ICacheService
from app.modules.basket.application.dtos.shopping_cart_dto import \
    ShoppingCartDto
from app.modules.basket.application.services.basket_cache_patterns import \
    BasketCachePatterns


class BasketCacheService:
    """Higher-level basket caching service built on core cache."""

    def __init__(self, cache_service: ICacheService):
        """
        Initialize basket cache service.

        Args:
            cache_service: Core cache service implementation
        """
        self._cache = cache_service
        self._patterns = BasketCachePatterns()
        self._default_ttl = 3600  # 1 hour

    async def get_basket(self, user_name: str) -> ShoppingCartDto | None:
        """
        Get basket from cache.

        Args:
            user_name: User name

        Returns:
            ShoppingCartDto if found in cache, None otherwise
        """
        cache_key = self._patterns.basket_key(user_name)
        cached_data = await self._cache.get(cache_key)

        if cached_data:
            try:
                return ShoppingCartDto(**cached_data)
            except Exception:
                return None

        return None

    async def set_basket(self, basket: ShoppingCartDto, ttl: int | None = None) -> None:
        """
        Set basket in cache.

        Args:
            basket: ShoppingCartDto to cache
            ttl: Optional TTL in seconds (default: 1 hour)
        """
        cache_key = self._patterns.basket_key(basket.user_name)
        basket_dict = basket.model_dump()
        await self._cache.set(cache_key, basket_dict, ttl or self._default_ttl)

    async def invalidate_basket(self, user_name: str) -> None:
        """
        Invalidate basket cache for a user.

        Args:
            user_name: User name
        """
        cache_key = self._patterns.basket_key(user_name)
        await self._cache.delete(cache_key)

    async def invalidate_all_baskets(self) -> None:
        """Invalidate all basket caches."""
        pattern = self._patterns.invalidate_basket_pattern()
        await self._cache.invalidate_pattern(pattern)

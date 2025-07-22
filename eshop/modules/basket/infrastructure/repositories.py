"""Basket repository interfaces and implementations."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from ..domain.shopping_cart import ShoppingCart


class IBasketRepository(ABC):
    """Interface for basket repository."""
    
    @abstractmethod
    async def get_by_id(self, basket_id: UUID) -> Optional[ShoppingCart]:
        """Get basket by ID."""
        pass
    
    @abstractmethod
    async def save(self, basket: ShoppingCart) -> None:
        """Save basket."""
        pass
    
    @abstractmethod
    async def delete(self, basket_id: UUID) -> None:
        """Delete basket."""
        pass


class BasketRepository(IBasketRepository):
    """In-memory basket repository implementation."""
    
    def __init__(self):
        self._baskets: dict[UUID, ShoppingCart] = {}
    
    async def get_by_id(self, basket_id: UUID) -> Optional[ShoppingCart]:
        """Get basket by ID."""
        return self._baskets.get(basket_id)
    
    async def save(self, basket: ShoppingCart) -> None:
        """Save basket."""
        self._baskets[basket.id] = basket
    
    async def delete(self, basket_id: UUID) -> None:
        """Delete basket."""
        if basket_id in self._baskets:
            del self._baskets[basket_id]


class CachedBasketRepository(IBasketRepository):
    """Cached basket repository implementation."""
    
    def __init__(self, basket_repository: IBasketRepository, cache_service):
        self.basket_repository = basket_repository
        self.cache_service = cache_service
    
    async def get_by_id(self, basket_id: UUID) -> Optional[ShoppingCart]:
        """Get basket by ID with caching."""
        cache_key = f"basket:{basket_id}"
        
        # Try to get from cache first
        cached_basket = await self.cache_service.get(cache_key)
        if cached_basket:
            return cached_basket
        
        # Get from repository
        basket = await self.basket_repository.get_by_id(basket_id)
        if basket:
            # Cache the result
            await self.cache_service.set(cache_key, basket, ttl=3600)  # 1 hour
        
        return basket
    
    async def save(self, basket: ShoppingCart) -> None:
        """Save basket and invalidate cache."""
        await self.basket_repository.save(basket)
        
        # Invalidate cache
        cache_key = f"basket:{basket.id}"
        await self.cache_service.delete(cache_key)
    
    async def delete(self, basket_id: UUID) -> None:
        """Delete basket and invalidate cache."""
        await self.basket_repository.delete(basket_id)
        
        # Invalidate cache
        cache_key = f"basket:{basket_id}"
        await self.cache_service.delete(cache_key) 
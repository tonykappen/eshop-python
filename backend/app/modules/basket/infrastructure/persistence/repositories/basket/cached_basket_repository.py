"""Redis + JSON decorator for basket repository."""

import json
import logging
from uuid import UUID

from app.modules.basket.application.dtos.shopping_cart_dto import ShoppingCartDto
from app.modules.basket.application.services.basket_cache_patterns import (
    BasketCachePatterns,
)
from app.modules.basket.application.services.basket_cache_service import (
    BasketCacheService,
)
from app.modules.basket.domain.entities.basket import ShoppingCart
from app.modules.basket.domain.repositories.basket import IBasketRepository

logger = logging.getLogger(__name__)


class CachedBasketRepository(IBasketRepository):
    """Redis + JSON decorator for basket repository with cache-aside pattern."""

    def __init__(
        self,
        repository: IBasketRepository,
        cache_service: BasketCacheService,
        cache_patterns: BasketCachePatterns | None = None,
        default_ttl: int = 3600,
    ):
        """
        Initialize cached basket repository.

        Args:
            repository: Underlying SQL repository implementation
            cache_service: Basket cache service for Redis operations
            cache_patterns: Cache key patterns (optional, creates default if not provided)
            default_ttl: Default TTL for cache entries in seconds
        """
        self._repository = repository
        self._cache = cache_service
        self._cache_patterns = cache_patterns or BasketCachePatterns()
        self._default_ttl = default_ttl

    async def get_basket(
        self, user_name: str, as_no_tracking: bool = True
    ) -> ShoppingCart:
        """Get basket by user name with cache-aside pattern."""
        # Try cache first
        cached_basket = await self._cache.get_basket(user_name)

        if cached_basket:
            try:
                # Convert DTO to domain model
                return self._dto_to_domain(cached_basket)
            except Exception as e:
                logger.warning(
                    f"Failed to deserialize cached basket for {user_name}: {e}"
                )

        # Cache miss - get from repository
        basket = await self._repository.get_basket(user_name, as_no_tracking)

        if basket:
            # Cache the result
            basket_dto = self._domain_to_dto(basket)
            await self._cache.set_basket(basket_dto, self._default_ttl)

        return basket

    async def create_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """Create a new basket and invalidate cache."""
        result = await self._repository.create_basket(basket)
        # Invalidate cache for this user
        await self._cache.invalidate_basket(basket.user_name)
        return result

    async def delete_basket(self, user_name: str) -> bool:
        """Delete basket and invalidate cache."""
        result = await self._repository.delete_basket(user_name)
        if result:
            # Invalidate cache
            await self._cache.invalidate_basket(user_name)
        return result

    async def add_items_to_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """Add items to basket and invalidate cache."""
        result = await self._repository.add_items_to_basket(basket)
        # Invalidate cache after update
        await self._cache.invalidate_basket(basket.user_name)
        return result

    async def update_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """Update basket and invalidate cache."""
        result = await self._repository.update_basket(basket)
        # Invalidate cache after update
        await self._cache.invalidate_basket(basket.user_name)
        return result

    async def save_changes_async(self, user_name: str | None = None) -> int:
        """Save changes and invalidate cache if user_name provided."""
        result = await self._repository.save_changes_async(user_name)
        if user_name:
            # Invalidate cache after changes
            await self._cache.invalidate_basket(user_name)
        return result

    async def update_items_price(self, product_id: UUID, new_price) -> bool:
        """Update items price and invalidate all basket caches."""
        result = await self._repository.update_items_price(product_id, new_price)
        if result:
            # Invalidate all baskets since price changed affects all users
            await self._cache.invalidate_all_baskets()
        return result

    def _domain_to_dto(self, basket: ShoppingCart) -> ShoppingCartDto:
        """Convert domain model to DTO for caching."""
        from app.modules.basket.application.dtos.shopping_cart_dto import (
            ShoppingCartItemDto,
        )

        items_dto = [
            ShoppingCartItemDto(
                id=item.id,
                shopping_cart_id=item.shopping_cart_id,
                product_id=item.product_id,
                quantity=item.quantity,
                color=item.color,
                price=item.price,
                product_name=item.product_name,
            )
            for item in basket.items
        ]

        return ShoppingCartDto(
            id=basket.id,
            user_name=basket.user_name,
            items=items_dto,
        )

    def _dto_to_domain(self, dto: ShoppingCartDto) -> ShoppingCart:
        """Convert DTO to domain model."""
        from decimal import Decimal

        from app.modules.basket.domain.entities.basket import ShoppingCart, ShoppingCartItem

        basket = ShoppingCart.create(cart_id=dto.id, user_name=dto.user_name)

        for item_dto in dto.items:
            basket.add_item(
                product_id=item_dto.product_id,
                quantity=item_dto.quantity,
                color=item_dto.color,
                price=Decimal(str(item_dto.price)),
                product_name=item_dto.product_name,
            )

        return basket

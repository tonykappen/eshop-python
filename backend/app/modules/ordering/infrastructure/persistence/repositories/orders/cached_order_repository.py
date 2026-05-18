"""Cached order repository - decorator pattern for caching."""

import logging
from uuid import UUID

from app.modules.ordering.domain.entities.order.order import Order
from app.modules.ordering.domain.repositories.order import IOrderRepository

logger = logging.getLogger(__name__)


class CachedOrderRepository(IOrderRepository):
    """
    Cached decorator for order repository.

    Wraps an IOrderRepository and adds caching layer.
    """

    def __init__(self, repository: IOrderRepository, cache_service=None) -> None:
        """
        Initialize cached repository.

        Args:
            repository: Underlying order repository
            cache_service: Cache service (optional, can be added later)
        """
        self._repository = repository
        self._cache_service = cache_service

    async def add(self, order: Order) -> None:
        """Add order - delegate to underlying repository."""
        await self._repository.add(order)
        # Invalidate cache if cache service is available
        if self._cache_service:
            await self._cache_service.invalidate_order(order.id)

    async def get_by_id(self, order_id: UUID) -> Order | None:
        """
        Get order by ID with caching.

        Args:
            order_id: Order ID

        Returns:
            Order if found, None otherwise
        """
        # Try cache first if available
        if self._cache_service:
            cached_order = await self._cache_service.get_order(order_id)
            if cached_order:
                # Convert DTO back to domain (simplified - would need mapper)
                # For now, just use repository
                pass

        # Fall back to repository
        return await self._repository.get_by_id(order_id)

    async def get_all(self, skip: int = 0, take: int = 10) -> tuple[list[Order], int]:
        """Get all orders - delegate to underlying repository."""
        return await self._repository.get_all(skip=skip, take=take)

    async def remove(self, order: Order) -> None:
        """Remove order - delegate to underlying repository and invalidate cache."""
        await self._repository.remove(order)
        if self._cache_service:
            await self._cache_service.invalidate_order(order.id)

    async def save_changes_async(self) -> None:
        """Save changes - delegate to underlying repository."""
        await self._repository.save_changes_async()

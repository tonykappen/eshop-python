"""Basket repository interface."""

from abc import ABC, abstractmethod
from typing import Any

from app.modules.basket.domain.entities.basket import ShoppingCart


class IBasketRepository(ABC):
    """Interface for basket repository operations."""

    @abstractmethod
    async def get_basket(
        self, user_name: str, as_no_tracking: bool = True
    ) -> ShoppingCart:
        """
        Get basket by user name.

        Args:
            user_name: User name
            as_no_tracking: Whether to use no-tracking mode (default: True)

        Returns:
            ShoppingCart instance

        Raises:
            BasketNotFoundException: If basket not found
        """
        pass

    @abstractmethod
    async def create_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """
        Create a new basket.

        Args:
            basket: ShoppingCart to create

        Returns:
            Created ShoppingCart instance
        """
        pass

    @abstractmethod
    async def delete_basket(self, user_name: str) -> bool:
        """
        Delete basket by user name.

        Args:
            user_name: User name

        Returns:
            True if deleted successfully

        Raises:
            BasketNotFoundException: If basket not found
        """
        pass

    @abstractmethod
    async def save_changes_async(self, user_name: str | None = None) -> int:
        """
        Save changes to the database.

        Args:
            user_name: Optional user name for audit purposes

        Returns:
            Number of affected rows
        """
        pass

    @abstractmethod
    async def add_items_to_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """
        Add items to an existing basket.

        Args:
            basket: ShoppingCart containing items to add

        Returns:
            Updated ShoppingCart instance
        """
        pass

    @abstractmethod
    async def update_basket(self, basket: ShoppingCart) -> ShoppingCart:
        """
        Update an existing basket.

        Args:
            basket: ShoppingCart to update

        Returns:
            Updated ShoppingCart instance
        """
        pass

    async def update_items_price(self, product_id: Any, new_price: Any) -> bool:
        """
        Update price for all items with given product_id.

        Args:
            product_id: Product ID to update
            new_price: New price

        Returns:
            True if any items were updated, False otherwise
        """
        return False

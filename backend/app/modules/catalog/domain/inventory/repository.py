# isort: skip_file
"""Inventory repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.core.domain.repository import Repository
from app.modules.catalog.domain.inventory.models.inventory_item import InventoryItem


class InventoryRepository(Repository[InventoryItem, UUID], ABC):
    """Repository interface for InventoryItem aggregate."""

    @abstractmethod
    async def get_by_product_id(self, product_id: UUID) -> InventoryItem | None:
        """
        Get inventory item by product ID.

        Args:
            product_id: Product ID

        Returns:
            InventoryItem if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_low_stock_items(self) -> list[InventoryItem]:
        """
        Get inventory items with low stock.

        Returns:
            List of inventory items with low stock
        """
        pass

    @abstractmethod
    async def get_out_of_stock_items(self) -> list[InventoryItem]:
        """
        Get inventory items that are out of stock.

        Returns:
            List of out of stock inventory items
        """
        pass

    @abstractmethod
    async def get_items_needing_reorder(self) -> list[InventoryItem]:
        """
        Get inventory items that need reordering.

        Returns:
            List of inventory items needing reorder
        """
        pass

    @abstractmethod
    async def exists_by_product_id(self, product_id: UUID) -> bool:
        """
        Check if inventory item exists by product ID.

        Args:
            product_id: Product ID

        Returns:
            True if inventory item exists, False otherwise
        """
        pass

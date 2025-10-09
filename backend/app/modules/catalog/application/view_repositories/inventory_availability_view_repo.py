"""Inventory availability view repository for read models."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.modules.catalog.application.read_models.inventory_availability_view import InventoryAvailabilityView


class InventoryAvailabilityViewRepository(ABC):
    """Repository interface for InventoryAvailabilityView read model."""

    @abstractmethod
    async def get_by_product_id(self, product_id: UUID) -> Optional[InventoryAvailabilityView]:
        """
        Get inventory availability view by product ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            InventoryAvailabilityView if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_low_stock_items(self) -> List[InventoryAvailabilityView]:
        """
        Get inventory availability views with low stock.
        
        Returns:
            List of InventoryAvailabilityView with low stock
        """
        pass

    @abstractmethod
    async def get_out_of_stock_items(self) -> List[InventoryAvailabilityView]:
        """
        Get inventory availability views that are out of stock.
        
        Returns:
            List of out of stock InventoryAvailabilityView
        """
        pass

    @abstractmethod
    async def get_available_items(self) -> List[InventoryAvailabilityView]:
        """
        Get inventory availability views that are available.
        
        Returns:
            List of available InventoryAvailabilityView
        """
        pass

    @abstractmethod
    async def get_items_needing_reorder(self) -> List[InventoryAvailabilityView]:
        """
        Get inventory availability views that need reordering.
        
        Returns:
            List of InventoryAvailabilityView needing reorder
        """
        pass

    @abstractmethod
    async def get_by_stock_status(self, status: str) -> List[InventoryAvailabilityView]:
        """
        Get inventory availability views by stock status.
        
        Args:
            status: Stock status (in_stock, low_stock, out_of_stock)
            
        Returns:
            List of InventoryAvailabilityView with the specified status
        """
        pass

    @abstractmethod
    async def update_view(self, product_id: UUID) -> None:
        """
        Update the read model for a specific product.
        
        Args:
            product_id: Product ID to update
        """
        pass

    @abstractmethod
    async def rebuild_all_views(self) -> None:
        """Rebuild all inventory availability views from domain models."""
        pass



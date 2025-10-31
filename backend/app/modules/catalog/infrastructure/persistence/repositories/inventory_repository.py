"""Inventory repository implementation."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.domain.inventory.models.inventory_item import InventoryItem
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.infrastructure.persistence.models.inventory_item_orm import InventoryItemORM

logger = logging.getLogger(__name__)


class InventoryRepositoryImpl(InventoryRepository):
    """Inventory repository implementation."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.
        
        Args:
            session: Database session
        """
        self.session = session

    async def get_by_id(self, inventory_item_id: UUID) -> Optional[InventoryItem]:
        """
        Get inventory item by ID.
        
        Args:
            inventory_item_id: Inventory item ID
            
        Returns:
            InventoryItem if found, None otherwise
        """
        try:
            stmt = select(InventoryItemORM).where(
                InventoryItemORM.id == inventory_item_id,
                InventoryItemORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            inventory_orm = result.scalar_one_or_none()
            
            if inventory_orm:
                return self._orm_to_domain(inventory_orm)
            return None

        except Exception as e:
            logger.error(f"Error getting inventory item by ID {inventory_item_id}: {e}")
            raise

    async def get_by_product_id(self, product_id: UUID) -> Optional[InventoryItem]:
        """
        Get inventory item by product ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            InventoryItem if found, None otherwise
        """
        try:
            stmt = select(InventoryItemORM).where(
                InventoryItemORM.product_id == product_id,
                InventoryItemORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            inventory_orm = result.scalar_one_or_none()
            
            if inventory_orm:
                return self._orm_to_domain(inventory_orm)
            return None
            
        except Exception as e:
            logger.error(f"Error getting inventory item by product ID {product_id}: {e}")
            raise

    async def get_low_stock_items(self) -> List[InventoryItem]:
        """
        Get inventory items with low stock.
        
        Returns:
            List of inventory items with low stock
        """
        try:
            stmt = select(InventoryItemORM).where(
                InventoryItemORM.quantity <= InventoryItemORM.reorder_threshold,
                InventoryItemORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            inventory_items_orm = result.scalars().all()
            
            return [self._orm_to_domain(inventory_orm) for inventory_orm in inventory_items_orm]
            
        except Exception as e:
            logger.error(f"Error getting low stock items: {e}")
            raise

    async def get_out_of_stock_items(self) -> List[InventoryItem]:
        """
        Get out of stock inventory items.
        
        Returns:
            List of out of stock inventory items
        """
        try:
            stmt = select(InventoryItemORM).where(
                InventoryItemORM.quantity <= 0,
                InventoryItemORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            inventory_items_orm = result.scalars().all()
            
            return [self._orm_to_domain(inventory_orm) for inventory_orm in inventory_items_orm]
            
        except Exception as e:
            logger.error(f"Error getting out of stock items: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[InventoryItem]:
        """
        Get all inventory items with pagination.
        
        Args:
            skip: Number of inventory items to skip
            limit: Maximum number of inventory items to return
            
        Returns:
            List of inventory items
        """
        try:
            stmt = select(InventoryItemORM).where(
                InventoryItemORM.is_deleted == False
            ).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            inventory_items_orm = result.scalars().all()
            
            return [self._orm_to_domain(inventory_orm) for inventory_orm in inventory_items_orm]
            
        except Exception as e:
            logger.error(f"Error getting all inventory items: {e}")
            raise

    async def count(self) -> int:
        """
        Get total count of inventory items.
        
        Returns:
            Total number of inventory items
        """
        try:
            from sqlalchemy import func
            stmt = select(func.count(InventoryItemORM.id)).where(
                InventoryItemORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting inventory items: {e}")
            raise

    async def exists_by_product_id(self, product_id: UUID) -> bool:
        """
        Check if inventory item exists by product ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            True if inventory item exists, False otherwise
        """
        try:
            stmt = select(InventoryItemORM.id).where(
                InventoryItemORM.product_id == product_id,
                InventoryItemORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking inventory item existence by product ID {product_id}: {e}")
            raise

    async def add(self, inventory_item: InventoryItem) -> None:
        """
        Add a new inventory item.
        
        Args:
            inventory_item: Inventory item to add
        """
        try:
            inventory_orm = self._domain_to_orm(inventory_item)
            self.session.add(inventory_orm)
            await self.session.flush()

        except Exception as e:
            logger.error(f"Error adding inventory item: {e}")
            raise

    async def update(self, inventory_item: InventoryItem) -> None:
        """
        Update an existing inventory item.
        
        Args:
            inventory_item: Inventory item to update
        """
        try:
            stmt = update(InventoryItemORM).where(
                InventoryItemORM.id == inventory_item.id
            ).values(
                product_id=inventory_item.product_id,
                quantity=inventory_item.quantity,
                reserved_quantity=inventory_item.reserved_quantity,
                reorder_threshold=inventory_item.reorder_threshold,
                max_stock_threshold=inventory_item.max_stock_threshold,
                version=inventory_item.version,
            )
            await self.session.execute(stmt)
            
        except Exception as e:
            logger.error(f"Error updating inventory item: {e}")
            raise

    async def delete(self, inventory_item_id: UUID) -> None:
        """
        Delete an inventory item (soft delete).
        
        Args:
            inventory_item_id: Inventory item ID to delete
        """
        try:
            stmt = update(InventoryItemORM).where(
                InventoryItemORM.id == inventory_item_id
            ).values(
                is_deleted=True
            )
            await self.session.execute(stmt)
            
        except Exception as e:
            logger.error(f"Error deleting inventory item: {e}")
            raise

    def _orm_to_domain(self, inventory_orm: InventoryItemORM) -> InventoryItem:
        """
        Convert ORM model to domain model.
        
        Args:
            inventory_orm: Inventory item ORM model
            
        Returns:
            InventoryItem domain model
        """
        return InventoryItem(
            id=inventory_orm.id,
            product_id=inventory_orm.product_id,
            quantity=inventory_orm.quantity,
            reserved_quantity=inventory_orm.reserved_quantity,
            reorder_threshold=inventory_orm.reorder_threshold,
            max_stock_threshold=inventory_orm.max_stock_threshold,
            version=inventory_orm.version,
        )

    def _domain_to_orm(self, inventory_item: InventoryItem) -> InventoryItemORM:
        """
        Convert domain model to ORM model.
        
        Args:
            inventory_item: Inventory item domain model
            
        Returns:
            InventoryItem ORM model
        """
        return InventoryItemORM(
            id=inventory_item.id,
            product_id=inventory_item.product_id,
            quantity=inventory_item.quantity,
            reserved_quantity=inventory_item.reserved_quantity,
            reorder_threshold=inventory_item.reorder_threshold,
            max_stock_threshold=inventory_item.max_stock_threshold,
            version=inventory_item.version,
        )

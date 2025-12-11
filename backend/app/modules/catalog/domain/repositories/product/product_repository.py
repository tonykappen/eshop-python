"""Product repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.domain.repository import Repository
from app.modules.catalog.domain.entities.product.product import Product


class ProductRepository(Repository[Product, UUID], ABC):
    """Repository interface for Product aggregate."""

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get product by SKU.
        
        Args:
            sku: Product SKU
            
        Returns:
            Product if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Product]:
        """
        Get product by name.
        
        Args:
            name: Product name
            
        Returns:
            Product if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_category(self, category: str) -> List[Product]:
        """
        Get products by category.
        
        Args:
            category: Category name
            
        Returns:
            List of products in the category
        """
        pass

    @abstractmethod
    async def search_by_name(self, search_term: str) -> List[Product]:
        """
        Search products by name.
        
        Args:
            search_term: Search term
            
        Returns:
            List of products matching the search term
        """
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products with pagination.
        
        Args:
            skip: Number of products to skip
            limit: Maximum number of products to return
            
        Returns:
            List of products
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        Get total count of products.
        
        Returns:
            Total number of products
        """
        pass

    @abstractmethod
    async def exists_by_sku(self, sku: str) -> bool:
        """
        Check if product exists by SKU.
        
        Args:
            sku: Product SKU
            
        Returns:
            True if product exists, False otherwise
        """
        pass

    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """
        Check if product exists by name.
        
        Args:
            name: Product name
            
        Returns:
            True if product exists, False otherwise
        """
        pass



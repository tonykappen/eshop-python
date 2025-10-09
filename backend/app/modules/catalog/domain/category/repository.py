"""Category repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.core.domain.repository import Repository
from app.modules.catalog.domain.category.models.category import Category


class CategoryRepository(Repository[Category, UUID], ABC):
    """Repository interface for Category aggregate."""

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Category]:
        """
        Get category by name.
        
        Args:
            name: Category name
            
        Returns:
            Category if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_parent_id(self, parent_id: UUID) -> List[Category]:
        """
        Get categories by parent ID.
        
        Args:
            parent_id: Parent category ID
            
        Returns:
            List of child categories
        """
        pass

    @abstractmethod
    async def get_root_categories(self) -> List[Category]:
        """
        Get root categories (categories without parent).
        
        Returns:
            List of root categories
        """
        pass

    @abstractmethod
    async def get_active_categories(self) -> List[Category]:
        """
        Get active categories.
        
        Returns:
            List of active categories
        """
        pass

    @abstractmethod
    async def exists_by_name(self, name: str) -> bool:
        """
        Check if category exists by name.
        
        Args:
            name: Category name
            
        Returns:
            True if category exists, False otherwise
        """
        pass



"""Product repository interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
from uuid import UUID

from app.core.domain.repository import Repository

if TYPE_CHECKING:
    from app.modules.catalog.domain.entities.product.product import Product


class ProductRepository(Repository["Product", UUID], ABC):
    """Repository interface for Product aggregate."""

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Product | None:
        """
        Get product by SKU.

        Args:
            sku: Product SKU

        Returns:
            Product if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Product | None:
        """
        Get product by name.

        Args:
            name: Product name

        Returns:
            Product if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_category(
        self, category: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """
        Get products by category with pagination.

        Args:
            category: Category name
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (products, total_count)
        """
        pass

    @abstractmethod
    async def search_by_name(self, search_term: str) -> list[Product]:
        """
        Search products by name.

        Args:
            search_term: Search term

        Returns:
            List of products matching the search term
        """
        pass

    @abstractmethod
    async def get_all(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """
        Get all products with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (products, total_count)
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

    @abstractmethod
    async def exists(self, product_id: UUID) -> bool:
        """
        Check if a non-deleted product exists by ID.

        Args:
            product_id: Product ID

        Returns:
            True if product exists, False otherwise
        """
        pass

    @abstractmethod
    async def delete(
        self,
        product_id: UUID,
        deleted_by: UUID | None = None,
        deletion_reason: str | None = None,
    ) -> bool:
        """
        Delete a product (typically soft delete).

        Args:
            product_id: Product ID to delete
            deleted_by: User performing the deletion (optional)
            deletion_reason: Reason for deletion (optional)

        Returns:
            True if a row was affected, False otherwise
        """
        pass

    @abstractmethod
    async def get_deleted_by_id(self, product_id: UUID) -> Product | None:
        """Get a soft-deleted product by ID."""
        pass

    @abstractmethod
    async def get_deleted_products(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """Get soft-deleted products with pagination."""
        pass

    @abstractmethod
    async def restore_product(
        self, product_id: UUID, restored_by: UUID | None = None
    ) -> bool:
        """Restore a soft-deleted product."""
        pass

    @abstractmethod
    async def search(
        self, search_term: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """
        Search products (e.g. by name or description) with pagination.

        Args:
            search_term: Search term
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (products, total_count)
        """
        pass

"""Product listing view repository for read models."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.catalog.application.read_models.product_listing_view import (
    ProductListingView,
)


class ProductListingViewRepository(ABC):
    """Repository interface for ProductListingView read model."""

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> ProductListingView | None:
        """
        Get product listing view by ID.

        Args:
            product_id: Product ID

        Returns:
            ProductListingView if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_sku(self, sku: str) -> ProductListingView | None:
        """
        Get product listing view by SKU.

        Args:
            sku: Product SKU

        Returns:
            ProductListingView if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_category(self, category: str) -> list[ProductListingView]:
        """
        Get product listing views by category.

        Args:
            category: Category name

        Returns:
            List of ProductListingView in the category
        """
        pass

    @abstractmethod
    async def search_by_name(self, search_term: str) -> list[ProductListingView]:
        """
        Search product listing views by name.

        Args:
            search_term: Search term

        Returns:
            List of ProductListingView matching the search term
        """
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        search_term: str | None = None,
    ) -> list[ProductListingView]:
        """
        Get all product listing views with pagination and filtering.

        Args:
            skip: Number of products to skip
            limit: Maximum number of products to return
            category: Optional category filter
            search_term: Optional search term filter

        Returns:
            List of ProductListingView
        """
        pass

    @abstractmethod
    async def count(
        self, category: str | None = None, search_term: str | None = None
    ) -> int:
        """
        Get total count of product listing views.

        Args:
            category: Optional category filter
            search_term: Optional search term filter

        Returns:
            Total number of products
        """
        pass

    @abstractmethod
    async def get_by_price_range(
        self, min_price: float, max_price: float, currency: str = "USD"
    ) -> list[ProductListingView]:
        """
        Get product listing views by price range.

        Args:
            min_price: Minimum price
            max_price: Maximum price
            currency: Currency code

        Returns:
            List of ProductListingView in price range
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
        """Rebuild all product listing views from domain models."""
        pass

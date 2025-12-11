"""Catalog Unit of Work interface."""

from abc import ABC, abstractmethod
from typing import Type, TypeVar

from app.core.database.session import AsyncSession

from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.domain.repositories.product.product_repository import ProductRepository

T = TypeVar("T")


class ICatalogUnitOfWork(ABC):
    """
    Unit of Work interface for catalog module.
    
    Provides access to repositories and transaction management for catalog operations.
    """

    @property
    @abstractmethod
    def products(self) -> ProductRepository:
        """Get product repository."""
        ...

    @property
    @abstractmethod
    def categories(self) -> CategoryRepository:
        """Get category repository."""
        ...

    @property
    @abstractmethod
    def inventory(self) -> InventoryRepository:
        """Get inventory repository."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    @abstractmethod
    async def __aenter__(self) -> "ICatalogUnitOfWork":
        """Async context manager entry."""
        ...

    @abstractmethod
    async def __aexit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: type[BaseException] | None) -> None:
        """Async context manager exit."""
        ...

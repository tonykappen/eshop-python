"""SQL-based implementation of ICatalogUnitOfWork."""

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.application.transactions.commit_interceptors import (
    commit_interceptor_registry,
)
from app.modules.catalog.application.unit_of_work.catalog_unit_of_work import (
    ICatalogUnitOfWork,
)
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.domain.repositories.product.product_repository import ProductRepository
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlProductRepository,
    SqlCategoryRepository,
    SqlInventoryRepository,
)

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


class SqlCatalogUnitOfWork(ICatalogUnitOfWork):
    """SQL-based implementation of ICatalogUnitOfWork for catalog module."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize the SQL catalog unit of work.
        
        Args:
            session: Database session
        """
        self._session = session
        self._products_repo: ProductRepository | None = None
        self._categories_repo: CategoryRepository | None = None
        self._inventory_repo: InventoryRepository | None = None
        self._entities: list[object] = []

    @property
    def products(self) -> ProductRepository:
        """Get product repository."""
        if self._products_repo is None:
            self._products_repo = SqlProductRepository(self._session)
        return self._products_repo

    @property
    def categories(self) -> CategoryRepository:
        """Get category repository."""
        if self._categories_repo is None:
            self._categories_repo = SqlCategoryRepository(self._session)
        return self._categories_repo

    @property
    def inventory(self) -> InventoryRepository:
        """Get inventory repository."""
        if self._inventory_repo is None:
            self._inventory_repo = SqlInventoryRepository(self._session)
        return self._inventory_repo

    async def commit(self) -> None:
        """
        Commit the current transaction with interceptors.
        
        Raises:
            Exception: If commit fails
        """
        try:
            # Execute before commit hooks
            await commit_interceptor_registry.execute_before_commit(
                self._session, self._entities
            )

            # Flush changes to database
            await self._session.flush()

            # Commit the transaction
            await self._session.commit()

            # Execute after commit hooks
            await commit_interceptor_registry.execute_after_commit(
                self._session, self._entities
            )

            logger.info(f"Successfully committed {len(self._entities)} entities")

        except Exception as e:
            # Execute rollback hooks
            await commit_interceptor_registry.execute_on_rollback(
                self._session, self._entities, e
            )

            # Rollback the transaction
            await self._session.rollback()

            logger.error(f"Transaction rolled back due to error: {e}")
            raise

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()
        logger.info("Transaction rolled back")

    async def __aenter__(self) -> "SqlCatalogUnitOfWork":
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: "TracebackType | None",
    ) -> None:
        """Async context manager exit."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()












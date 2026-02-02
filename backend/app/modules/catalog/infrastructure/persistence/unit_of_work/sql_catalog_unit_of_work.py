"""SQL-based implementation of ICatalogUnitOfWork."""

import logging
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.transactions.commit_interceptors import (
    commit_interceptor_registry,
)
from app.modules.catalog.application.unit_of_work.catalog_unit_of_work import (
    ICatalogUnitOfWork,
)
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
from app.modules.catalog.application.services.catalog_cache_service import (
    CatalogCacheService,
    RedisCacheService,
)
from app.modules.catalog.domain.repositories.product.product_repository import (
    ProductRepository,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import (
    CachedProductRepository,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlCategoryRepository,
    SqlInventoryRepository,
    SqlProductRepository,
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
        """Get product repository with Redis caching."""
        if self._products_repo is None:
            sql_repo = SqlProductRepository(self._session)
            cache_service = CatalogCacheService(RedisCacheService())
            self._products_repo = CachedProductRepository(sql_repo, cache_service)
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

        Collects domain events from entities before commit to ensure
        outbox enqueuing happens inside the transaction.

        Raises:
            Exception: If commit fails
        """
        try:
            # Collect all entities with domain events before commit
            # This ensures domain events are available to interceptors
            entities_with_events = []
            
            # Collect from tracked entities list
            entities_with_events.extend(self._entities)
            
            # Also collect from SQLAlchemy session's change tracker
            # (in case entities are tracked by SQLAlchemy but not in _entities)
            # Note: This is a fallback - ideally entities should be in _entities
            for obj in self._session.identity_map.values():
                if obj not in entities_with_events:
                    entities_with_events.append(obj)
            
            # Collect domain events from all entities before commit
            # This ensures they're available to the OutboxEnqueuerInterceptor
            all_domain_events = []
            for entity in entities_with_events:
                if hasattr(entity, "domain_events") and entity.domain_events:
                    all_domain_events.extend(entity.domain_events)

            if all_domain_events:
                logger.debug(
                    f"Collected {len(all_domain_events)} domain events from {len(entities_with_events)} entities"
                )

            # Execute before commit hooks (outbox enqueuing happens here)
            await commit_interceptor_registry.execute_before_commit(
                self._session, entities_with_events
            )

            # Flush changes to database (includes outbox rows)
            await self._session.flush()

            # Commit the transaction (product + outbox row atomically)
            await self._session.commit()

            # Execute after commit hooks (domain event dispatching happens here)
            await commit_interceptor_registry.execute_after_commit(
                self._session, entities_with_events
            )

            logger.info(f"Successfully committed {len(entities_with_events)} entities")

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

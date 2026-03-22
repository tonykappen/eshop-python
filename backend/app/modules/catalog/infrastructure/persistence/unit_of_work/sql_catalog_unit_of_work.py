"""SQL-based implementation of ICatalogUnitOfWork."""

from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging.base_logger import BaseLogger
from app.core.transactions.commit_interceptors import commit_interceptor_registry
from app.modules.catalog.application.services.catalog_cache_service import (
    CatalogCacheService,
    RedisCacheService,
)
from app.modules.catalog.application.unit_of_work.catalog_unit_of_work import (
    ICatalogUnitOfWork,
)
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.inventory.repository import InventoryRepository
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

logger = BaseLogger(__name__)


class SqlCatalogUnitOfWork(ICatalogUnitOfWork):
    """SQL-based implementation of ICatalogUnitOfWork for catalog module."""

    def __init__(
        self,
        session: AsyncSession,
        cache_service: CatalogCacheService | None = None,
    ) -> None:
        self._session = session
        self._cache_service = cache_service
        self._products_repo: ProductRepository | None = None
        self._categories_repo: CategoryRepository | None = None
        self._inventory_repo: InventoryRepository | None = None
        self._tracked: list[object] = []

    @property
    def products(self) -> ProductRepository:
        """Get product repository with Redis caching."""
        if self._products_repo is None:
            sql_repo = SqlProductRepository(self._session)
            if self._cache_service is not None:
                self._products_repo = CachedProductRepository(sql_repo, self._cache_service)
            else:
                try:
                    cache_svc = CatalogCacheService(RedisCacheService())
                    self._products_repo = CachedProductRepository(sql_repo, cache_svc)
                except Exception:
                    self._products_repo = sql_repo
        return self._products_repo

    @property
    def categories(self) -> CategoryRepository:
        if self._categories_repo is None:
            self._categories_repo = SqlCategoryRepository(self._session)
        return self._categories_repo

    @property
    def inventory(self) -> InventoryRepository:
        if self._inventory_repo is None:
            self._inventory_repo = SqlInventoryRepository(self._session)
        return self._inventory_repo

    def track(self, entity: object) -> None:
        """Explicitly track an aggregate so its domain events are visible to interceptors."""
        if entity not in self._tracked:
            self._tracked.append(entity)

    def collect_domain_events(self) -> list[Any]:
        """Collect domain events from all tracked entities and session-managed objects."""
        events: list[Any] = []
        seen: set[int] = set()

        for entity in self._gather_all_entities():
            eid = id(entity)
            if eid in seen:
                continue
            seen.add(eid)
            if hasattr(entity, "domain_events") and entity.domain_events:
                events.extend(entity.domain_events)

        return events

    def _gather_all_entities(self) -> list[object]:
        """Merge explicitly tracked entities with SQLAlchemy session state.

        Only includes tracked entities and objects that SQLAlchemy considers
        pending/dirty/deleted — NOT the full identity map, which contains
        read-only objects whose modification by interceptors would trigger
        unwanted secondary UPDATEs.
        """
        entities: list[object] = list(self._tracked)
        for obj in list(self._session.new) + list(self._session.dirty) + list(self._session.deleted):
            if obj not in entities:
                entities.append(obj)
        return entities

    async def commit(self) -> None:
        """
        Commit the current transaction with interceptors.
        Domain events are collected deterministically from session state + tracked entities.
        """
        try:
            all_entities = self._gather_all_entities()

            await commit_interceptor_registry.execute_before_commit(
                self._session, all_entities
            )

            await self._session.flush()
            await self._session.commit()

            await commit_interceptor_registry.execute_after_commit(
                self._session, all_entities
            )

            await self._invalidate_product_caches(all_entities)

            logger.log_with_context(
                "Successfully committed",
                context={"entity_count": len(all_entities)},
            )

        except Exception as e:
            await commit_interceptor_registry.execute_on_rollback(
                self._session, self._gather_all_entities(), e
            )
            await self._session.rollback()
            logger.log_error_with_context("Transaction rolled back", error=e)
            raise

    async def _invalidate_product_caches(self, entities: list[object]) -> None:
        """Invalidate catalog-specific caches for committed product entities."""
        if self._cache_service is None:
            return
        try:
            from app.modules.catalog.domain.entities.product.product import Product as ProductEntity
            from app.modules.catalog.infrastructure.persistence.orm.product_orm import (
                ProductORM,
            )

            has_product_changes = False
            for entity in entities:
                product_id = getattr(entity, "id", None)
                if product_id is None:
                    continue
                if isinstance(entity, (ProductEntity, ProductORM)) or (
                    hasattr(entity, "name") and hasattr(entity, "sku")
                ):
                    await self._cache_service.invalidate_product(product_id)
                    has_product_changes = True

            if has_product_changes:
                await self._cache_service.invalidate_products_list()
        except Exception as e:
            logger.log_warning_with_context(
                "Post-commit cache invalidation failed (best-effort)",
                context={"error": str(e)},
            )

    async def rollback(self) -> None:
        await self._session.rollback()
        logger.log_with_context("Transaction rolled back")

    async def __aenter__(self) -> "SqlCatalogUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: "TracebackType | None",
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

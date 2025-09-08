"""Catalog data seeder with 1-1 parity to .NET CatalogDataSeeder."""

from app.core.database.seeding import (
    IDataSeeder,
    check_if_data_exists,
    ensure_schema_exists,
)
from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger
from app.core.mapping.orm_mapper import ORMMapper
from app.modules.catalog.infrastructure.orm_models import ProductORM
from app.modules.catalog.infrastructure.seed.initial_data import InitialData

logger = BaseLogger(__name__)


class CatalogDataSeeder(IDataSeeder):
    """Catalog data seeder - matches .NET CatalogDataSeeder."""

    async def seed_all_async(self) -> None:
        """Seed all catalog data - matches .NET SeedAllAsync()."""
        logger.log_with_context("🔄 Seeding catalog data...", "info")

        # Ensure catalog schema exists
        await ensure_schema_exists("catalog")

        # Check if products already exist
        if await check_if_data_exists("products", "catalog"):
            logger.log_with_context("✅ Catalog products already exist, skipping seeding", "info")
            return

        # Seed products
        await self._seed_products()

        logger.log_with_context("✅ Catalog data seeding completed", "info")

    async def _seed_products(self) -> None:
        """Seed products data."""
        async with AsyncSessionLocal() as session:
            try:
                # Get initial products
                products = InitialData.get_products()

                # Convert domain models to ORM models
                orm_products = []
                for product in products:
                    orm_product = ORMMapper.to_orm(product, ProductORM)
                    orm_products.append(orm_product)

                # Add products to session
                session.add_all(orm_products)

                # Commit changes
                await session.commit()

                logger.log_with_context(
                    "✅ Seeded products",
                    "info",
                    context={"product_count": len(products)}
                )

            except Exception as e:
                logger.log_error_with_context(
                    "❌ Failed to seed products",
                    error=e
                )
                await session.rollback()
                raise

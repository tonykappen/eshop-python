"""Catalog data seeder with 1-1 parity to .NET CatalogDataSeeder."""

from eshop.core.database.seeding import (
    IDataSeeder,
    check_if_data_exists,
    ensure_schema_exists,
)
from eshop.core.database.session import AsyncSessionLocal
from eshop.core.logging.logger import get_logger
from eshop.core.mapping.orm_mapper import ORMMapper
from eshop.modules.catalog.infrastructure.orm_models import ProductORM
from eshop.modules.catalog.infrastructure.seed.initial_data import InitialData

logger = get_logger(__name__)


class CatalogDataSeeder(IDataSeeder):
    """Catalog data seeder - matches .NET CatalogDataSeeder."""

    async def seed_all_async(self) -> None:
        """Seed all catalog data - matches .NET SeedAllAsync()."""
        logger.info("🔄 Seeding catalog data...")

        # Ensure catalog schema exists
        await ensure_schema_exists("catalog")

        # Check if products already exist
        if await check_if_data_exists("products", "catalog"):
            logger.info("✅ Catalog products already exist, skipping seeding")
            return

        # Seed products
        await self._seed_products()

        logger.info("✅ Catalog data seeding completed")

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

                logger.info(f"✅ Seeded {len(products)} products")

            except Exception as e:
                logger.error(f"❌ Failed to seed products: {e}")
                await session.rollback()
                raise

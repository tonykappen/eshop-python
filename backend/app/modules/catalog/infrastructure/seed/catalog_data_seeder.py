"""Catalog data seeder with 1-1 parity to .NET CatalogDataSeeder."""

from app.core.database.seeding import (
    IDataSeeder,
    check_if_data_exists,
    ensure_schema_exists,
)
from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger
from app.modules.catalog.infrastructure.persistence.models.product_orm import ProductORM
from app.modules.catalog.infrastructure.seed.initial_data import CatalogInitialData

logger = BaseLogger(__name__)


class CatalogDataSeeder(IDataSeeder):
    """Catalog data seeder - matches .NET CatalogDataSeeder."""

    async def seed_all_async(self) -> None:
        """Seed all catalog data - matches .NET SeedAllAsync()."""
        logger.log_with_context("Seeding catalog data...", "info")

        # Ensure catalog schema exists
        await ensure_schema_exists("catalog")

        # Check if products already exist
        if await check_if_data_exists("products", "catalog"):
            logger.log_with_context(
                "[OK] Catalog products already exist, skipping seeding", "info"
            )
            return

        # Seed products
        await self._seed_products()

        logger.log_with_context("[OK] Catalog data seeding completed", "info")

    async def _seed_products(self) -> None:
        """Seed products data."""
        async with AsyncSessionLocal() as session:
            try:
                # Get initial products
                products = CatalogInitialData.get_initial_products()

                # Convert domain models to ORM models
                orm_products = []
                for product in products:
                    # Create ORM product manually to match the new schema
                    orm_product = ProductORM(
                        id=product.id,
                        name=product.name,
                        sku=str(
                            product.sku.value
                        ),  # Convert SKU value object to string
                        description=product.description,
                        image_file=product.image_file,
                        price_amount=str(
                            product.price.amount
                        ),  # Convert Money amount to string
                        price_currency=product.price.currency,  # Extract currency from Money
                        categories=product.category,  # Note: domain uses 'category', ORM uses 'categories'
                        version=product.version if hasattr(product, "version") else 1,
                        created_at=(
                            product.created_at
                            if hasattr(product, "created_at")
                            else None
                        ),
                        updated_at=(
                            product.updated_at
                            if hasattr(product, "updated_at")
                            else None
                        ),
                        created_by=(
                            product.created_by
                            if hasattr(product, "created_by")
                            else None
                        ),
                        updated_by=(
                            product.updated_by
                            if hasattr(product, "updated_by")
                            else None
                        ),
                        is_deleted=False,
                    )

                    logger.log_with_context(
                        "Converted domain entity Product to ORM model ProductORM",
                        "debug",
                    )
                    logger.log_with_context(
                        f"Converted price for {product.name}: {{'amount': {product.price.amount}, 'currency': '{product.price.currency}'}} -> {orm_product.price_amount}",
                        "debug",
                    )

                    orm_products.append(orm_product)

                # Add products to session
                session.add_all(orm_products)

                # Commit changes
                await session.commit()

                logger.log_with_context(
                    "[OK] Seeded products",
                    "info",
                    context={"product_count": len(products)},
                )

            except Exception as e:
                logger.log_error_with_context(
                    "[FAILED] Failed to seed products",
                    error=e,
                    context={"error_type": type(e).__name__, "error_details": str(e)},
                )
                await session.rollback()
                raise

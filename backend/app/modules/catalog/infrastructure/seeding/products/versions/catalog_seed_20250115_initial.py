"""Initial catalog seed data aligned with alembic migration."""

from uuid import uuid4

from app.core.logging.base_logger import BaseLogger
from app.modules.catalog.infrastructure.persistence.orm.category_orm import \
    CategoryORM
from app.modules.catalog.infrastructure.persistence.orm.inventory_item_orm import \
    InventoryItemORM
from app.modules.catalog.infrastructure.persistence.orm.product_orm import \
    ProductORM
from app.modules.catalog.infrastructure.seeding.products.seed_registry import \
    Seed
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

logger = BaseLogger(__name__)


class CatalogInitialSeed(Seed):
    """Initial seed for catalog data."""

    def __init__(self):
        """Initialize the initial catalog seed."""
        super().__init__(
            version="catalog_seed_20250115_initial",
            description="Initial catalog data with products, categories, and inventory",
        )

    async def execute(self, session: AsyncSession) -> None:
        """
        Execute the initial catalog seed.

        Args:
            session: Database session
        """
        logger.log_with_context("Executing initial catalog seed")

        # Create categories first
        categories = await self._create_categories(session)

        # Create products
        products = await self._create_products(session, categories)

        # Create inventory items
        await self._create_inventory_items(session, products)

        logger.log_with_context("Initial catalog seed completed successfully")

    async def _create_categories(self, session: AsyncSession) -> dict[str, str]:
        """
        Create initial categories.

        Args:
            session: Database session

        Returns:
            Dictionary mapping category names to IDs
        """
        categories_data = [
            {
                "id": str(uuid4()),
                "name": "Electronics",
                "description": "Electronic devices and gadgets",
                "parent_id": None,
                "is_active": True,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "Clothing",
                "description": "Clothing and apparel",
                "parent_id": None,
                "is_active": True,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "Home & Garden",
                "description": "Home and garden products",
                "parent_id": None,
                "is_active": True,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "Books & Media",
                "description": "Books and media products",
                "parent_id": None,
                "is_active": True,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "Sports & Outdoors",
                "description": "Sports and outdoor equipment",
                "parent_id": None,
                "is_active": True,
                "version": 1,
                "is_deleted": False,
            },
        ]

        category_ids: dict[str, str] = {}

        for category_data in categories_data:
            await session.execute(insert(CategoryORM).values(**category_data))
            category_ids[str(category_data["name"])] = str(category_data["id"])

        logger.log_with_context(
            "Created categories", context={"category_count": len(categories_data)}
        )
        return category_ids

    async def _create_products(
        self, session: AsyncSession, categories: dict[str, str]
    ) -> dict[str, str]:
        """
        Create initial products.

        Args:
            session: Database session
            categories: Dictionary mapping category names to IDs

        Returns:
            Dictionary mapping product SKUs to IDs
        """
        products_data = [
            {
                "id": str(uuid4()),
                "name": "iPhone 15 Pro",
                "sku": "IPHONE-15-PRO-256",
                "description": "Latest iPhone with advanced camera system and A17 Pro chip",
                "image_file": "/images/iphone-15-pro.jpg",
                "price_amount": "999.00",
                "price_currency": "USD",
                "categories": ["Electronics", "Smartphones"],
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "Samsung Galaxy S24 Ultra",
                "sku": "SAMSUNG-S24-ULTRA-512",
                "description": "Premium Android smartphone with S Pen and advanced AI features",
                "image_file": "/images/samsung-s24-ultra.jpg",
                "price_amount": "1199.00",
                "price_currency": "USD",
                "categories": ["Electronics", "Smartphones"],
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "MacBook Pro 16-inch",
                "sku": "MACBOOK-PRO-16-M3",
                "description": "Powerful laptop with M3 chip for professional work",
                "image_file": "/images/macbook-pro-16.jpg",
                "price_amount": "2499.00",
                "price_currency": "USD",
                "categories": ["Electronics", "Laptops"],
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "Nike Air Max 270",
                "sku": "NIKE-AIR-MAX-270-BLK",
                "description": "Comfortable running shoes with Air Max technology",
                "image_file": "/images/nike-air-max-270.jpg",
                "price_amount": "150.00",
                "price_currency": "USD",
                "categories": ["Clothing", "Shoes"],
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "Dyson V15 Detect Vacuum",
                "sku": "DYSON-V15-DETECT",
                "description": "Advanced cordless vacuum with laser dust detection",
                "image_file": "/images/dyson-v15-detect.jpg",
                "price_amount": "749.00",
                "price_currency": "USD",
                "categories": ["Home & Garden", "Cleaning"],
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "name": "The Psychology of Money",
                "sku": "BOOK-PSYCHOLOGY-MONEY",
                "description": "Timeless lessons on wealth, greed, and happiness",
                "image_file": "/images/psychology-of-money.jpg",
                "price_amount": "16.99",
                "price_currency": "USD",
                "categories": ["Books & Media", "Business"],
                "version": 1,
                "is_deleted": False,
            },
        ]

        product_ids: dict[str, str] = {}

        for product_data in products_data:
            await session.execute(insert(ProductORM).values(**product_data))
            product_ids[str(product_data["sku"])] = str(product_data["id"])

        logger.log_with_context(
            "Created products", context={"product_count": len(products_data)}
        )
        return product_ids

    async def _create_inventory_items(
        self, session: AsyncSession, products: dict[str, str]
    ) -> None:
        """
        Create initial inventory items.

        Args:
            session: Database session
            products: Dictionary mapping product SKUs to IDs
        """
        inventory_data = [
            {
                "id": str(uuid4()),
                "product_id": products["IPHONE-15-PRO-256"],
                "quantity": 50,
                "reserved_quantity": 5,
                "reorder_threshold": 10,
                "max_stock_threshold": 100,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "product_id": products["SAMSUNG-S24-ULTRA-512"],
                "quantity": 30,
                "reserved_quantity": 3,
                "reorder_threshold": 8,
                "max_stock_threshold": 80,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "product_id": products["MACBOOK-PRO-16-M3"],
                "quantity": 20,
                "reserved_quantity": 2,
                "reorder_threshold": 5,
                "max_stock_threshold": 50,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "product_id": products["NIKE-AIR-MAX-270-BLK"],
                "quantity": 100,
                "reserved_quantity": 10,
                "reorder_threshold": 20,
                "max_stock_threshold": 200,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "product_id": products["DYSON-V15-DETECT"],
                "quantity": 15,
                "reserved_quantity": 1,
                "reorder_threshold": 5,
                "max_stock_threshold": 30,
                "version": 1,
                "is_deleted": False,
            },
            {
                "id": str(uuid4()),
                "product_id": products["BOOK-PSYCHOLOGY-MONEY"],
                "quantity": 200,
                "reserved_quantity": 20,
                "reorder_threshold": 50,
                "max_stock_threshold": 500,
                "version": 1,
                "is_deleted": False,
            },
        ]

        for inventory_item_data in inventory_data:
            await session.execute(
                insert(InventoryItemORM).values(**inventory_item_data)
            )

        logger.log_with_context(
            "Created inventory items", context={"inventory_count": len(inventory_data)}
        )

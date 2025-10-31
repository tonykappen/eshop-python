"""Product repository implementation for database operations."""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.domain.product.models.product import Product
from app.modules.catalog.domain.value_objects import Money, SKU
from app.modules.catalog.infrastructure.orm_models import ProductORM

logger = logging.getLogger(__name__)


class ProductRepository:
    """Repository for Product entities with real database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _orm_to_domain(self, product_orm: ProductORM) -> Product:
        """
        Convert ORM model to domain model.
        
        Args:
            product_orm: Product ORM model
            
        Returns:
            Product domain model
            
        Raises:
            ValueError: If conversion fails
        """
        try:
            # Get SKU from ORM model (now part of database schema)
            sku_value = getattr(product_orm, 'sku', None)
            if not sku_value:
                # Fallback: Generate a SKU from the product ID if not in database
                # SKU validator requires 3-50 chars, alphanumeric with hyphens/underscores
                sku_raw = str(product_orm.id).replace("-", "").upper()
                sku_value = sku_raw[:50]  # Max 50 chars per validator
                if len(sku_value) < 3:
                    sku_value = sku_value.ljust(3, "0")
            
            # Convert price from price_amount and price_currency to Money object
            price_amount_str = getattr(product_orm, 'price_amount', None)
            price_currency = getattr(product_orm, 'price_currency', 'USD')
            
            if not price_amount_str:
                raise ValueError("Product price_amount cannot be None")
            
            # price_amount is stored as String(20) in database, convert to Decimal
            price_amount = Decimal(str(price_amount_str))
            price = Money(
                amount=price_amount,
                currency=price_currency if price_currency else "USD"
            )
            
            # Handle ID conversion - it might be UUID or string
            product_id = product_orm.id
            if isinstance(product_id, str):
                product_id = UUID(product_id)
            elif not isinstance(product_id, UUID):
                product_id = UUID(str(product_id))
            
            # Handle categories - validator requires at least one category
            # Database column is 'categories' (plural)
            categories = getattr(product_orm, 'categories', None)
            if not categories or (isinstance(categories, list) and len(categories) == 0):
                # Default to "Uncategorized" if no category exists
                categories = ["Uncategorized"]
            elif not isinstance(categories, list):
                categories = [str(categories)] if categories else ["Uncategorized"]
            
            # Ensure name, description, and image_file are not None/empty
            name = product_orm.name or ""
            description = product_orm.description or ""
            image_file = product_orm.image_file or ""
            
            return Product(
                id=product_id,
                name=name,
                sku=SKU(value=sku_value),
                category=categories,  # Domain model uses 'category' (singular)
                description=description,
                image_file=image_file,
                price=price,
            )
        except Exception as e:
            logger.error(f"Failed to convert ProductORM to Product: {e}", exc_info=True)
            logger.error(f"ProductORM data: id={product_orm.id}, name={product_orm.name}, "
                        f"categories={getattr(product_orm, 'categories', None)}, "
                        f"price_amount={getattr(product_orm, 'price_amount', None)}, "
                        f"price_currency={getattr(product_orm, 'price_currency', None)}")
            raise ValueError(f"Failed to convert ProductORM to Product: {e}") from e

    async def get_by_id(self, product_id: UUID) -> Product | None:
        """Get a product by ID."""
        product_id_str = str(product_id)

        result = await self.session.execute(
            select(ProductORM).where(ProductORM.id == product_id_str)
        )
        orm_product = result.scalar_one_or_none()

        if orm_product is None:
            return None

        # Convert ORM model to Domain entity using custom mapper
        return self._orm_to_domain(orm_product)

    async def get_all(self, page: int = 1, page_size: int = 10) -> tuple[list[Product], int]:
        """Get all products with pagination."""
        # Get total count
        count_result = await self.session.execute(select(ProductORM))
        total_count = len(count_result.scalars().all())

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(ProductORM)
            .offset(offset)
            .limit(page_size)
            .order_by(ProductORM.created_at.desc())
        )
        orm_products = result.scalars().all()

        # Convert to domain entities using custom mapper
        products = [self._orm_to_domain(orm_product) for orm_product in orm_products]
        return products, total_count

    async def get_by_category(self, category: str, page: int = 1, page_size: int = 10) -> tuple[list[Product], int]:
        """Get products by category with pagination."""
        # Get total count for category
        count_result = await self.session.execute(
            select(ProductORM).where(ProductORM.categories.contains([category]))
        )
        total_count = len(count_result.scalars().all())

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(ProductORM)
            .where(ProductORM.categories.contains([category]))
            .offset(offset)
            .limit(page_size)
            .order_by(ProductORM.created_at.desc())
        )
        orm_products = result.scalars().all()

        # Convert to domain entities using custom mapper
        products = [self._orm_to_domain(orm_product) for orm_product in orm_products]
        return products, total_count

    async def search(self, search_term: str, page: int = 1, page_size: int = 10) -> tuple[list[Product], int]:
        """Search products by name or description with pagination."""
        search_pattern = f"%{search_term}%"
        
        # Get total count for search
        count_result = await self.session.execute(
            select(ProductORM).where(
                (ProductORM.name.ilike(search_pattern)) |
                (ProductORM.description.ilike(search_pattern))
            )
        )
        total_count = len(count_result.scalars().all())

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(ProductORM)
            .where(
                (ProductORM.name.ilike(search_pattern)) |
                (ProductORM.description.ilike(search_pattern))
            )
            .offset(offset)
            .limit(page_size)
            .order_by(ProductORM.created_at.desc())
        )
        orm_products = result.scalars().all()

        # Convert to domain entities using custom mapper
        products = [self._orm_to_domain(orm_product) for orm_product in orm_products]
        return products, total_count

    def _domain_to_orm(self, product: Product) -> ProductORM:
        """
        Convert domain model to ORM model.
        
        Args:
            product: Product domain model
            
        Returns:
            Product ORM model
        """
        # SQLAlchemy UUID column can accept UUID objects directly
        from datetime import datetime
        
        now = datetime.utcnow()
        return ProductORM(
            id=product.id,  # UUID object works with UUID column type
            name=product.name,
            sku=str(product.sku),  # SKU from domain model
            categories=product.category,  # Domain model uses 'category', ORM uses 'categories'
            description=product.description,
            image_file=product.image_file,
            price_amount=str(product.price.amount),  # Extract amount from Money object as string
            price_currency=product.price.currency,  # Extract currency from Money object
            version=1,  # Default version
            created_at=now,
            updated_at=now,
            is_deleted=False,
        )

    async def add(self, product: Product) -> Product:
        """Add a new product."""
        # Convert Domain entity to ORM model using custom mapper
        orm_product = self._domain_to_orm(product)

        self.session.add(orm_product)
        await self.session.flush()  # Flush to get any DB-generated values

        # Convert back to domain entity (in case DB modified anything)
        return self._orm_to_domain(orm_product)

    async def update(self, product: Product) -> Product:
        """Update an existing product."""
        product_id_str = str(product.id)

        # Get existing ORM model
        result = await self.session.execute(
            select(ProductORM).where(ProductORM.id == product_id_str)
        )
        existing_orm_product = result.scalar_one()

        # Update ORM model from Domain entity
        from datetime import datetime
        
        existing_orm_product.name = product.name
        existing_orm_product.sku = str(product.sku)
        existing_orm_product.categories = product.category  # Domain model uses 'category', ORM uses 'categories'
        existing_orm_product.description = product.description
        existing_orm_product.image_file = product.image_file
        existing_orm_product.price_amount = str(product.price.amount)  # Extract amount from Money object as string
        existing_orm_product.price_currency = product.price.currency  # Extract currency from Money object
        existing_orm_product.version = getattr(existing_orm_product, 'version', 1) + 1  # Increment version
        existing_orm_product.updated_at = datetime.utcnow()  # Update timestamp

        await self.session.flush()

        # Convert back to domain entity
        return self._orm_to_domain(existing_orm_product)

    async def delete(self, product_id: UUID) -> bool:
        """Delete a product."""
        product_id_str = str(product_id)

        result = await self.session.execute(
            delete(ProductORM).where(ProductORM.id == product_id_str)
        )

        return result.rowcount > 0

    async def exists(self, product_id: UUID) -> bool:
        """Check if a product exists."""
        product_id_str = str(product_id)
        
        result = await self.session.execute(
            select(ProductORM.id).where(ProductORM.id == product_id_str)
        )
        
        return result.scalar_one_or_none() is not None

"""Product repository implementation for database operations."""

from uuid import UUID
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.mapping.orm_mapper import ORMMapper
from app.modules.catalog.domain.product.models.product import Product
from app.modules.catalog.infrastructure.orm_models import ProductORM


class ProductRepository:
    """Repository for Product entities with real database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: UUID) -> Product | None:
        """Get a product by ID."""
        product_id_str = str(product_id)

        result = await self.session.execute(
            select(ProductORM).where(ProductORM.id == product_id_str)
        )
        orm_product = result.scalar_one_or_none()

        if orm_product is None:
            return None

        # Convert ORM model to Domain entity using ORMMapper
        return ORMMapper.from_orm(orm_product, Product)

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

        # Convert to domain entities
        products = ORMMapper.from_orm_list(list(orm_products), Product)
        return products, total_count

    async def get_by_category(self, category: str, page: int = 1, page_size: int = 10) -> tuple[list[Product], int]:
        """Get products by category with pagination."""
        # Get total count for category
        # Note: Database column is 'categories' (plural), not 'category'
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

        # Convert to domain entities
        products = ORMMapper.from_orm_list(list(orm_products), Product)
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

        # Convert to domain entities
        products = ORMMapper.from_orm_list(list(orm_products), Product)
        return products, total_count

    async def add(self, product: Product) -> Product:
        """Add a new product."""
        # Convert Domain entity to ORM model using ORMMapper
        orm_product = ORMMapper.to_orm(product, ProductORM)

        self.session.add(orm_product)
        await self.session.flush()  # Flush to get any DB-generated values

        # Convert back to domain entity (in case DB modified anything)
        return ORMMapper.from_orm(orm_product, Product)

    async def update(self, product: Product) -> Product:
        """Update an existing product."""
        product_id_str = str(product.id)

        # Get existing ORM model
        result = await self.session.execute(
            select(ProductORM).where(ProductORM.id == product_id_str)
        )
        existing_orm_product = result.scalar_one()

        # Update ORM model from Domain entity using ORMMapper
        updated_orm_product = ORMMapper.update_orm_from_domain(existing_orm_product, product)

        await self.session.flush()

        # Convert back to domain entity
        return ORMMapper.from_orm(updated_orm_product, Product)

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

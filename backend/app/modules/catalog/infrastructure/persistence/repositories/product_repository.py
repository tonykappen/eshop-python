"""Product repository implementation."""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.catalog.domain.product.models.product import Product
from app.modules.catalog.domain.product.repository import ProductRepository
from app.modules.catalog.domain.value_objects import Money, SKU
from app.modules.catalog.infrastructure.persistence.models.product_orm import ProductORM

logger = logging.getLogger(__name__)


class ProductRepositoryImpl(ProductRepository):
    """Product repository implementation."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.
        
        Args:
            session: Database session
        """
        self.session = session

    async def get_by_id(self, product_id: UUID) -> Optional[Product]:
        """
        Get product by ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product if found, None otherwise
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.id == product_id,
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            product_orm = result.scalar_one_or_none()
            
            if product_orm:
                return self._orm_to_domain(product_orm)
            return None

        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {e}")
            raise

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Get product by SKU.
        
        Args:
            sku: Product SKU
            
        Returns:
            Product if found, None otherwise
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.sku == sku,
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            product_orm = result.scalar_one_or_none()
            
            if product_orm:
                return self._orm_to_domain(product_orm)
            return None
            
        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            raise

    async def get_by_name(self, name: str) -> Optional[Product]:
        """
        Get product by name.
        
        Args:
            name: Product name
            
        Returns:
            Product if found, None otherwise
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.name == name,
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            product_orm = result.scalar_one_or_none()
            
            if product_orm:
                return self._orm_to_domain(product_orm)
            return None
            
        except Exception as e:
            logger.error(f"Error getting product by name {name}: {e}")
            raise

    async def get_by_category(self, category: str) -> List[Product]:
        """
        Get products by category.
        
        Args:
            category: Category name
            
        Returns:
            List of products in the category
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.categories.contains([category]),
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()
            
            return [self._orm_to_domain(product_orm) for product_orm in products_orm]
            
        except Exception as e:
            logger.error(f"Error getting products by category {category}: {e}")
            raise

    async def search_by_name(self, search_term: str) -> List[Product]:
        """
        Search products by name.
        
        Args:
            search_term: Search term
            
        Returns:
            List of products matching the search term
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.name.ilike(f"%{search_term}%"),
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()
            
            return [self._orm_to_domain(product_orm) for product_orm in products_orm]
            
        except Exception as e:
            logger.error(f"Error searching products by name {search_term}: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Product]:
        """
        Get all products with pagination.
        
        Args:
            skip: Number of products to skip
            limit: Maximum number of products to return
            
        Returns:
            List of products
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.is_deleted == False
            ).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()
            
            return [self._orm_to_domain(product_orm) for product_orm in products_orm]
            
        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            raise

    async def count(self) -> int:
        """
        Get total count of products.
        
        Returns:
            Total number of products
        """
        try:
            from sqlalchemy import func
            stmt = select(func.count(ProductORM.id)).where(
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error counting products: {e}")
            raise

    async def exists_by_sku(self, sku: str) -> bool:
        """
        Check if product exists by SKU.
        
        Args:
            sku: Product SKU
            
        Returns:
            True if product exists, False otherwise
        """
        try:
            stmt = select(ProductORM.id).where(
                ProductORM.sku == sku,
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking product existence by SKU {sku}: {e}")
            raise

    async def exists_by_name(self, name: str) -> bool:
        """
        Check if product exists by name.
        
        Args:
            name: Product name
            
        Returns:
            True if product exists, False otherwise
        """
        try:
            stmt = select(ProductORM.id).where(
                ProductORM.name == name,
                ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None
            
        except Exception as e:
            logger.error(f"Error checking product existence by name {name}: {e}")
            raise

    async def add(self, product: Product) -> None:
        """
        Add a new product.
        
        Args:
            product: Product to add
        """
        try:
            product_orm = self._domain_to_orm(product)
            self.session.add(product_orm)
            await self.session.flush()

        except Exception as e:
            logger.error(f"Error adding product: {e}")
            raise

    async def update(self, product: Product) -> None:
        """
        Update an existing product.
        
        Args:
            product: Product to update
        """
        try:
            stmt = update(ProductORM).where(
                ProductORM.id == product.id
            ).values(
                name=product.name,
                sku=str(product.sku),
                description=product.description,
                image_file=product.image_file,
                price_amount=str(product.price.amount),
                price_currency=product.price.currency,
                categories=product.category,
                version=product.version,
            )
            await self.session.execute(stmt)
            
        except Exception as e:
            logger.error(f"Error updating product: {e}")
            raise

    async def delete(self, product_id: UUID) -> None:
        """
        Delete a product (soft delete).
        
        Args:
            product_id: Product ID to delete
        """
        try:
            stmt = update(ProductORM).where(
                ProductORM.id == product_id
            ).values(
                is_deleted=True
            )
            await self.session.execute(stmt)
            
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            raise

    def _orm_to_domain(self, product_orm: ProductORM) -> Product:
        """
        Convert ORM model to domain model.
        
        Args:
            product_orm: Product ORM model
            
        Returns:
            Product domain model
        """
        from decimal import Decimal
        
        return Product(
            id=product_orm.id,
            name=product_orm.name,
            sku=SKU(value=product_orm.sku),
            category=product_orm.categories,
            description=product_orm.description,
            image_file=product_orm.image_file,
            price=Money(
                amount=Decimal(product_orm.price_amount),
                currency=product_orm.price_currency
            ),
            version=product_orm.version,
        )

    def _domain_to_orm(self, product: Product) -> ProductORM:
        """
        Convert domain model to ORM model.
        
        Args:
            product: Product domain model
            
        Returns:
            Product ORM model
        """
        return ProductORM(
            id=product.id,
            name=product.name,
            sku=str(product.sku),
            description=product.description,
            image_file=product.image_file,
            price_amount=str(product.price.amount),
            price_currency=product.price.currency,
            categories=product.category,
            version=product.version,
        )
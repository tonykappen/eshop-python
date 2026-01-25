"""SQL implementation of IProductRepository."""

import logging
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.repositories.product.product_repository import (
    ProductRepository,
)
from app.modules.catalog.domain.value_objects import SKU, Money
from app.modules.catalog.infrastructure.persistence.orm.product_orm import ProductORM

logger = logging.getLogger(__name__)


class SqlProductRepository(ProductRepository):
    """SQL implementation of IProductRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Database session
        """
        self.session = session

    async def get_by_id(self, product_id: UUID) -> Product | None:
        """
        Get product by ID (non-deleted only).

        Args:
            product_id: Product ID

        Returns:
            Product if found, None otherwise
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.id == product_id, ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            product_orm = result.scalar_one_or_none()

            if product_orm:
                return self._orm_to_domain(product_orm)
            return None

        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {e}")
            raise

    async def get_deleted_by_id(self, product_id: UUID) -> Product | None:
        """
        Get deleted product by ID (for restore operations).

        Args:
            product_id: Product ID

        Returns:
            Product if found and deleted, None otherwise
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.id == product_id, ProductORM.is_deleted == True
            )
            result = await self.session.execute(stmt)
            product_orm = result.scalar_one_or_none()

            if product_orm:
                return self._orm_to_domain(product_orm)
            return None

        except Exception as e:
            logger.error(f"Error getting deleted product by ID {product_id}: {e}")
            raise

    async def get_by_sku(self, sku: str) -> Product | None:
        """
        Get product by SKU.

        Args:
            sku: Product SKU

        Returns:
            Product if found, None otherwise
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.sku == sku, ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            product_orm = result.scalar_one_or_none()

            if product_orm:
                return self._orm_to_domain(product_orm)
            return None

        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            raise

    async def get_by_name(self, name: str) -> Product | None:
        """
        Get product by name.

        Args:
            name: Product name

        Returns:
            Product if found, None otherwise
        """
        try:
            stmt = select(ProductORM).where(
                ProductORM.name == name, ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            product_orm = result.scalar_one_or_none()

            if product_orm:
                return self._orm_to_domain(product_orm)
            return None

        except Exception as e:
            logger.error(f"Error getting product by name {name}: {e}")
            raise

    async def get_by_category(
        self, category: str, page: int = 1, page_size: int = 10
    ) -> list[Product] | tuple[list[Product], int]:
        """
        Get products by category with optional pagination.

        Args:
            category: Category name
            page: Optional page number (1-indexed). If provided, returns tuple with count
            page_size: Optional items per page. If provided, returns tuple with count

        Returns:
            List of products, or tuple of (products, total_count) if pagination params provided
        """
        try:
            # If pagination params provided, use paginated version
            if page != 1 or page_size != 10:
                from sqlalchemy import func

                # Get total count
                count_stmt = select(func.count(ProductORM.id)).where(
                    ProductORM.categories.contains([category]),
                    ProductORM.is_deleted == False,
                )
                count_result = await self.session.execute(count_stmt)
                total_count = count_result.scalar() or 0

                # Get paginated results
                offset = (page - 1) * page_size
                stmt = (
                    select(ProductORM)
                    .where(
                        ProductORM.categories.contains([category]),
                        ProductORM.is_deleted == False,
                    )
                    .offset(offset)
                    .limit(page_size)
                    .order_by(ProductORM.created_at.desc())
                )

                result = await self.session.execute(stmt)
                products_orm = result.scalars().all()

                products = [
                    self._orm_to_domain(product_orm) for product_orm in products_orm
                ]
                return products, total_count

            # Non-paginated version (matches abstract interface)
            stmt = select(ProductORM).where(
                ProductORM.categories.contains([category]),
                ProductORM.is_deleted == False,
            )
            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()

            return [self._orm_to_domain(product_orm) for product_orm in products_orm]

        except Exception as e:
            logger.error(f"Error getting products by category {category}: {e}")
            raise

    async def search_by_name(self, search_term: str) -> list[Product]:
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
                ProductORM.is_deleted == False,
            )
            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()

            return [self._orm_to_domain(product_orm) for product_orm in products_orm]

        except Exception as e:
            logger.error(f"Error searching products by name {search_term}: {e}")
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Product]:
        """
        Get all products with pagination.

        Args:
            skip: Number of products to skip
            limit: Maximum number of products to return

        Returns:
            List of products
        """
        try:
            stmt = (
                select(ProductORM)
                .where(ProductORM.is_deleted == False)
                .offset(skip)
                .limit(limit)
            )
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
                ProductORM.sku == sku, ProductORM.is_deleted == False
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
                ProductORM.name == name, ProductORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(f"Error checking product existence by name {name}: {e}")
            raise

    async def delete(
        self,
        product_id: UUID,
        deleted_by: UUID | None = None,
        deletion_reason: str | None = None,
    ) -> bool:
        """
        Delete a product (soft delete) with audit trail.

        Args:
            product_id: Product ID to delete
            deleted_by: User ID who is deleting the product (optional)
            deletion_reason: Reason for deletion (optional)

        Returns:
            True if product was deleted, False otherwise
        """
        try:
            from datetime import datetime

            stmt = (
                update(ProductORM)
                .where(ProductORM.id == product_id, ProductORM.is_deleted == False)
                .values(
                    is_deleted=True,
                    deleted_at=datetime.utcnow(),
                    deleted_by=deleted_by,
                    deletion_reason=deletion_reason,
                )
            )
            result = await self.session.execute(stmt)
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            raise

    async def add(self, product: Product) -> Product:
        """
        Add a new product and return it.

        Args:
            product: Product to add

        Returns:
            The added product
        """
        try:
            product_orm = self._domain_to_orm(product)
            self.session.add(product_orm)
            await self.session.flush()

            # Return the domain model
            return self._orm_to_domain(product_orm)

        except Exception as e:
            logger.error(f"Error adding product: {e}")
            raise

    async def update(self, product: Product) -> Product:
        """
        Update an existing product and return it.

        Args:
            product: Product to update

        Returns:
            The updated product
        """
        try:
            stmt = (
                update(ProductORM)
                .where(ProductORM.id == product.id)
                .values(
                    name=product.name,
                    sku=str(product.sku),
                    description=product.description,
                    image_file=product.image_file,
                    price_amount=str(product.price.amount),
                    price_currency=product.price.currency,
                    categories=product.category,
                    version=product.version,
                )
            )
            await self.session.execute(stmt)
            await self.session.flush()

            # Fetch and return the updated product
            return await self.get_by_id(product.id)

        except Exception as e:
            logger.error(f"Error updating product: {e}")
            raise

    async def exists(self, product_id: UUID) -> bool:
        """
        Check if a product exists.

        Args:
            product_id: Product ID to check

        Returns:
            True if product exists, False otherwise
        """
        product = await self.get_by_id(product_id)
        return product is not None

    async def search(
        self, search_term: str, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """
        Search products by name or description with pagination.

        Args:
            search_term: Search term
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (products, total_count)
        """
        try:
            from sqlalchemy import func, or_

            # Get total count
            count_stmt = select(func.count(ProductORM.id)).where(
                or_(
                    ProductORM.name.ilike(f"%{search_term}%"),
                    ProductORM.description.ilike(f"%{search_term}%"),
                ),
                ProductORM.is_deleted == False,
            )
            count_result = await self.session.execute(count_stmt)
            total_count = count_result.scalar() or 0

            # Get paginated results
            offset = (page - 1) * page_size
            stmt = (
                select(ProductORM)
                .where(
                    or_(
                        ProductORM.name.ilike(f"%{search_term}%"),
                        ProductORM.description.ilike(f"%{search_term}%"),
                    ),
                    ProductORM.is_deleted == False,
                )
                .offset(offset)
                .limit(page_size)
                .order_by(ProductORM.created_at.desc())
            )

            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()

            products = [
                self._orm_to_domain(product_orm) for product_orm in products_orm
            ]
            return products, total_count

        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise

    async def get_all(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """
        Get all products with pagination.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (products, total_count)
        """
        try:
            from sqlalchemy import func

            logger.debug(
                f"SqlProductRepository.get_all: page={page}, page_size={page_size}"
            )

            # Get total count
            count_stmt = select(func.count(ProductORM.id)).where(
                ProductORM.is_deleted == False
            )
            count_result = await self.session.execute(count_stmt)
            total_count = count_result.scalar() or 0
            logger.debug(f"SqlProductRepository.get_all: total_count={total_count}")

            # Get paginated results
            offset = (page - 1) * page_size
            stmt = (
                select(ProductORM)
                .where(ProductORM.is_deleted == False)
                .offset(offset)
                .limit(page_size)
                .order_by(ProductORM.created_at.desc())
            )

            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()
            logger.debug(
                f"SqlProductRepository.get_all: found {len(products_orm)} ORM products"
            )

            products = []
            for product_orm in products_orm:
                try:
                    product = self._orm_to_domain(product_orm)
                    products.append(product)
                except Exception as e:
                    logger.error(
                        f"Error converting ORM to domain for product {product_orm.id}: {e}",
                        exc_info=True,
                    )
                    raise

            logger.debug(
                f"SqlProductRepository.get_all: converted {len(products)} domain products"
            )
            return products, total_count

        except Exception as e:
            logger.error(f"Error getting all products: {e}", exc_info=True)
            raise

    async def get_deleted_products(
        self, page: int = 1, page_size: int = 10
    ) -> tuple[list[Product], int]:
        """
        Get deleted products with pagination (admin only).

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (products, total_count)
        """
        try:
            from sqlalchemy import func

            # Get total count
            count_stmt = select(func.count(ProductORM.id)).where(
                ProductORM.is_deleted == True
            )
            count_result = await self.session.execute(count_stmt)
            total_count = count_result.scalar() or 0

            # Get paginated results
            # Order by deleted_at (nulls last) and then by updated_at as fallback
            from sqlalchemy import nullslast

            offset = (page - 1) * page_size
            stmt = (
                select(ProductORM)
                .where(ProductORM.is_deleted == True)
                .offset(offset)
                .limit(page_size)
                .order_by(
                    nullslast(ProductORM.deleted_at.desc()),
                    ProductORM.updated_at.desc(),
                )
            )

            result = await self.session.execute(stmt)
            products_orm = result.scalars().all()

            products = [
                self._orm_to_domain(product_orm) for product_orm in products_orm
            ]
            return products, total_count

        except Exception as e:
            logger.error(f"Error getting deleted products: {e}")
            raise

    async def restore_product(
        self, product_id: UUID, restored_by: UUID | None = None
    ) -> bool:
        """
        Restore a deleted product.

        Args:
            product_id: Product ID to restore
            restored_by: User ID who is restoring the product (optional)

        Returns:
            True if product was restored, False otherwise
        """
        try:
            stmt = (
                update(ProductORM)
                .where(ProductORM.id == product_id, ProductORM.is_deleted == True)
                .values(
                    is_deleted=False,
                    deleted_at=None,
                    deleted_by=None,
                    deletion_reason=None,
                    updated_by=restored_by,
                )
            )
            result = await self.session.execute(stmt)
            return result.rowcount > 0

        except Exception as e:
            logger.error(f"Error restoring product: {e}")
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
                currency=product_orm.price_currency,
            ),
            version=product_orm.version,
            created_at=product_orm.created_at,
            last_modified=product_orm.updated_at,  # Entity uses last_modified, not updated_at
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

"""SQL implementation of ICategoryRepository."""

from uuid import UUID

from app.core.logging.base_logger import BaseLogger
from app.modules.catalog.domain.category.repository import CategoryRepository
from app.modules.catalog.domain.entities.category import Category
from app.modules.catalog.infrastructure.persistence.orm.category_orm import \
    CategoryORM
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = BaseLogger(__name__)


class SqlCategoryRepository(CategoryRepository):
    """SQL implementation of ICategoryRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize the repository.

        Args:
            session: Database session
        """
        self.session = session

    async def get_by_id(self, category_id: UUID) -> Category | None:
        """
        Get category by ID.

        Args:
            category_id: Category ID

        Returns:
            Category if found, None otherwise
        """
        try:
            stmt = select(CategoryORM).where(
                CategoryORM.id == category_id, CategoryORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            category_orm = result.scalar_one_or_none()

            if category_orm:
                return self._orm_to_domain(category_orm)
            return None

        except Exception as e:
            logger.log_error_with_context(
                "Error getting category by ID",
                error=e,
                context={"category_id": str(category_id)},
            )
            raise

    async def get_by_name(self, name: str) -> Category | None:
        """
        Get category by name.

        Args:
            name: Category name

        Returns:
            Category if found, None otherwise
        """
        try:
            stmt = select(CategoryORM).where(
                CategoryORM.name == name, CategoryORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            category_orm = result.scalar_one_or_none()

            if category_orm:
                return self._orm_to_domain(category_orm)
            return None

        except Exception as e:
            logger.log_error_with_context(
                "Error getting category by name", error=e, context={"name": name}
            )
            raise

    async def get_by_parent_id(self, parent_id: UUID) -> list[Category]:
        """
        Get categories by parent ID.

        Args:
            parent_id: Parent category ID

        Returns:
            List of categories with the parent ID
        """
        try:
            stmt = select(CategoryORM).where(
                CategoryORM.parent_id == parent_id, CategoryORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            categories_orm = result.scalars().all()

            return [
                self._orm_to_domain(category_orm) for category_orm in categories_orm
            ]

        except Exception as e:
            logger.log_error_with_context(
                "Error getting categories by parent ID",
                error=e,
                context={"parent_id": str(parent_id)},
            )
            raise

    async def get_active_categories(self) -> list[Category]:
        """
        Get all active categories.

        Returns:
            List of active categories
        """
        try:
            stmt = select(CategoryORM).where(
                CategoryORM.is_active == True, CategoryORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            categories_orm = result.scalars().all()

            return [
                self._orm_to_domain(category_orm) for category_orm in categories_orm
            ]

        except Exception as e:
            logger.log_error_with_context("Error getting active categories", error=e)
            raise

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Category]:
        """
        Get all categories with pagination.

        Args:
            skip: Number of categories to skip
            limit: Maximum number of categories to return

        Returns:
            List of categories
        """
        try:
            stmt = (
                select(CategoryORM)
                .where(CategoryORM.is_deleted == False)
                .offset(skip)
                .limit(limit)
            )
            result = await self.session.execute(stmt)
            categories_orm = result.scalars().all()

            return [
                self._orm_to_domain(category_orm) for category_orm in categories_orm
            ]

        except Exception as e:
            logger.log_error_with_context("Error getting all categories", error=e)
            raise

    async def count(self) -> int:
        """
        Get total count of categories.

        Returns:
            Total number of categories
        """
        try:
            from sqlalchemy import func

            stmt = select(func.count(CategoryORM.id)).where(
                CategoryORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar() or 0

        except Exception as e:
            logger.log_error_with_context("Error counting categories", error=e)
            raise

    async def exists_by_name(self, name: str) -> bool:
        """
        Check if category exists by name.

        Args:
            name: Category name

        Returns:
            True if category exists, False otherwise
        """
        try:
            stmt = select(CategoryORM.id).where(
                CategoryORM.name == name, CategoryORM.is_deleted == False
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.log_error_with_context(
                "Error checking category existence by name",
                error=e,
                context={"name": name},
            )
            raise

    async def add(self, category: Category) -> None:
        """
        Add a new category.

        Args:
            category: Category to add
        """
        try:
            category_orm = self._domain_to_orm(category)
            self.session.add(category_orm)
            await self.session.flush()

        except Exception as e:
            logger.log_error_with_context("Error adding category", error=e)
            raise

    async def update(self, category: Category) -> None:
        """
        Update an existing category.

        Args:
            category: Category to update
        """
        try:
            stmt = (
                update(CategoryORM)
                .where(CategoryORM.id == category.id)
                .values(
                    name=category.name,
                    description=category.description,
                    parent_id=category.parent_id,
                    is_active=category.is_active,
                    version=category.version,
                )
            )
            await self.session.execute(stmt)

        except Exception as e:
            logger.log_error_with_context("Error updating category", error=e)
            raise

    async def delete(self, category_id: UUID) -> None:
        """
        Delete a category (soft delete).

        Args:
            category_id: Category ID to delete
        """
        try:
            stmt = (
                update(CategoryORM)
                .where(CategoryORM.id == category_id)
                .values(is_deleted=True)
            )
            await self.session.execute(stmt)

        except Exception as e:
            logger.log_error_with_context(
                "Error deleting category",
                error=e,
                context={"category_id": str(category_id)},
            )
            raise

    def _orm_to_domain(self, category_orm: CategoryORM) -> Category:
        """
        Convert ORM model to domain model.

        Args:
            category_orm: Category ORM model

        Returns:
            Category domain model
        """
        return Category(
            id=category_orm.id,
            name=category_orm.name,
            description=category_orm.description,
            parent_id=category_orm.parent_id,
            is_active=category_orm.is_active,
            version=category_orm.version,
        )

    def _domain_to_orm(self, category: Category) -> CategoryORM:
        """
        Convert domain model to ORM model.

        Args:
            category: Category domain model

        Returns:
            Category ORM model
        """
        return CategoryORM(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            is_active=category.is_active,
            version=category.version,
        )

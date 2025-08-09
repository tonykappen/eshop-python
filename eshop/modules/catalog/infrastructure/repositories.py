"""Repository implementations for the Catalog module demonstrating ORM mapping."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eshop.core.mapping.orm_mapper import ORMMapper
from eshop.modules.catalog.domain.entities import (
    CatalogBrand,
    CatalogCategory,
    CatalogItem,
)
from eshop.modules.catalog.infrastructure.orm_models import (
    CatalogBrandORM,
    CatalogCategoryORM,
    CatalogItemORM,
)


class CatalogItemRepository:
    """Repository for CatalogItem entities demonstrating three-tier mapping."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, item_id: UUID) -> CatalogItem | None:
        """Get a catalog item by ID."""
        # Convert UUID to string for ORM query
        item_id_str = str(item_id)

        # Query ORM model
        result = await self.session.execute(
            select(CatalogItemORM)
            .options(
                selectinload(CatalogItemORM.category),
                selectinload(CatalogItemORM.brand),
            )
            .where(CatalogItemORM.id == item_id_str)
        )
        orm_item = result.scalar_one_or_none()

        if orm_item is None:
            return None

        # Convert ORM model to Domain entity using ORMMapper
        return ORMMapper.from_orm(orm_item, CatalogItem)

    async def get_all(self) -> list[CatalogItem]:
        """Get all catalog items."""
        result = await self.session.execute(
            select(CatalogItemORM).options(
                selectinload(CatalogItemORM.category),
                selectinload(CatalogItemORM.brand),
            )
        )
        orm_items = result.scalars().all()

        # Convert list of ORM models to Domain entities
        return ORMMapper.from_orm_list(list(orm_items), CatalogItem)

    async def get_by_category(self, category_id: UUID) -> list[CatalogItem]:
        """Get catalog items by category."""
        category_id_str = str(category_id)

        result = await self.session.execute(
            select(CatalogItemORM)
            .options(
                selectinload(CatalogItemORM.category),
                selectinload(CatalogItemORM.brand),
            )
            .where(CatalogItemORM.category_id == category_id_str)
        )
        orm_items = result.scalars().all()

        return ORMMapper.from_orm_list(list(orm_items), CatalogItem)

    async def add(self, item: CatalogItem) -> CatalogItem:
        """Add a new catalog item."""
        # Convert Domain entity to ORM model using ORMMapper
        orm_item = ORMMapper.to_orm(item, CatalogItemORM)

        self.session.add(orm_item)
        await self.session.flush()  # Flush to get any DB-generated values

        # Convert back to domain entity (in case DB modified anything)
        return ORMMapper.from_orm(orm_item, CatalogItem)

    async def update(self, item: CatalogItem) -> CatalogItem:
        """Update an existing catalog item."""
        item_id_str = str(item.id)

        # Get existing ORM model
        result = await self.session.execute(
            select(CatalogItemORM).where(CatalogItemORM.id == item_id_str)
        )
        existing_orm_item = result.scalar_one()

        # Update ORM model from Domain entity using ORMMapper
        updated_orm_item = ORMMapper.update_orm_from_domain(existing_orm_item, item)

        await self.session.flush()

        # Convert back to domain entity
        return ORMMapper.from_orm(updated_orm_item, CatalogItem)

    async def delete(self, item_id: UUID) -> bool:
        """Delete a catalog item."""
        item_id_str = str(item_id)

        result = await self.session.execute(
            delete(CatalogItemORM).where(CatalogItemORM.id == item_id_str)
        )

        return result.rowcount > 0


class CatalogCategoryRepository:
    """Repository for CatalogCategory entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, category_id: UUID) -> CatalogCategory | None:
        """Get a catalog category by ID."""
        category_id_str = str(category_id)

        result = await self.session.execute(
            select(CatalogCategoryORM).where(CatalogCategoryORM.id == category_id_str)
        )
        orm_category = result.scalar_one_or_none()

        if orm_category is None:
            return None

        return ORMMapper.from_orm(orm_category, CatalogCategory)

    async def get_all(self) -> list[CatalogCategory]:
        """Get all catalog categories."""
        result = await self.session.execute(select(CatalogCategoryORM))
        orm_categories = result.scalars().all()

        return ORMMapper.from_orm_list(list(orm_categories), CatalogCategory)

    async def add(self, category: CatalogCategory) -> CatalogCategory:
        """Add a new catalog category."""
        orm_category = ORMMapper.to_orm(category, CatalogCategoryORM)

        self.session.add(orm_category)
        await self.session.flush()

        return ORMMapper.from_orm(orm_category, CatalogCategory)

    async def update(self, category: CatalogCategory) -> CatalogCategory:
        """Update an existing catalog category."""
        category_id_str = str(category.id)

        result = await self.session.execute(
            select(CatalogCategoryORM).where(CatalogCategoryORM.id == category_id_str)
        )
        existing_orm_category = result.scalar_one()

        updated_orm_category = ORMMapper.update_orm_from_domain(
            existing_orm_category, category
        )
        await self.session.flush()

        return ORMMapper.from_orm(updated_orm_category, CatalogCategory)

    async def delete(self, category_id: UUID) -> bool:
        """Delete a catalog category."""
        category_id_str = str(category_id)

        result = await self.session.execute(
            delete(CatalogCategoryORM).where(CatalogCategoryORM.id == category_id_str)
        )

        return result.rowcount > 0


class CatalogBrandRepository:
    """Repository for CatalogBrand entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, brand_id: UUID) -> CatalogBrand | None:
        """Get a catalog brand by ID."""
        brand_id_str = str(brand_id)

        result = await self.session.execute(
            select(CatalogBrandORM).where(CatalogBrandORM.id == brand_id_str)
        )
        orm_brand = result.scalar_one_or_none()

        if orm_brand is None:
            return None

        return ORMMapper.from_orm(orm_brand, CatalogBrand)

    async def get_all(self) -> list[CatalogBrand]:
        """Get all catalog brands."""
        result = await self.session.execute(select(CatalogBrandORM))
        orm_brands = result.scalars().all()

        return ORMMapper.from_orm_list(list(orm_brands), CatalogBrand)

    async def add(self, brand: CatalogBrand) -> CatalogBrand:
        """Add a new catalog brand."""
        orm_brand = ORMMapper.to_orm(brand, CatalogBrandORM)

        self.session.add(orm_brand)
        await self.session.flush()

        return ORMMapper.from_orm(orm_brand, CatalogBrand)

    async def update(self, brand: CatalogBrand) -> CatalogBrand:
        """Update an existing catalog brand."""
        brand_id_str = str(brand.id)

        result = await self.session.execute(
            select(CatalogBrandORM).where(CatalogBrandORM.id == brand_id_str)
        )
        existing_orm_brand = result.scalar_one()

        updated_orm_brand = ORMMapper.update_orm_from_domain(existing_orm_brand, brand)
        await self.session.flush()

        return ORMMapper.from_orm(updated_orm_brand, CatalogBrand)

    async def delete(self, brand_id: UUID) -> bool:
        """Delete a catalog brand."""
        brand_id_str = str(brand_id)

        result = await self.session.execute(
            delete(CatalogBrandORM).where(CatalogBrandORM.id == brand_id_str)
        )

        return result.rowcount > 0

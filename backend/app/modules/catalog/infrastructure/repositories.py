"""Repository implementations for the Catalog module demonstrating ORM mapping.

NOTE: This file contains legacy repository implementations for CatalogBrand, CatalogCategory, and CatalogItem
entities that are no longer part of the current domain model. These repositories are kept for reference
and test purposes only. They will cause import errors if the old entities are not available.

To fix import errors, the entire file content is commented out. Uncomment if you need to restore these repositories.
"""

# Legacy repository implementations - commented out to prevent import errors
# These entities (CatalogBrand, CatalogCategory, CatalogItem) no longer exist in the domain model

"""
# Original file content commented out to prevent import errors
# Uncomment and fix imports if you need to restore these repositories

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.mapping.orm_mapper import ORMMapper
from app.modules.catalog.domain.entities import (
    CatalogBrand,
    CatalogCategory,
    CatalogItem,
)
from app.modules.catalog.infrastructure.orm_models import (
    CatalogBrandORM,
    CatalogCategoryORM,
    CatalogItemORM,
)


class CatalogItemRepository:
    # ... (all repository classes commented out)
    pass


class CatalogCategoryRepository:
    # ... (all repository classes commented out)
    pass


class CatalogBrandRepository:
    # ... (all repository classes commented out)
    pass
"""

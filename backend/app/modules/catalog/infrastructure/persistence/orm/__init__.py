"""ORM models for catalog module persistence layer."""

# Export Base for Alembic migrations and model registration
from app.modules.catalog.infrastructure.persistence.orm.base import Base
from app.modules.catalog.infrastructure.persistence.orm.category_orm import CategoryORM
from app.modules.catalog.infrastructure.persistence.orm.inventory_item_orm import (
    InventoryItemORM,
)
from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import OutboxORM

# Export all ORM models for convenient imports
from app.modules.catalog.infrastructure.persistence.orm.product_orm import ProductORM

__all__ = [
    "Base",
    "ProductORM",
    "CategoryORM",
    "InventoryItemORM",
    "OutboxORM",
]

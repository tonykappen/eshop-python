"""Category mapper for domain ↔ DTO ↔ contract conversions."""

from uuid import UUID

from app.modules.catalog.application.dvos.category_dvo import CategoryDVO
from app.modules.catalog.domain.category.models.category import Category


class CategoryMapper:
    """Mapper for Category domain model conversions."""

    @staticmethod
    def domain_to_dvo(category: Category) -> CategoryDVO:
        """
        Convert Category domain model to CategoryDVO.

        Args:
            category: Category domain model

        Returns:
            CategoryDVO
        """
        return CategoryDVO(
            id=category.id,
            name=category.name,
            description=category.description,
            parent_id=category.parent_id,
            is_active=category.is_active,
            version=category.version,
            created_at=category.created_at.isoformat() if category.created_at else "",
            updated_at=category.updated_at.isoformat() if category.updated_at else "",
        )

    @staticmethod
    def dvo_to_domain(dvo: CategoryDVO) -> Category:
        """
        Convert CategoryDVO to Category domain model.

        Args:
            dvo: CategoryDVO

        Returns:
            Category domain model
        """
        return Category(
            id=dvo.id,
            name=dvo.name,
            description=dvo.description,
            parent_id=dvo.parent_id,
            is_active=dvo.is_active,
            version=dvo.version,
        )

    @staticmethod
    def domain_to_dict(category: Category) -> dict:
        """
        Convert Category domain model to dictionary.

        Args:
            category: Category domain model

        Returns:
            Dictionary representation
        """
        return {
            "id": str(category.id),
            "name": category.name,
            "description": category.description,
            "parent_id": str(category.parent_id) if category.parent_id else None,
            "is_active": category.is_active,
            "version": category.version,
            "created_at": (
                category.created_at.isoformat() if category.created_at else None
            ),
            "updated_at": (
                category.updated_at.isoformat() if category.updated_at else None
            ),
        }

    @staticmethod
    def dict_to_domain(data: dict) -> Category:
        """
        Convert dictionary to Category domain model.

        Args:
            data: Dictionary data

        Returns:
            Category domain model
        """
        return Category(
            id=UUID(data["id"]),
            name=data["name"],
            description=data["description"],
            parent_id=UUID(data["parent_id"]) if data.get("parent_id") else None,
            is_active=data.get("is_active", True),
            version=data.get("version", 1),
        )

"""Product mapping rules for Catalog BC."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.mapping.profiles.base_mapping_profile import BaseMappingProfile
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.value_objects import SKU, Money
from app.modules.catalog.infrastructure.persistence.orm.product_orm import ProductORM


class CatalogProductProfile(BaseMappingProfile):
    """
    Mapping profile for Product entity.

    Defines mapping rules between:
    - Product (Domain) ↔ ProductORM (ORM)
    - Product (Domain) ↔ ProductDto (DTO)
    - ProductORM (ORM) ↔ ProductDto (DTO)
    """

    def configure(self) -> None:
        """Configure Product mapping rules."""
        # Configuration is done through method implementations
        pass

    def domain_to_orm(self, product: Product) -> ProductORM:
        """
        Map Product domain entity to ProductORM.

        Args:
            product: Product domain entity

        Returns:
            ProductORM instance
        """
        current_time = datetime.utcnow()

        # Extract SKU value
        sku_value = (
            product.sku.value if hasattr(product.sku, "value") else str(product.sku)
        )

        # Extract price information
        price_amount = (
            str(product.price.amount)
            if hasattr(product.price, "amount")
            else str(product.price)
        )
        price_currency = (
            product.price.currency if hasattr(product.price, "currency") else "USD"
        )

        # Extract categories - Product domain has 'category' (list), ORM has 'categories'
        categories = product.category if hasattr(product, "category") else []

        return ProductORM(
            id=product.id,
            sku=sku_value,
            name=product.name,
            description=product.description,
            price_amount=price_amount,
            price_currency=price_currency,
            categories=categories,
            image_file=product.image_file or "",
            is_active=getattr(product, "is_active", True),
            version=product.version,
            created_at=getattr(product, "created_at", current_time) or current_time,
            updated_at=getattr(product, "updated_at", current_time) or current_time,
            is_deleted=getattr(product, "is_deleted", False),
        )

    def orm_to_domain(self, orm: ProductORM) -> Product:
        """
        Map ProductORM to Product domain entity.

        Args:
            orm: ProductORM instance

        Returns:
            Product domain entity
        """
        # Convert price_amount string to Decimal
        price_amount = (
            Decimal(str(orm.price_amount)) if orm.price_amount else Decimal("0")
        )

        # ORM has 'categories' (list), Product domain has 'category' (list)
        categories = orm.categories if hasattr(orm, "categories") else []

        return Product(
            id=orm.id,
            name=orm.name,
            sku=SKU(value=orm.sku),
            category=categories,
            description=orm.description,
            price=Money(amount=price_amount, currency=orm.price_currency or "USD"),
            image_file=orm.image_file or "",
            version=orm.version,
        )

    def domain_to_dto(self, product: Product) -> ProductDto:
        """
        Map Product domain entity to ProductDto.

        Args:
            product: Product domain entity

        Returns:
            ProductDto instance
        """
        # Extract SKU value
        sku_value = (
            product.sku.value if hasattr(product.sku, "value") else str(product.sku)
        )

        # Extract price information
        price_amount = (
            product.price.amount if hasattr(product.price, "amount") else product.price
        )
        price_currency = (
            product.price.currency if hasattr(product.price, "currency") else "USD"
        )

        # Extract categories
        categories = product.category if hasattr(product, "category") else []

        # Extract timestamps
        created_at = (
            product.created_at.isoformat()
            if hasattr(product, "created_at") and product.created_at
            else ""
        )
        updated_at = (
            product.updated_at.isoformat()
            if hasattr(product, "updated_at") and product.updated_at
            else ""
        )

        return ProductDto(
            id=product.id,
            name=product.name,
            sku=sku_value,
            category=categories,
            description=product.description,
            image_file=product.image_file or None,
            price=float(price_amount),
            currency=price_currency,
            version=product.version,
            created_at=created_at,
            updated_at=updated_at,
        )

    def dto_to_domain(self, dto: ProductDto) -> Product:
        """
        Map ProductDto to Product domain entity.

        Args:
            dto: ProductDto instance

        Returns:
            Product domain entity
        """
        return Product(
            id=dto.id,
            name=dto.name,
            sku=SKU(value=dto.sku),
            category=dto.category,
            description=dto.description,
            price=Money(amount=Decimal(str(dto.price)), currency=dto.currency),
            image_file=dto.image_file or "",
            version=dto.version,
        )

    def orm_to_dto(self, orm: ProductORM) -> ProductDto:
        """
        Map ProductORM to ProductDto.

        Args:
            orm: ProductORM instance

        Returns:
            ProductDto instance
        """
        # ORM has 'categories', DTO has 'category'
        categories = orm.categories if hasattr(orm, "categories") else []

        return ProductDto(
            id=orm.id,
            name=orm.name,
            sku=orm.sku,
            category=categories,
            description=orm.description,
            price=float(orm.price_amount) if orm.price_amount else 0.0,
            currency=orm.price_currency or "USD",
            image_file=orm.image_file or None,
            version=orm.version,
            created_at=orm.created_at.isoformat() if orm.created_at else "",
            updated_at=orm.updated_at.isoformat() if orm.updated_at else "",
        )

    def dto_to_orm(self, dto: ProductDto) -> ProductORM:
        """
        Map ProductDto to ProductORM.

        Args:
            dto: ProductDto instance

        Returns:
            ProductORM instance
        """
        current_time = datetime.utcnow()

        # DTO has 'category', ORM has 'categories'
        categories = dto.category if hasattr(dto, "category") else []

        # Parse timestamps
        created_at = (
            datetime.fromisoformat(dto.created_at) if dto.created_at else current_time
        )
        updated_at = (
            datetime.fromisoformat(dto.updated_at) if dto.updated_at else current_time
        )

        return ProductORM(
            id=dto.id,
            sku=dto.sku,
            name=dto.name,
            description=dto.description,
            price_amount=str(dto.price),
            price_currency=dto.currency,
            categories=categories,
            image_file=dto.image_file or "",
            version=dto.version,
            created_at=created_at,
            updated_at=updated_at,
            is_deleted=False,
        )

    def map(self, source: Any, destination_type: type) -> Any:
        """
        Generic map method that routes to appropriate specific mapper.

        Args:
            source: Source object
            destination_type: Target type

        Returns:
            Mapped object
        """
        source_type = type(source)

        # Domain → ORM
        if source_type == Product and destination_type == ProductORM:
            return self.domain_to_orm(source)

        # ORM → Domain
        if source_type == ProductORM and destination_type == Product:
            return self.orm_to_domain(source)

        # Domain → DTO
        if source_type == Product and destination_type == ProductDto:
            return self.domain_to_dto(source)

        # DTO → Domain
        if source_type == ProductDto and destination_type == Product:
            return self.dto_to_domain(source)

        # ORM → DTO
        if source_type == ProductORM and destination_type == ProductDto:
            return self.orm_to_dto(source)

        # DTO → ORM
        if source_type == ProductDto and destination_type == ProductORM:
            return self.dto_to_orm(source)

        raise NotImplementedError(
            f"Mapping from {source_type.__name__} to {destination_type.__name__} not implemented"
        )

    def can_map(self, source_type: type, destination_type: type) -> bool:
        """
        Check if this profile can map between the given types.

        Args:
            source_type: Source type
            destination_type: Destination type

        Returns:
            True if mapping is supported
        """
        supported_mappings = [
            (Product, ProductORM),
            (ProductORM, Product),
            (Product, ProductDto),
            (ProductDto, Product),
            (ProductORM, ProductDto),
            (ProductDto, ProductORM),
        ]

        return (source_type, destination_type) in supported_mappings

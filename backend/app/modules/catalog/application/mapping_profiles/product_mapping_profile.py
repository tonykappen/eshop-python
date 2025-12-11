"""Product mapper for domain ↔ DTO ↔ contract conversions."""

from decimal import Decimal

from app.modules.catalog.application.dvos.product_dvo import ProductDVO
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.value_objects import Money


class ProductMapper:
    """Mapper for Product domain model conversions."""

    @staticmethod
    def domain_to_dvo(product: Product) -> ProductDVO:
        """
        Convert Product domain model to ProductDVO.
        
        Args:
            product: Product domain model
            
        Returns:
            ProductDVO
        """
        return ProductDVO(
            id=product.id,
            name=product.name,
            sku=str(product.sku),
            category=product.category,
            description=product.description,
            image_file=product.image_file,
            price_amount=product.price.amount,
            price_currency=product.price.currency,
            version=product.version,
            created_at=product.created_at.isoformat() if product.created_at else "",
            updated_at=product.updated_at.isoformat() if product.updated_at else "",
        )

    @staticmethod
    def dvo_to_domain(dvo: ProductDVO) -> Product:
        """
        Convert ProductDVO to Product domain model.
        
        Args:
            dvo: ProductDVO
            
        Returns:
            Product domain model
        """
        return Product(
            id=dvo.id,
            name=dvo.name,
            sku=SKU(value=dvo.sku),
            category=dvo.category,
            description=dvo.description,
            image_file=dvo.image_file,
            price=Money(amount=dvo.price_amount, currency=dvo.price_currency),
            version=dvo.version,
        )

    @staticmethod
    def dvo_to_dto(dvo: ProductDVO) -> ProductDto:
        """
        Convert ProductDVO to ProductDto.
        
        Args:
            dvo: ProductDVO
            
        Returns:
            ProductDto
        """
        return ProductDto(
            id=str(dvo.id),
            name=dvo.name,
            sku=dvo.sku,
            category=dvo.category,
            description=dvo.description,
            image_file=dvo.image_file,
            price=float(dvo.price_amount),
            currency=dvo.price_currency,
            version=dvo.version,
            created_at=dvo.created_at,
            updated_at=dvo.updated_at,
        )

    @staticmethod
    def dto_to_dvo(dto: ProductDto) -> ProductDVO:
        """
        Convert ProductDto to ProductDVO.
        
        Args:
            dto: ProductDto
            
        Returns:
            ProductDVO
        """
        return ProductDVO(
            id=UUID(dto.id),
            name=dto.name,
            sku=dto.sku,
            category=dto.category,
            description=dto.description,
            image_file=dto.image_file,
            price_amount=Decimal(str(dto.price)),
            price_currency=dto.currency,
            version=dto.version,
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )

    @staticmethod
    def domain_to_dto(product: Product) -> ProductDto:
        """
        Convert Product domain model to ProductDto.
        
        Args:
            product: Product domain model
            
        Returns:
            ProductDto
        """
        dvo = ProductMapper.domain_to_dvo(product)
        return ProductMapper.dvo_to_dto(dvo)

    @staticmethod
    def dto_to_domain(dto: ProductDto) -> Product:
        """
        Convert ProductDto to Product domain model.
        
        Args:
            dto: ProductDto
            
        Returns:
            Product domain model
        """
        dvo = ProductMapper.dto_to_dvo(dto)
        return ProductMapper.dvo_to_domain(dvo)



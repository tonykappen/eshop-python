"""CreateProductHandler with 1-1 parity to .NET implementation."""

import asyncio
from typing import Any
from uuid import UUID

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.contracts.products.dtos import ProductDto
from app.modules.catalog.domain.exceptions import (
    ProductCreationError,
    ProductValidationError,
)
from app.modules.catalog.domain.models import Product
from app.modules.catalog.infrastructure.product_repository import ProductRepository
from app.modules.catalog.infrastructure.cache_service import CatalogCacheService, RedisCacheService
from app.modules.catalog.infrastructure.event_publisher import CatalogEventPublisherFactory
from app.core.database.session import AsyncSessionLocal
from app.core.logging.logger import get_logger

from pydantic import BaseModel, Field
from decimal import Decimal

logger = get_logger(__name__)


class CreateProductCommand(BaseModel):
    """Command to create a new product - matches .NET CreateProductCommand."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    picture_url: str = Field(..., description="Product picture URL")
    category: list[str] = Field(..., description="Product categories")


class CreateProductResult(BaseModel):
    """Result of creating a product - matches .NET CreateProductResult."""

    id: UUID = Field(..., description="Created product ID")


class CreateProductCommandValidator:
    """Validator for CreateProductCommand - matches .NET CreateProductCommandValidator."""

    def validate(self, command: CreateProductCommand) -> list[str]:
        """
        Validate the create product command.
        
        Args:
            command: The command to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not command.name or not command.name.strip():
            errors.append("Name is required")
            
        if not command.description or not command.description.strip():
            errors.append("Description is required")
            
        if command.price <= 0:
            errors.append("Price must be greater than 0")
            
        if not command.picture_url or not command.picture_url.strip():
            errors.append("Picture URL is required")
            
        if not command.category:
            errors.append("At least one category is required")
            
        return errors


class CreateProductHandler(IRequestHandler[CreateProductCommand, CreateProductResult]):
    """Handler for CreateProductCommand - matches .NET CreateProductHandler."""

    def __init__(self) -> None:
        """Initialize handler."""
        self.cache_service = CatalogCacheService(RedisCacheService())
        self.event_publisher = CatalogEventPublisherFactory.get_instance()

    async def handle(
        self, command: CreateProductCommand, cancellation_token: CancellationToken
    ) -> CreateProductResult:
        """
        Handle the command - matches .NET Handle(CreateProductCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            CreateProductResult containing the created product ID
        """
        # Validate command first
        validator = CreateProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        product = self._create_new_product(command)

        # Use real database repository
        async with AsyncSessionLocal() as session:
            try:
                repository = ProductRepository(session)
                saved_product = await repository.add(product)
                await session.commit()
                
                # Cache the created product
                await self._cache_product(saved_product)
                
                # Publish integration event
                await self._publish_product_created_event(saved_product)
                
                # Invalidate products list cache
                await self.cache_service.invalidate_products_list()
                
                logger.log_info_with_context(
                    f"Product created successfully: {saved_product.name}",
                    product_id=str(saved_product.id),
                    product_name=saved_product.name,
                )
                
                return CreateProductResult(id=saved_product.id)
            except Exception as e:
                await session.rollback()
                raise ProductCreationError(
                    message="Failed to save product to database", 
                    details=str(e)
                ) from e

    def _create_new_product(self, command: CreateProductCommand) -> Product:
        """
        Create new product from command - matches .NET CreateNewProduct(ProductDto productDto).

        Args:
            command: Create product command

        Returns:
            Created Product entity

        Raises:
            ProductValidationError: If product data is invalid
        """
        from uuid import uuid4

        # Validate product data
        if not command.name or not command.name.strip():
            raise ProductValidationError("Product name is required", field="name")

        if command.price <= 0:
            raise ProductValidationError(
                "Product price must be greater than zero", field="price"
            )

        try:
            product = Product.create(
                product_id=uuid4(),
                name=command.name,
                category=command.category,
                description=command.description,
                image_file=command.picture_url,  # Map picture_url to image_file for domain model
                price=Decimal(str(command.price)),
            )
            return product
        except Exception as e:
            raise ProductValidationError(f"Failed to create product: {str(e)}") from e

    async def _cache_product(self, product: Product) -> None:
        """Cache the created product."""
        try:
            # Convert product to DTO for caching
            product_dto = ProductDto(
                id=product.id,
                name=product.name,
                category=product.category,
                description=product.description,
                picture_url=product.image_file,
                price=product.price,
            )
            
            # Cache the product
            await self.cache_service.set_product(
                product.id,
                product_dto.model_dump(),
                ttl=3600  # 1 hour TTL
            )
            
            logger.log_debug_with_context(
                f"Cached product {product.id}",
                product_id=str(product.id),
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to cache product {product.id}",
                error=e,
                product_id=str(product.id),
            )

    async def _publish_product_created_event(self, product: Product) -> None:
        """Publish product created integration event."""
        try:
            await self.event_publisher.publish_product_created(
                product_id=product.id,
                product_name=product.name,
                price=float(product.price),
                category_id=None,  # TODO: Add category support
                additional_data={
                    "description": product.description,
                    "picture_url": product.image_file,
                    "categories": product.category,
                }
            )
            
            logger.log_debug_with_context(
                f"Published ProductCreated event for {product.id}",
                product_id=str(product.id),
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to publish ProductCreated event for {product.id}",
                error=e,
                product_id=str(product.id),
            )


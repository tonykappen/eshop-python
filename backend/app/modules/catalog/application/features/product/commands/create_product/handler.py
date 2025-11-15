"""CreateProductHandler with 1-1 parity to .NET implementation."""

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.contracts.product.dtos import ProductDto
from app.modules.catalog.domain.exceptions import (
    ProductCreationError,
    ProductValidationError,
)
from app.modules.catalog.domain.product.models.product import Product
from app.modules.catalog.infrastructure.persistence.repositories.product_repository import ProductRepositoryImpl as ProductRepository
from app.core.database.session import AsyncSessionLocal


from .command import CreateProductCommand, CreateProductResult


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
            
        # picture_url is now optional, so no validation needed
            
        if not command.category:
            errors.append("At least one category is required")
            
        return errors


class CreateProductHandler(IRequestHandler[CreateProductCommand, CreateProductResult]):
    """Handler for CreateProductCommand - matches .NET CreateProductHandler."""

    def __init__(self) -> None:
        """Initialize handler."""
        pass

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
            from app.modules.catalog.domain.value_objects import Money
            
            # Use default empty string if picture_url is not provided (optional field)
            image_file = command.picture_url.strip() if command.picture_url and command.picture_url.strip() else ""
            
            price_money = Money(
                amount=Decimal(str(command.price)),
                currency="USD"  # Default currency
            )
            
            product = Product.create(
                product_id=uuid4(),
                name=command.name,
                sku=f"{command.name.upper().replace(' ', '-')[:20]}-{uuid4().hex[:8]}",  # Generate SKU
                category=command.category,
                description=command.description,
                image_file=image_file,  # Optional: can be empty string
                price=price_money,
            )
            return product
        except Exception as e:
            raise ProductValidationError(f"Failed to create product: {str(e)}") from e


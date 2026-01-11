"""CreateProductHandler with 1-1 parity to .NET implementation."""

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.modules.catalog.domain.exceptions.product import (
    ProductCreationError,
    ProductValidationError,
)
from app.modules.catalog.domain.entities.product.product import Product
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
            errors.append("Product name is required and cannot be empty")
            
        if not command.description or not command.description.strip():
            errors.append("Product description is required and cannot be empty")
            
        if command.price <= 0:
            errors.append("Product price must be greater than 0")
        elif command.price < 0.01:
            errors.append("Product price must be at least $0.01")
            
        # picture_url is now optional, so no validation needed
            
        if not command.category:
            errors.append("At least one category is required. Please add a category using the 'Add' button")
        elif isinstance(command.category, list):
            # Filter out empty strings and whitespace-only categories
            valid_categories = [cat.strip() for cat in command.category if cat and cat.strip()]
            if not valid_categories:
                errors.append("At least one valid category is required. Categories cannot be empty or whitespace-only")
            
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
            # Format errors more user-friendly
            if len(errors) == 1:
                error_message = errors[0]
            else:
                error_message = "Please fix the following errors: " + "; ".join(errors)
            raise ProductValidationError(error_message, field=None)

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

        # Validate product data (additional validation beyond command validator)
        if not command.name or not command.name.strip():
            raise ProductValidationError("Product name is required and cannot be empty", field="name")

        if command.price <= 0:
            raise ProductValidationError(
                "Product price must be greater than $0.00", field="price"
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


"""UpdateProductHandler with 1-1 parity to .NET implementation."""

import asyncio
from typing import Any
from uuid import UUID
from pydantic import BaseModel

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.exceptions import (
    ProductNotFoundError,
    ProductUpdateError,
    ProductValidationError,
)
from app.modules.catalog.domain.product.models.product import Product
from app.modules.catalog.infrastructure.persistence.repositories.product_repository import ProductRepositoryImpl as ProductRepository
from app.core.database.session import AsyncSessionLocal


from .command import UpdateProductCommand, UpdateProductResult


class UpdateProductCommandValidator:
    """Validator for UpdateProductCommand - matches .NET UpdateProductCommandValidator."""

    def validate(self, command: UpdateProductCommand) -> list[str]:
        """
        Validate the update product command.
        
        Args:
            command: The command to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not command.id:
            errors.append("Id is required")
            
        if not command.name or not command.name.strip():
            errors.append("Name is required")
            
        if command.price <= 0:
            errors.append("Price must be greater than 0")
            
        if not command.description or not command.description.strip():
            errors.append("Description is required")
            
        # picture_url is now optional, so no validation needed
            
        if not command.category:
            errors.append("At least one category is required")
            
        return errors


class UpdateProductHandler(IRequestHandler[UpdateProductCommand, UpdateProductResult]):
    """Handler for UpdateProductCommand - matches .NET UpdateProductHandler."""

    def __init__(self) -> None:
        """Initialize handler."""
        pass

    async def handle(
        self, command: UpdateProductCommand, cancellation_token: CancellationToken
    ) -> UpdateProductResult:
        """
        Handle the command - matches .NET Handle(UpdateProductCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            UpdateProductResult indicating success

        Raises:
            ProductNotFoundError: If product with given ID is not found
            ProductUpdateError: If update operation fails
        """
        # Validate command first
        validator = UpdateProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            
            # Find the product
            product = await repository.get_by_id(command.id)
            if product is None:
                raise ProductNotFoundError(command.id)

            try:
                # Update product with new values
                self._update_product_with_new_values(product, command)

                # Save to database
                await repository.update(product)
                await session.commit()

                return UpdateProductResult(is_success=True)
            except Exception as e:
                await session.rollback()
                raise ProductUpdateError(
                    message="Failed to update product in database",
                    details=str(e)
                ) from e


    def _update_product_with_new_values(self, product: Product, command: UpdateProductCommand) -> None:
        """
        Update product with new values - matches .NET UpdateProductWithNewValues method.
        
        Args:
            product: Product entity to update
            command: Update command with new values
        """
        try:
            from app.modules.catalog.domain.value_objects import Money
            from decimal import Decimal
            
            # Convert float price to Money value object
            # Use existing currency from product or default to USD
            currency = product.price.currency if product.price else "USD"
            price_money = Money(
                amount=Decimal(str(command.price)),
                currency=currency
            )
            
            # Use provided picture_url if it exists, otherwise keep existing image_file
            # Handle empty string as valid (optional field)
            if command.picture_url is not None:
                image_file = command.picture_url.strip() if command.picture_url.strip() else ""
            else:
                image_file = product.image_file or ""
            
            product.update(
                name=command.name,
                category=command.category,
                description=command.description,
                image_file=image_file,  # Map picture_url to image_file for domain model
                price=price_money,
            )
        except Exception as e:
            raise ProductValidationError(f"Failed to update product: {str(e)}") from e


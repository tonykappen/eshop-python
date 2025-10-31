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
from app.modules.catalog.infrastructure.persistence.repositories.product_repository_legacy import ProductRepository
from app.modules.catalog.infrastructure.cache_service import CatalogCacheService, RedisCacheService
from app.modules.catalog.infrastructure.event_publisher import CatalogEventPublisherFactory
from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class UpdateProductCommand(BaseModel):
    """Command to update an existing product - matches .NET UpdateProductCommand."""

    id: UUID
    name: str
    description: str
    price: float
    picture_url: str | None = None  # Optional
    category: list[str]


class UpdateProductResult:
    """Result of updating a product - matches .NET UpdateProductResult."""

    def __init__(self, is_success: bool) -> None:
        self.is_success = is_success


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
        self.cache_service = CatalogCacheService(RedisCacheService())
        self.event_publisher = CatalogEventPublisherFactory.get_instance()

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
                # Store old price for event publishing
                old_price = float(product.price.amount) if product.price else 0.0
                
                # Update product with new values
                self._update_product_with_new_values(product, command)

                # Save to database
                await repository.update(product)
                await session.commit()

                # Invalidate cache for this product
                await self.cache_service.invalidate_product(command.id)
                
                # Publish price changed event if price changed
                new_price = float(product.price.amount) if product.price else 0.0
                if old_price != new_price:
                    await self._publish_price_changed_event(command.id, old_price, new_price)

                # Invalidate products list cache
                await self.cache_service.invalidate_products_list()

                logger.log_with_context(
                    f"Product updated successfully: {product.name}",
                    "info",
                    product_id=str(command.id),
                    product_name=product.name,
                )

                return UpdateProductResult(True)
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
            
            # Use existing image_file if picture_url is not provided, otherwise use the provided value
            image_file = (command.picture_url or "").strip() if command.picture_url else product.image_file
            
            product.update(
                name=command.name,
                category=command.category,
                description=command.description,
                image_file=image_file,  # Map picture_url to image_file for domain model
                price=price_money,
            )
        except Exception as e:
            raise ProductValidationError(f"Failed to update product: {str(e)}") from e

    async def _publish_price_changed_event(self, product_id: UUID, old_price: float, new_price: float) -> None:
        """Publish product price changed integration event."""
        try:
            await self.event_publisher.publish_product_price_changed(
                product_id=product_id,
                old_price=old_price,
                new_price=new_price,
                price_change_reason="Product update",
                additional_data={
                    "updated_at": "now",  # TODO: Add proper timestamp
                }
            )
            
            logger.log_debug_with_context(
                f"Published ProductPriceChanged event for {product_id}",
                product_id=str(product_id),
                old_price=old_price,
                new_price=new_price,
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to publish ProductPriceChanged event for {product_id}",
                error=e,
                product_id=str(product_id),
            )


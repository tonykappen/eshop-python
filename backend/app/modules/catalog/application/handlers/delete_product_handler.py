"""DeleteProductHandler with 1-1 parity to .NET implementation."""

import asyncio
from typing import Any
from uuid import UUID
from pydantic import BaseModel

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.exceptions import (
    ProductNotFoundError,
    ProductDeleteError,
)
from app.modules.catalog.infrastructure.persistence.repositories.product_repository_legacy import ProductRepository
from app.modules.catalog.infrastructure.cache_service import CatalogCacheService, RedisCacheService
from app.modules.catalog.infrastructure.event_publisher import CatalogEventPublisherFactory
from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class DeleteProductCommand(BaseModel):
    """Command to delete a product - matches .NET DeleteProductCommand."""

    product_id: UUID


class DeleteProductResult:
    """Result of deleting a product - matches .NET DeleteProductResult."""

    def __init__(self, is_success: bool) -> None:
        self.is_success = is_success


class DeleteProductCommandValidator:
    """Validator for DeleteProductCommand - matches .NET DeleteProductCommandValidator."""

    def validate(self, command: DeleteProductCommand) -> list[str]:
        """
        Validate the delete product command.
        
        Args:
            command: The command to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not command.product_id:
            errors.append("Product Id is required")
            
        return errors


class DeleteProductHandler(IRequestHandler[DeleteProductCommand, DeleteProductResult]):
    """Handler for DeleteProductCommand - matches .NET DeleteProductHandler."""

    def __init__(self) -> None:
        """Initialize handler."""
        self.cache_service = CatalogCacheService(RedisCacheService())
        self.event_publisher = CatalogEventPublisherFactory.get_instance()

    async def handle(
        self, command: DeleteProductCommand, cancellation_token: CancellationToken
    ) -> DeleteProductResult:
        """
        Handle the command - matches .NET Handle(DeleteProductCommand command, CancellationToken cancellationToken).

        Args:
            command: The command to handle
            cancellation_token: Cancellation token

        Returns:
            DeleteProductResult indicating success

        Raises:
            ProductNotFoundError: If product with given ID is not found
            ProductDeleteError: If delete operation fails
        """
        # Validate command first
        validator = DeleteProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            from app.modules.catalog.domain.exceptions import ProductValidationError
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            
            # Check if product exists and get product details for event
            product = await repository.get_by_id(command.product_id)
            if not product:
                raise ProductNotFoundError(command.product_id)

            try:
                # Delete the product
                success = await repository.delete(command.product_id)
                await session.commit()

                if not success:
                    raise ProductDeleteError(
                        message="Failed to delete product from database"
                    )

                # Invalidate cache for this product
                await self.cache_service.invalidate_product(command.product_id)
                
                # Publish product deleted event
                await self._publish_product_deleted_event(product)
                
                # Also publish discontinued event (for backward compatibility/analytics)
                await self._publish_product_discontinued_event(product)
                
                # Invalidate products list cache
                await self.cache_service.invalidate_products_list()

                logger.log_with_context(
                    f"Product deleted successfully: {product.name}",
                    "info",
                    product_id=str(command.product_id),
                    product_name=product.name,
                )

                return DeleteProductResult(True)
            except Exception as e:
                await session.rollback()
                raise ProductDeleteError(
                    message="Failed to delete product from database", 
                    details=str(e)
                ) from e

    async def _publish_product_deleted_event(self, product) -> None:
        """Publish product deleted integration event."""
        try:
            from datetime import datetime
            deleted_at = datetime.now().isoformat()
            
            await self.event_publisher.publish_product_deleted(
                product_id=product.id,
                product_name=product.name,
                deleted_at=deleted_at,
                reason="Product deleted via API",
                additional_data={
                    "price": float(product.price.amount) if product.price else 0.0,
                    "categories": product.category,
                }
            )
            
            logger.log_debug_with_context(
                f"Published ProductDeleted event for {product.id}",
                product_id=str(product.id),
                product_name=product.name,
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to publish ProductDeleted event for {product.id}",
                error=e,
                product_id=str(product.id),
            )

    async def _publish_product_discontinued_event(self, product) -> None:
        """Publish product discontinued integration event (for backward compatibility)."""
        try:
            from datetime import datetime
            await self.event_publisher.publish_product_discontinued(
                product_id=product.id,
                discontinuation_date=datetime.now().isoformat(),
                reason="Product deleted",
                additional_data={
                    "product_name": product.name,
                    "deleted_at": datetime.now().isoformat(),
                }
            )
            
            logger.log_debug_with_context(
                f"Published ProductDiscontinued event for {product.id}",
                product_id=str(product.id),
                product_name=product.name,
            )
        except Exception as e:
            logger.log_error_with_context(
                f"Failed to publish ProductDiscontinued event for {product.id}",
                error=e,
                product_id=str(product.id),
            )


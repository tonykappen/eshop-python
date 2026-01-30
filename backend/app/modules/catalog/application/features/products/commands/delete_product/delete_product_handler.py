"""DeleteProductHandler with 1-1 parity to .NET implementation."""

import logging

from app.core.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.exceptions.product import (
    ProductDeleteError,
    ProductNotFoundError,
)
from app.modules.catalog.application.services.catalog_cache_service import (
    CatalogCacheService,
    RedisCacheService,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.redis.cached_product_repository import (
    CachedProductRepository,
)
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlProductRepository,
)

from .delete_product_command import DeleteProductCommand, DeleteProductResult


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
        pass

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
            from app.modules.catalog.domain.exceptions.product import (
                ProductValidationError,
            )

            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use Unit of Work to ensure interceptors are called
        from app.modules.catalog.infrastructure.persistence.unit_of_work import (
            SqlCatalogUnitOfWork,
        )

        async with AsyncSessionLocal() as session:
            uow = SqlCatalogUnitOfWork(session)
            repository = uow.products

            # Check if product exists
            if not await repository.exists(command.product_id):
                raise ProductNotFoundError(command.product_id)

            try:
                # Load domain entity to raise domain event
                product = await repository.get_by_id(command.product_id)
                if product is None:
                    raise ProductNotFoundError(command.product_id)

                # Call domain method to raise domain event (soft delete)
                product.deactivate()

                # Track entity in UoW for interceptors BEFORE delete
                # This ensures domain events are available to interceptors
                uow._entities.append(product)

                # Delete the product (soft delete via repository)
                # Note: repository.delete() does a direct SQL UPDATE, which bypasses
                # SQLAlchemy's entity tracking. However, we've already added the entity
                # to uow._entities above, so interceptors will still see it.
                success = await repository.delete(
                    command.product_id,
                    deleted_by=command.deleted_by,
                    deletion_reason=command.deletion_reason,
                )

                if not success:
                    raise ProductDeleteError(
                        message="Failed to delete product from database"
                    )

                # Commit via UoW (calls interceptors, including OutboxEnqueuerInterceptor)
                # The entity in uow._entities will be processed by interceptors
                await uow.commit()

                logger.info(f"Product {command.product_id} soft-deleted successfully.")
                return DeleteProductResult(is_success=True)
            except Exception as e:
                await uow.rollback()
                raise ProductDeleteError(
                    message="Failed to delete product from database", details=str(e)
                ) from e

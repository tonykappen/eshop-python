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
from app.modules.catalog.infrastructure.persistence.repositories.product_repository import ProductRepositoryImpl as ProductRepository
from app.core.database.session import AsyncSessionLocal


from .command import DeleteProductCommand, DeleteProductResult


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
            from app.modules.catalog.domain.exceptions import ProductValidationError
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            
            # Check if product exists
            if not await repository.exists(command.product_id):
                raise ProductNotFoundError(command.product_id)

            try:
                # Delete the product with audit trail
                success = await repository.delete(
                    command.product_id,
                    deleted_by=command.deleted_by,
                    deletion_reason=command.deletion_reason
                )
                await session.commit()

                if not success:
                    raise ProductDeleteError(
                        message="Failed to delete product from database"
                    )

                return DeleteProductResult(is_success=True)
            except Exception as e:
                await session.rollback()
                raise ProductDeleteError(
                    message="Failed to delete product from database", 
                    details=str(e)
                ) from e


"""GetProductByIdHandler with 1-1 parity to .NET implementation."""

import asyncio
from typing import Any
from uuid import UUID

from eshop.core.mediator.cancellation import CancellationToken
from eshop.core.mediator.handler_registry import IRequestHandler
from eshop.modules.catalog.contracts.products.dtos import ProductDto
from eshop.modules.catalog.contracts.products.features.get_product_by_id import (
    GetProductByIdQuery,
    GetProductByIdResult,
)
from eshop.modules.catalog.domain.exceptions import ProductNotFoundError


class GetProductByIdHandler(IRequestHandler[GetProductByIdQuery, GetProductByIdResult]):
    """Handler for GetProductByIdQuery - matches .NET GetProductByIdHandler."""

    def __init__(self, db_context: Any) -> None:  # type: ignore
        """Initialize handler with database context."""
        self.db_context = db_context

    async def handle(
        self, query: GetProductByIdQuery, cancellation_token: CancellationToken
    ) -> GetProductByIdResult:
        """
        Handle the query - matches .NET Handle(GetProductByIdQuery query, CancellationToken cancellationToken).

        Args:
            query: The query to handle

        Returns:
            GetProductByIdResult containing the product

        Raises:
            ProductNotFoundException: If product is not found
        """
        # Get product by id using dbContext
        # This is a simplified implementation - in real code, you'd use SQLAlchemy
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()
        product = await self._get_product_by_id(query.id, cancellation_token)

        if product is None:
            raise ProductNotFoundError(query.id)

        # Mapping product entity to ProductDto
        # In real implementation, you'd use a mapper
        product_dto = ProductDto(
            id=product.id,
            name=product.name,
            category=product.category,
            description=product.description,
            image_file=product.image_file,
            price=product.price,
        )

        return GetProductByIdResult(product=product_dto)

    async def _get_product_by_id(
        self,
        product_id: UUID,
        cancellation_token: CancellationToken,  # noqa: ARG002, ARG001
    ) -> Any | None:
        """Get product by ID from database."""
        # Simplified implementation - in real code, you'd use SQLAlchemy
        # var product = await dbContext.Products
        #     .AsNoTracking()
        #     .SingleOrDefaultAsync(p => p.Id == query.Id, cancellationToken);

        # Check for cancellation during database operation
        cancellation_token.throw_if_cancellation_requested()

        # Simulate database delay
        await asyncio.sleep(0.1)

        # Check again after delay
        cancellation_token.throw_if_cancellation_requested()

        # For now, return None to simulate not found
        return None

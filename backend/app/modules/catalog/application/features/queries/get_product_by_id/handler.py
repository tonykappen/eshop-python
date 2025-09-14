"""GetProductByIdHandler with 1-1 parity to .NET implementation."""

import asyncio
from typing import Any
from uuid import UUID

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.contracts.products.dtos import ProductDto
from .query import GetProductByIdQuery, GetProductByIdResult
from app.modules.catalog.domain.exceptions import ProductNotFoundError
from app.modules.catalog.infrastructure.product_repository import ProductRepository
from app.core.database.session import AsyncSessionLocal


class GetProductByIdHandler(IRequestHandler[GetProductByIdQuery, GetProductByIdResult]):
    """Handler for GetProductByIdQuery - matches .NET GetProductByIdHandler."""

    def __init__(self) -> None:
        """Initialize handler."""
        pass

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
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            product = await repository.get_by_id(query.id)

            if product is None:
                raise ProductNotFoundError(query.id)

            # Mapping product entity to ProductDto
            product_dto = ProductDto(
                id=product.id,
                name=product.name,
                category=product.category,
                description=product.description,
                picture_url=product.image_file,  # Map image_file to picture_url
                price=product.price,
            )

            return GetProductByIdResult(product=product_dto)


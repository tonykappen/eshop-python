"""GetProductsHandler for listing products with pagination and filtering."""

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.contracts.products.dtos import ProductDto
from app.modules.catalog.domain.models import Product
from app.modules.catalog.infrastructure.product_repository import ProductRepository
from app.core.database.session import AsyncSessionLocal
from .query import GetProductsQuery, GetProductsResult


class GetProductsHandler(
    IRequestHandler[GetProductsQuery, GetProductsResult]
):
    """Handler for GetProductsQuery - provides paginated product listing."""

    def __init__(self) -> None:
        """Initialize handler."""
        pass

    async def handle(
        self, query: GetProductsQuery, cancellation_token: CancellationToken
    ) -> GetProductsResult:
        """
        Handle the query to get products with pagination and filtering.

        Args:
            query: The query containing pagination and filter parameters
            cancellation_token: Cancellation token for async operations

        Returns:
            PaginatedResult containing paginated products
        """
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Use real database repository
        async with AsyncSessionLocal() as session:
            repository = ProductRepository(session)
            
            # Get products based on filters
            if query.search_term:
                products, total_count = await repository.search(
                    query.search_term, query.page, query.page_size
                )
            elif query.category_id:
                # For now, we'll use category name instead of ID
                # In a real implementation, you'd have a category lookup
                products, total_count = await repository.get_by_category(
                    str(query.category_id), query.page, query.page_size
                )
            else:
                products, total_count = await repository.get_all(
                    query.page, query.page_size
                )
            
            # Convert to DTOs
            product_dtos = [self._map_to_dto(product) for product in products]
            
            total_pages = (total_count + query.page_size - 1) // query.page_size
            return GetProductsResult(
                items=product_dtos,
                total=total_count,
                page=query.page,
                size=query.page_size,
                pages=total_pages,
            )



    def _map_to_dto(self, product: Product) -> ProductDto:
        """Map product entity to DTO."""
        return ProductDto(
            id=product.id,
            name=product.name,
            category=product.category,  # Keep as list[str] for DTO
            description=product.description,
            picture_url=product.image_file,  # Map image_file to picture_url
            price=product.price,  # Keep as Decimal for DTO
        )

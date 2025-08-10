"""GetProductsHandler for listing products with pagination and filtering."""

import asyncio
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.core.contracts.cqrs import IQuery
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.core.pagination.models import PaginatedResult
from app.modules.catalog.contracts.products.dtos import ProductDto
from app.modules.catalog.domain.models import Product


class GetProductsQuery(IQuery[PaginatedResult[ProductDto]]):
    """Query to get products with optional filtering and pagination."""

    page: int = 1
    page_size: int = 10
    category_id: UUID | None = None
    search_term: str | None = None


class GetProductsHandler(
    IRequestHandler[GetProductsQuery, PaginatedResult[ProductDto]]
):
    """Handler for GetProductsQuery - provides paginated product listing."""

    def __init__(self, db_context: Any) -> None:  # type: ignore
        """Initialize handler with database context."""
        self.db_context = db_context

    async def handle(
        self, query: GetProductsQuery, cancellation_token: CancellationToken
    ) -> PaginatedResult[ProductDto]:
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

        # Get products with pagination and filtering
        return await self._get_products_paginated(query, cancellation_token)

    async def _get_products_paginated(
        self, query: GetProductsQuery, cancellation_token: CancellationToken
    ) -> PaginatedResult[ProductDto]:
        """
        Get products with pagination and filtering from database.

        Args:
            query: Query parameters
            cancellation_token: Cancellation token

        Returns:
            Paginated result of products
        """
        # This is a simplified implementation - in real code, you'd use SQLAlchemy
        # Check for cancellation
        cancellation_token.throw_if_cancellation_requested()

        # Simulate database query with pagination
        await asyncio.sleep(0.01)  # Simulate database call

        # Mock data for demonstration
        mock_products = await self._create_mock_products()

        # Apply filtering
        filtered_products = self._apply_filters(mock_products, query)

        # Apply pagination
        total_count = len(filtered_products)
        start_index = (query.page - 1) * query.page_size
        end_index = start_index + query.page_size
        page_products = filtered_products[start_index:end_index]

        # Convert to DTOs
        product_dtos = [self._map_to_dto(product) for product in page_products]

        total_pages = (total_count + query.page_size - 1) // query.page_size
        return PaginatedResult(
            items=product_dtos,
            total=total_count,
            page=query.page,
            size=query.page_size,
            pages=total_pages,
        )

    async def _create_mock_products(self) -> list[Product]:
        """Create mock products for demonstration."""
        from uuid import uuid4

        return [
            Product.create(
                product_id=uuid4(),
                name="Laptop Computer",
                category=["Electronics"],
                description="High-performance laptop for work and gaming",
                image_file="laptop.jpg",
                price=Decimal("999.99"),
            ),
            Product.create(
                product_id=uuid4(),
                name="Wireless Mouse",
                category=["Electronics"],
                description="Ergonomic wireless mouse with precision tracking",
                image_file="mouse.jpg",
                price=Decimal("29.99"),
            ),
            Product.create(
                product_id=uuid4(),
                name="Office Chair",
                category=["Furniture"],
                description="Comfortable ergonomic office chair",
                image_file="chair.jpg",
                price=Decimal("249.99"),
            ),
            Product.create(
                product_id=uuid4(),
                name="Coffee Mug",
                category=["Kitchen"],
                description="Ceramic coffee mug with handle",
                image_file="mug.jpg",
                price=Decimal("12.99"),
            ),
        ]

    def _apply_filters(
        self, products: list[Product], query: GetProductsQuery
    ) -> list[Product]:
        """Apply filtering to products list."""
        filtered = products

        # Filter by category if specified
        if query.category_id:
            # In real implementation, you'd match by category ID
            filtered = [p for p in filtered if str(query.category_id) in p.category]

        # Filter by search term if specified
        if query.search_term:
            search_lower = query.search_term.lower()
            filtered = [
                p
                for p in filtered
                if search_lower in p.name.lower()
                or search_lower in p.description.lower()
            ]

        return filtered

    def _map_to_dto(self, product: Product) -> ProductDto:
        """Map product entity to DTO."""
        return ProductDto(
            id=product.id,
            name=product.name,
            category=product.category,  # Keep as list[str] for DTO
            description=product.description,
            image_file=product.image_file,
            price=product.price,  # Keep as Decimal for DTO
        )

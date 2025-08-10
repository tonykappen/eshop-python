"""GetProductsHandler for listing products with pagination and filtering."""

import asyncio
from typing import Any, List
from uuid import UUID

from eshop.core.mediator.cancellation import CancellationToken
from eshop.core.mediator.handler_registry import IRequestHandler
from eshop.core.pagination.models import PaginatedResult
from eshop.modules.catalog.contracts.products.dtos import ProductDto
from eshop.modules.catalog.domain.models import Product


class GetProductsQuery:
    """Query to get products with optional filtering and pagination."""

    def __init__(
        self,
        page: int = 1,
        page_size: int = 10,
        category_id: UUID | None = None,
        search_term: str | None = None,
    ) -> None:
        self.page = page
        self.page_size = page_size
        self.category_id = category_id
        self.search_term = search_term


class GetProductsResult:
    """Result containing paginated products."""

    def __init__(self, products: PaginatedResult[ProductDto]) -> None:
        self.products = products


class GetProductsHandler(IRequestHandler[GetProductsQuery, GetProductsResult]):
    """Handler for GetProductsQuery - provides paginated product listing."""

    def __init__(self, db_context: Any) -> None:  # type: ignore
        """Initialize handler with database context."""
        self.db_context = db_context

    async def handle(
        self, query: GetProductsQuery, cancellation_token: CancellationToken
    ) -> GetProductsResult:
        """
        Handle the query to get products with pagination and filtering.

        Args:
            query: The query containing pagination and filter parameters
            cancellation_token: Cancellation token for async operations

        Returns:
            GetProductsResult containing paginated products
        """
        # Check for cancellation before database operation
        cancellation_token.throw_if_cancellation_requested()

        # Get products with pagination and filtering
        products = await self._get_products_paginated(query, cancellation_token)

        return GetProductsResult(products=products)

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

        return PaginatedResult(
            items=product_dtos,
            total_count=total_count,
            page=query.page,
            page_size=query.page_size,
        )

    async def _create_mock_products(self) -> List[Product]:
        """Create mock products for demonstration."""
        from uuid import uuid4

        return [
            Product.create(
                product_id=uuid4(),
                name="Laptop Computer",
                category="Electronics",
                description="High-performance laptop for work and gaming",
                image_file="laptop.jpg",
                price=999.99,
            ),
            Product.create(
                product_id=uuid4(),
                name="Wireless Mouse",
                category="Electronics",
                description="Ergonomic wireless mouse with precision tracking",
                image_file="mouse.jpg",
                price=29.99,
            ),
            Product.create(
                product_id=uuid4(),
                name="Office Chair",
                category="Furniture",
                description="Comfortable ergonomic office chair",
                image_file="chair.jpg",
                price=249.99,
            ),
            Product.create(
                product_id=uuid4(),
                name="Coffee Mug",
                category="Kitchen",
                description="Ceramic coffee mug with handle",
                image_file="mug.jpg",
                price=12.99,
            ),
        ]

    def _apply_filters(
        self, products: List[Product], query: GetProductsQuery
    ) -> List[Product]:
        """Apply filtering to products list."""
        filtered = products

        # Filter by category if specified
        if query.category_id:
            # In real implementation, you'd match by category ID
            filtered = [p for p in filtered if p.category == str(query.category_id)]

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
            category=product.category,
            description=product.description,
            image_file=product.image_file,
            price=product.price,
        )

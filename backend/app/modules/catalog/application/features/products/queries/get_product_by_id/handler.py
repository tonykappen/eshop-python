"""GetProductByIdHandler with 1-1 parity to .NET implementation."""

import asyncio
from typing import Any
from uuid import UUID

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from .query import GetProductByIdQuery, GetProductByIdResult
from app.modules.catalog.domain.exceptions.product import ProductNotFoundError
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import SqlProductRepository as ProductRepository
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

            # Convert SKU value object to string
            sku_str = str(product.sku) if product.sku else ""
            
            # Convert Money value object to float and get currency
            price_float = float(product.price.amount) if product.price else 0.0
            currency_str = product.price.currency if product.price else "USD"
            
            # Convert datetime fields to ISO format strings
            created_at_str = product.created_at.isoformat() if product.created_at else ""
            updated_at_str = product.last_modified.isoformat() if product.last_modified else ""
            
            # Handle image_file: convert empty strings to None
            image_file = product.image_file.strip() if product.image_file and product.image_file.strip() else None
            
            # Mapping product entity to ProductDto
            product_dto = ProductDto(
                id=product.id,
                name=product.name,
                sku=sku_str,
                category=product.category,
                description=product.description,
                image_file=image_file,
                price=price_float,
                currency=currency_str,
                version=product.version,
                created_at=created_at_str,
                updated_at=updated_at_str,
            )

            return GetProductByIdResult(product=product_dto)


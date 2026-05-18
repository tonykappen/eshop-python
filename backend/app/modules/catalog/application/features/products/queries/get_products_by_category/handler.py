"""GetProductsByCategoryHandler - Category-filter handler for products."""

from collections.abc import Callable
from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.application.public_interface.dto.product import \
    ProductDto
from app.modules.catalog.domain.entities.product.product import Product

from .get_products_by_category_query import (GetProductsByCategoryQuery,
                                             GetProductsByCategoryResult)

logger = BaseLogger(__name__)


class GetProductsByCategoryHandler(
    IRequestHandler[GetProductsByCategoryQuery, GetProductsByCategoryResult]
):
    """Category-filter handler for GetProductsByCategoryQuery."""

    def __init__(self, uow_factory: Callable[[], Any] | None = None) -> None:
        self._uow_factory = uow_factory

    async def handle(
        self, query: GetProductsByCategoryQuery, cancellation_token: CancellationToken
    ) -> GetProductsByCategoryResult:
        cancellation_token.throw_if_cancellation_requested()

        if self._uow_factory is None:
            raise RuntimeError("Handler not properly configured: missing UoW factory")

        async with self._uow_factory() as uow:
            repository = uow.products

            logger.log_with_context(
                "GetProductsByCategoryHandler",
                context={
                    "category": query.category,
                    "page": query.page,
                    "page_size": query.page_size,
                },
            )

            products, total_count = await repository.get_by_category(
                query.category, query.page, query.page_size
            )

            logger.log_with_context(
                "Repository returned products for category",
                context={
                    "category": query.category,
                    "product_count": len(products),
                    "total_count": total_count,
                },
            )

            product_dtos = [self._map_to_dto(product) for product in products]

            total_pages = (
                (total_count + query.page_size - 1) // query.page_size
                if total_count > 0
                else 0
            )

            return GetProductsByCategoryResult(
                items=product_dtos,
                total=total_count,
                page=query.page,
                size=query.page_size,
                pages=total_pages,
                category=query.category,
            )

    def _map_to_dto(self, product: Product) -> ProductDto:
        sku_str = str(product.sku) if product.sku else ""
        price_float = float(product.price.amount) if product.price else 0.0
        currency_str = product.price.currency if product.price else "USD"
        created_at_str = product.created_at.isoformat() if product.created_at else ""
        updated_at_str = (
            product.last_modified.isoformat() if product.last_modified else ""
        )
        image_file = (
            product.image_file.strip()
            if product.image_file and product.image_file.strip()
            else None
        )

        return ProductDto(
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

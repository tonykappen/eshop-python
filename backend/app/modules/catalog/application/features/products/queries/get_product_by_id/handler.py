"""GetProductByIdHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from typing import Any

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.application.public_interface.dto.product import ProductDto
from app.modules.catalog.domain.exceptions.product import ProductNotFoundError

from .get_product_by_id_query import GetProductByIdQuery, GetProductByIdResult


class GetProductByIdHandler(IRequestHandler[GetProductByIdQuery, GetProductByIdResult]):
    """Handler for GetProductByIdQuery - matches .NET GetProductByIdHandler."""

    def __init__(self, uow_factory: Callable[[], Any] | None = None) -> None:
        self._uow_factory = uow_factory

    async def handle(
        self, query: GetProductByIdQuery, cancellation_token: CancellationToken
    ) -> GetProductByIdResult:
        cancellation_token.throw_if_cancellation_requested()

        if self._uow_factory is None:
            raise RuntimeError("Handler not properly configured: missing UoW factory")

        async with self._uow_factory() as uow:
            product = await uow.products.get_by_id(query.id)

            if product is None:
                raise ProductNotFoundError(query.id)

            sku_str = str(product.sku) if product.sku else ""
            price_float = float(product.price.amount) if product.price else 0.0
            currency_str = product.price.currency if product.price else "USD"
            created_at_str = (
                product.created_at.isoformat() if product.created_at else ""
            )
            updated_at_str = (
                product.last_modified.isoformat() if product.last_modified else ""
            )
            image_file = (
                product.image_file.strip()
                if product.image_file and product.image_file.strip()
                else None
            )

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

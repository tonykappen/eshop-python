"""UpdateProductHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from decimal import Decimal
from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.exceptions.product import (
    ProductNotFoundError,
    ProductUpdateError,
    ProductValidationError,
)
from app.modules.catalog.domain.value_objects import Money

from .update_product_command import UpdateProductCommand, UpdateProductResult

logger = BaseLogger(__name__)


class UpdateProductCommandValidator:
    """Validator for UpdateProductCommand - matches .NET UpdateProductCommandValidator."""

    def validate(self, command: UpdateProductCommand) -> list[str]:
        errors: list[str] = []

        if not command.id:
            errors.append("Id is required")
        if not command.name or not command.name.strip():
            errors.append("Name is required")
        if command.price <= 0:
            errors.append("Price must be greater than 0")
        if not command.description or not command.description.strip():
            errors.append("Description is required")
        if not command.category:
            errors.append("At least one category is required")

        return errors


class UpdateProductHandler(IRequestHandler[UpdateProductCommand, UpdateProductResult]):
    """Handler for UpdateProductCommand - matches .NET UpdateProductHandler."""

    def __init__(self, uow_factory: Callable[[], Any] | None = None) -> None:
        self._uow_factory = uow_factory

    async def handle(
        self, command: UpdateProductCommand, cancellation_token: CancellationToken
    ) -> UpdateProductResult:
        validator = UpdateProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            raise ProductValidationError(
                f"Command validation failed: {', '.join(errors)}"
            )

        cancellation_token.throw_if_cancellation_requested()

        if self._uow_factory is None:
            raise ProductUpdateError(
                message="Handler not properly configured: missing UoW factory"
            )

        async with self._uow_factory() as uow:
            product = await uow.products.get_by_id(command.id)
            if product is None:
                raise ProductNotFoundError(command.id)

            try:
                old_price = product.price

                self._update_product_with_new_values(product, command)

                domain_event_count = len(product.domain_events) if hasattr(product, "domain_events") else 0
                if old_price != product.price:
                    logger.log_with_context(
                        "Price changed",
                        context={
                            "product_id": str(command.id),
                            "old_price": str(old_price),
                            "new_price": str(product.price),
                            "domain_event_count": domain_event_count,
                        },
                    )

                uow.track(product)
                updated_product = await uow.products.update(product)

                if updated_product and hasattr(product, "domain_events") and product.domain_events:
                    if hasattr(updated_product, "domain_events"):
                        from copy import deepcopy

                        updated_product.domain_events = []
                        for event in product.domain_events:
                            event_copy = deepcopy(event)
                            if hasattr(event_copy, "product"):
                                event_copy.product = updated_product
                            updated_product.domain_events.append(event_copy)
                    uow.track(updated_product)

                return UpdateProductResult(is_success=True)
            except (ProductNotFoundError, ProductUpdateError, ProductValidationError):
                raise
            except Exception as e:
                raise ProductUpdateError(
                    message="Failed to update product in database", details=str(e)
                ) from e

    def _update_product_with_new_values(
        self, product: Product, command: UpdateProductCommand
    ) -> None:
        try:
            currency = product.price.currency if product.price else "USD"
            price_money = Money(amount=Decimal(str(command.price)), currency=currency)

            if command.picture_url is not None:
                image_file = (
                    command.picture_url.strip() if command.picture_url.strip() else ""
                )
            else:
                image_file = product.image_file or ""

            product.update(
                name=command.name,
                category=command.category,
                description=command.description,
                image_file=image_file,
                price=price_money,
            )
        except Exception as e:
            raise ProductValidationError(f"Failed to update product: {e!s}") from e

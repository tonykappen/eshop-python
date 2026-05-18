"""CreateProductHandler with 1-1 parity to .NET implementation."""

from collections.abc import Callable
from decimal import Decimal
from typing import Any
from uuid import uuid4

from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.handler_registry import IRequestHandler
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.exceptions.product import (
    ProductCreationError, ProductValidationError)
from app.modules.catalog.domain.value_objects import Money

from .create_product_command import CreateProductCommand, CreateProductResult


class CreateProductCommandValidator:
    """Validator for CreateProductCommand - matches .NET CreateProductCommandValidator."""

    def validate(self, command: CreateProductCommand) -> list[str]:
        errors: list[str] = []

        if not command.name or not command.name.strip():
            errors.append("Product name is required and cannot be empty")

        if not command.description or not command.description.strip():
            errors.append("Product description is required and cannot be empty")

        if command.price <= 0:
            errors.append("Product price must be greater than 0")
        elif command.price < 0.01:
            errors.append("Product price must be at least $0.01")

        if not command.category:
            errors.append(
                "At least one category is required. Please add a category using the 'Add' button"
            )
        elif isinstance(command.category, list):
            valid_categories = [
                cat.strip() for cat in command.category if cat and cat.strip()
            ]
            if not valid_categories:
                errors.append(
                    "At least one valid category is required. Categories cannot be empty or whitespace-only"
                )

        return errors


class CreateProductHandler(IRequestHandler[CreateProductCommand, CreateProductResult]):
    """Handler for CreateProductCommand - matches .NET CreateProductHandler."""

    def __init__(self, uow_factory: Callable[[], Any] | None = None) -> None:
        self._uow_factory = uow_factory

    async def handle(
        self, command: CreateProductCommand, cancellation_token: CancellationToken
    ) -> CreateProductResult:
        validator = CreateProductCommandValidator()
        errors = validator.validate(command)
        if errors:
            if len(errors) == 1:
                error_message = errors[0]
            else:
                error_message = "Please fix the following errors: " + "; ".join(errors)
            raise ProductValidationError(error_message, field=None)

        cancellation_token.throw_if_cancellation_requested()

        product = self._create_new_product(command)

        if self._uow_factory is None:
            raise ProductCreationError(
                message="Handler not properly configured: missing UoW factory"
            )

        async with self._uow_factory() as uow:
            try:
                await uow.products.add(product)
                return CreateProductResult(id=product.id)
            except Exception as e:
                raise ProductCreationError(
                    message="Failed to save product to database", details=str(e)
                ) from e

    def _create_new_product(self, command: CreateProductCommand) -> Product:
        if not command.name or not command.name.strip():
            raise ProductValidationError(
                "Product name is required and cannot be empty", field="name"
            )

        if command.price <= 0:
            raise ProductValidationError(
                "Product price must be greater than $0.00", field="price"
            )

        try:
            image_file = (
                command.picture_url.strip()
                if command.picture_url and command.picture_url.strip()
                else ""
            )

            price_money = Money(amount=Decimal(str(command.price)), currency="USD")

            product = Product.create(
                product_id=uuid4(),
                name=command.name,
                sku=f"{command.name.upper().replace(' ', '-')[:20]}-{uuid4().hex[:8]}",
                category=command.category,
                description=command.description,
                image_file=image_file,
                price=price_money,
            )
            return product
        except Exception as e:
            raise ProductValidationError(f"Failed to create product: {e!s}") from e

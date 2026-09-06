"""Tests for UpdateProductHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.mediator.cancellation import CancellationToken
from app.modules.catalog.application.features.products.commands.update_product.update_product_command import (
    UpdateProductCommand,
)
from app.modules.catalog.application.features.products.commands.update_product.update_product_handler import (
    UpdateProductCommandValidator,
    UpdateProductHandler,
)
from app.modules.catalog.domain.exceptions.product import (
    ProductNotFoundError,
    ProductUpdateError,
    ProductValidationError,
)
from app.modules.catalog.domain.value_objects import Money


class TestUpdateProductCommandValidator:
    def test_valid_command(self) -> None:
        cmd = UpdateProductCommand(
            id=uuid4(),
            name="Widget",
            description="A widget",
            price=Decimal("10.00"),
            category=["tools"],
        )
        assert UpdateProductCommandValidator().validate(cmd) == []

    def test_invalid_command_collects_errors(self) -> None:
        cmd = UpdateProductCommand(
            id=None,
            name="",
            description="",
            price=Decimal("0"),
            category=[],
        )
        errors = UpdateProductCommandValidator().validate(cmd)
        assert len(errors) >= 4


@pytest.mark.asyncio
async def test_handler_raises_when_uow_factory_missing() -> None:
    handler = UpdateProductHandler(uow_factory=None)
    cmd = UpdateProductCommand(
        id=uuid4(),
        name="Widget",
        description="Desc",
        price=Decimal("9.99"),
        category=["cat"],
    )
    with pytest.raises(ProductUpdateError):
        await handler.handle(cmd, CancellationToken())


@pytest.mark.asyncio
async def test_handler_raises_validation_error() -> None:
    handler = UpdateProductHandler(uow_factory=MagicMock())
    cmd = UpdateProductCommand(
        id=uuid4(),
        name="",
        description="",
        price=Decimal("-1"),
        category=[],
    )
    with pytest.raises(ProductValidationError):
        await handler.handle(cmd, CancellationToken())


@pytest.mark.asyncio
async def test_handler_raises_not_found() -> None:
    uow = AsyncMock()
    uow.products.get_by_id = AsyncMock(return_value=None)
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)

    handler = UpdateProductHandler(uow_factory=lambda: uow)
    product_id = uuid4()
    cmd = UpdateProductCommand(
        id=product_id,
        name="Widget",
        description="Desc",
        price=Decimal("9.99"),
        category=["cat"],
    )

    with pytest.raises(ProductNotFoundError):
        await handler.handle(cmd, CancellationToken())

"""Tests for UpdateItemPriceInBasketHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions.bad_request_exception import BadRequestException
from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_command import (
    UpdateItemPriceInBasketCommand,
    UpdateItemPriceInBasketResult,
)
from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_handler import (
    UpdateItemPriceInBasketHandler,
)


class TestUpdateItemPriceInBasketHandler:
    """Test UpdateItemPriceInBasketHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        """Test successful price update."""
        mock_repository = AsyncMock()
        handler = UpdateItemPriceInBasketHandler(repository=mock_repository)

        product_id = uuid4()
        new_price = Decimal("149.99")

        mock_repository.update_items_price = AsyncMock(return_value=True)

        command = UpdateItemPriceInBasketCommand(product_id=product_id, price=new_price)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, UpdateItemPriceInBasketResult)
        assert result.is_success is True
        mock_repository.update_items_price.assert_called_once_with(
            product_id, new_price
        )

    @pytest.mark.asyncio
    async def test_handle_no_items_updated_returns_false(self) -> None:
        """Test that no items updated returns false."""
        mock_repository = AsyncMock()
        handler = UpdateItemPriceInBasketHandler(repository=mock_repository)

        product_id = uuid4()
        new_price = Decimal("149.99")

        mock_repository.update_items_price = AsyncMock(return_value=False)

        command = UpdateItemPriceInBasketCommand(product_id=product_id, price=new_price)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, UpdateItemPriceInBasketResult)
        assert result.is_success is False

    @pytest.mark.asyncio
    async def test_handle_missing_product_id_raises_error(self) -> None:
        """Test that missing product ID raises validation error."""
        # Note: UpdateItemPriceInBasketCommand requires UUID, so we test the validator directly
        from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_handler import (
            UpdateItemPriceInBasketCommandValidator,
        )

        validator = UpdateItemPriceInBasketCommandValidator()
        # Create a command with None product_id using type ignore for testing
        command = UpdateItemPriceInBasketCommand(
            product_id=None,
            price=Decimal("149.99"),  # type: ignore[arg-type]
        )
        errors = validator.validate(command)
        assert "ProductId is required" in errors

    @pytest.mark.asyncio
    async def test_handle_invalid_price_raises_error(self) -> None:
        """Test that invalid price raises validation error."""
        mock_repository = AsyncMock()
        handler = UpdateItemPriceInBasketHandler(repository=mock_repository)

        command = UpdateItemPriceInBasketCommand(product_id=uuid4(), price=Decimal("0"))
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "Price must be greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_negative_price_raises_error(self) -> None:
        """Test that negative price raises validation error."""
        mock_repository = AsyncMock()
        handler = UpdateItemPriceInBasketHandler(repository=mock_repository)

        command = UpdateItemPriceInBasketCommand(
            product_id=uuid4(), price=Decimal("-10.00")
        )
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "Price must be greater than 0" in str(exc_info.value)

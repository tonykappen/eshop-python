"""Tests for RemoveItemFromBasketHandler."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.exceptions.bad_request_exception import BadRequestException
from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_command import (
    RemoveItemFromBasketCommand, RemoveItemFromBasketResult)
from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_handler import \
    RemoveItemFromBasketHandler
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException


class TestRemoveItemFromBasketHandler:
    """Test RemoveItemFromBasketHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        """Test successful item removal from basket."""
        mock_repository = AsyncMock()
        handler = RemoveItemFromBasketHandler(repository=mock_repository)

        user_name = "testuser"
        product_id = uuid4()
        basket_id = uuid4()

        # Mock basket
        mock_basket = MagicMock()
        mock_basket.id = basket_id
        mock_basket.remove_item = MagicMock()
        mock_repository.get_basket.return_value = mock_basket
        mock_repository.update_basket.return_value = mock_basket
        mock_repository.save_changes_async = AsyncMock()

        command = RemoveItemFromBasketCommand(
            user_name=user_name, product_id=product_id
        )
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, RemoveItemFromBasketResult)
        assert result.id == basket_id
        mock_repository.get_basket.assert_called_once_with(
            user_name, as_no_tracking=False
        )
        mock_basket.remove_item.assert_called_once_with(product_id)
        mock_repository.save_changes_async.assert_called_once_with(user_name)

    @pytest.mark.asyncio
    async def test_handle_empty_user_name_raises_error(self) -> None:
        """Test that empty user name raises validation error."""
        mock_repository = AsyncMock()
        handler = RemoveItemFromBasketHandler(repository=mock_repository)

        command = RemoveItemFromBasketCommand(user_name="", product_id=uuid4())
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "UserName is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_missing_product_id_raises_error(self) -> None:
        """Test that missing product ID raises validation error."""
        # Note: RemoveItemFromBasketCommand requires UUID, so we test the validator directly
        from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_handler import \
            RemoveItemFromBasketCommandValidator

        validator = RemoveItemFromBasketCommandValidator()
        # Create a command with None product_id using type ignore for testing
        command = RemoveItemFromBasketCommand(
            user_name="testuser",
            product_id=None,  # type: ignore[arg-type]
        )
        errors = validator.validate(command)
        assert "ProductId is required" in errors

    @pytest.mark.asyncio
    async def test_handle_basket_not_found_raises_error(self) -> None:
        """Test that basket not found raises error."""
        mock_repository = AsyncMock()
        handler = RemoveItemFromBasketHandler(repository=mock_repository)

        user_name = "testuser"
        product_id = uuid4()

        # Mock basket not found
        mock_repository.get_basket.side_effect = BasketNotFoundException(user_name)

        command = RemoveItemFromBasketCommand(
            user_name=user_name, product_id=product_id
        )
        token = CancellationToken()

        with pytest.raises(BasketNotFoundException):
            await handler.handle(command, token)

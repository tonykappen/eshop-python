"""Tests for CreateBasketHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.dtos.shopping_cart_dto import (
    ShoppingCartDto, ShoppingCartItemDto)
from app.modules.basket.application.features.basket.command.create_basket.create_basket_command import (
    CreateBasketCommand, CreateBasketResult)
from app.modules.basket.application.features.basket.command.create_basket.create_basket_handler import \
    CreateBasketHandler


class TestCreateBasketHandler:
    """Test CreateBasketHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        """Test successful basket creation."""
        mock_repository = AsyncMock()
        handler = CreateBasketHandler(repository=mock_repository)

        shopping_cart_dto = ShoppingCartDto(
            id=uuid4(),
            user_name="testuser",
            items=[],
        )

        command = CreateBasketCommand(shopping_cart=shopping_cart_dto)
        token = CancellationToken()

        # Mock repository.create_basket to return a basket
        mock_basket = MagicMock()
        mock_basket.id = shopping_cart_dto.id
        mock_repository.create_basket.return_value = mock_basket

        result = await handler.handle(command, token)

        assert isinstance(result, CreateBasketResult)
        assert result.id == mock_basket.id
        mock_repository.create_basket.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_with_items_success(self) -> None:
        """Test successful basket creation with items."""
        mock_repository = AsyncMock()
        handler = CreateBasketHandler(repository=mock_repository)

        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=uuid4(),
            product_id=uuid4(),
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        shopping_cart_dto = ShoppingCartDto(
            id=uuid4(),
            user_name="testuser",
            items=[item_dto],
        )

        command = CreateBasketCommand(shopping_cart=shopping_cart_dto)
        token = CancellationToken()

        mock_basket = MagicMock()
        mock_basket.id = shopping_cart_dto.id
        mock_repository.create_basket.return_value = mock_basket

        result = await handler.handle(command, token)

        assert isinstance(result, CreateBasketResult)
        mock_repository.create_basket.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_empty_user_name_raises_error(self) -> None:
        """Test that empty user name raises validation error."""
        mock_repository = AsyncMock()
        handler = CreateBasketHandler(repository=mock_repository)

        shopping_cart_dto = ShoppingCartDto(
            id=uuid4(),
            user_name="",  # Empty user name
            items=[],
        )

        command = CreateBasketCommand(shopping_cart=shopping_cart_dto)
        token = CancellationToken()

        from app.core.exceptions.bad_request_exception import \
            BadRequestException

        with pytest.raises(BadRequestException):
            await handler.handle(command, token)

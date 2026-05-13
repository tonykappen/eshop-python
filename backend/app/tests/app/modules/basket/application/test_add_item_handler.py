"""Tests for AddItemIntoBasketHandler."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.exceptions.bad_request_exception import BadRequestException
from app.core.exceptions.not_found_exception import NotFoundError
from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.dtos.shopping_cart_dto import ShoppingCartItemDto
from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_command import (
    AddItemIntoBasketCommand,
    AddItemIntoBasketResult,
)
from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_handler import (
    AddItemIntoBasketHandler,
)
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.catalog.application.features.products.queries.get_product_by_id.get_product_by_id_query import (
    GetProductByIdResult,
)
from app.modules.catalog.application.public_interface.dto.product import ProductDto


class TestAddItemIntoBasketHandler:
    """Test AddItemIntoBasketHandler."""

    @pytest.mark.asyncio
    async def test_handle_success_existing_basket(self):
        """Test successful add item to existing basket."""
        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )

        product_id = uuid4()
        user_name = "testuser"
        basket_id = uuid4()

        # Mock product result
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            sku="TEST-SKU-001",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=99.99,
            currency="USD",
            version=1,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        product_result = GetProductByIdResult(product=product_dto)
        mock_mediator.send.return_value = product_result

        # Mock existing basket
        mock_basket = MagicMock()
        mock_basket.id = basket_id
        mock_basket.add_item = MagicMock()
        mock_repository.get_basket.return_value = mock_basket
        mock_repository.update_basket.return_value = mock_basket
        mock_repository.save_changes_async = AsyncMock()

        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=basket_id,
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("99.99"),
            product_name="Test Product",
        )

        command = AddItemIntoBasketCommand(
            user_name=user_name, shopping_cart_item=item_dto
        )
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, AddItemIntoBasketResult)
        assert result.id == basket_id
        mock_repository.get_basket.assert_called_once_with(
            user_name, as_no_tracking=False
        )
        mock_basket.add_item.assert_called_once()
        mock_repository.save_changes_async.assert_called_once_with(user_name)

    @pytest.mark.asyncio
    async def test_handle_success_new_basket(self):
        """Test successful add item creates new basket if not exists."""
        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )

        product_id = uuid4()
        user_name = "testuser"
        basket_id = uuid4()

        # Mock product result
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            sku="TEST-SKU-001",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=99.99,
            currency="USD",
            version=1,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        product_result = GetProductByIdResult(product=product_dto)
        mock_mediator.send.return_value = product_result

        # Mock basket not found - will create new one
        mock_repository.get_basket.side_effect = BasketNotFoundException(user_name)

        # Mock new basket creation
        mock_basket = MagicMock()
        mock_basket.id = basket_id
        mock_basket.add_item = MagicMock()
        mock_repository.create_basket.return_value = mock_basket
        mock_repository.save_changes_async = AsyncMock()

        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=None,
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("99.99"),
            product_name="Test Product",
        )

        command = AddItemIntoBasketCommand(
            user_name=user_name, shopping_cart_item=item_dto
        )
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, AddItemIntoBasketResult)
        assert result.id == basket_id
        mock_repository.create_basket.assert_called_once()
        mock_repository.save_changes_async.assert_called_once_with(user_name)

    @pytest.mark.asyncio
    async def test_handle_empty_user_name_raises_error(self):
        """Test that empty user name raises validation error."""
        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )

        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=uuid4(),
            product_id=uuid4(),
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        command = AddItemIntoBasketCommand(user_name="", shopping_cart_item=item_dto)
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "UserName is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_invalid_quantity_raises_error(self):
        """Test that invalid quantity raises validation error."""
        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )

        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=uuid4(),
            product_id=uuid4(),
            quantity=0,  # Invalid quantity
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        command = AddItemIntoBasketCommand(
            user_name="testuser", shopping_cart_item=item_dto
        )
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "Quantity must be greater than 0" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_product_not_found_raises_error(self):
        """Test that product not found raises error."""
        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )

        product_id = uuid4()
        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=uuid4(),
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        # Mock product not found
        mock_mediator.send.side_effect = NotFoundError(product_id, "Product")

        command = AddItemIntoBasketCommand(
            user_name="testuser", shopping_cart_item=item_dto
        )
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_handle_invalid_product_result_raises_error(self):
        """Test that invalid product result raises error."""
        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )

        product_id = uuid4()
        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=uuid4(),
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        # Mock invalid product result
        mock_mediator.send.return_value = GetProductByIdResult(product=None)

        command = AddItemIntoBasketCommand(
            user_name="testuser", shopping_cart_item=item_dto
        )
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "not found or invalid" in str(exc_info.value)

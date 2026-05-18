"""Tests for CheckoutBasketHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.exceptions.bad_request_exception import BadRequestException
from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.dtos.basket_checkout_dto import \
    BasketCheckoutDto
from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_command import (
    CheckoutBasketCommand, CheckoutBasketResult)
from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_handler import \
    CheckoutBasketHandler
from app.modules.basket.domain.entities.basket import (ShoppingCart,
                                                       ShoppingCartItem)
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException


class TestCheckoutBasketHandler:
    """Test CheckoutBasketHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful basket checkout."""
        mock_repository = AsyncMock()
        mock_outbox_service = AsyncMock()
        handler = CheckoutBasketHandler(
            repository=mock_repository, outbox_service=mock_outbox_service
        )

        user_name = "testuser"
        customer_id = uuid4()
        basket_id = uuid4()

        # Mock basket with items
        mock_item = MagicMock(spec=ShoppingCartItem)
        mock_item.product_id = uuid4()
        mock_item.quantity = 2
        mock_item.price = Decimal("99.99")

        mock_basket = MagicMock(spec=ShoppingCart)
        mock_basket.id = basket_id
        mock_basket.items = [mock_item]
        mock_basket.total_price = Decimal("199.98")

        mock_repository.get_basket.return_value = mock_basket
        mock_repository.delete_basket = AsyncMock()
        mock_repository.save_changes_async = AsyncMock()
        mock_outbox_service.write_integration_event = AsyncMock()

        checkout_dto = BasketCheckoutDto(
            user_name=user_name,
            customer_id=customer_id,
            total_price=Decimal("199.98"),  # Required field
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

        command = CheckoutBasketCommand(basket_checkout=checkout_dto)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, CheckoutBasketResult)
        assert result.is_success is True
        mock_repository.get_basket.assert_called_once_with(
            user_name, as_no_tracking=False
        )
        mock_outbox_service.write_integration_event.assert_called_once()
        mock_repository.delete_basket.assert_called_once_with(user_name)
        mock_repository.save_changes_async.assert_called_once_with(user_name)

    @pytest.mark.asyncio
    async def test_handle_empty_user_name_raises_error(self):
        """Test that empty user name raises validation error."""
        mock_repository = AsyncMock()
        mock_outbox_service = AsyncMock()
        handler = CheckoutBasketHandler(
            repository=mock_repository, outbox_service=mock_outbox_service
        )

        checkout_dto = BasketCheckoutDto(
            user_name="",  # Empty user name
            customer_id=uuid4(),
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

        command = CheckoutBasketCommand(basket_checkout=checkout_dto)
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "UserName is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_null_basket_checkout_raises_error(self):
        """Test that null basket checkout raises validation error."""
        mock_repository = AsyncMock()
        mock_outbox_service = AsyncMock()
        handler = CheckoutBasketHandler(
            repository=mock_repository, outbox_service=mock_outbox_service
        )

        command = CheckoutBasketCommand(basket_checkout=None)
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "BasketCheckoutDto can't be null" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_basket_not_found_returns_false(self):
        """Test that basket not found returns failure result."""
        mock_repository = AsyncMock()
        mock_outbox_service = AsyncMock()
        handler = CheckoutBasketHandler(
            repository=mock_repository, outbox_service=mock_outbox_service
        )

        user_name = "testuser"
        checkout_dto = BasketCheckoutDto(
            user_name=user_name,
            customer_id=uuid4(),
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

        # Mock basket not found
        mock_repository.get_basket.side_effect = BasketNotFoundException(user_name)

        command = CheckoutBasketCommand(basket_checkout=checkout_dto)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, CheckoutBasketResult)
        assert result.is_success is False

    @pytest.mark.asyncio
    async def test_handle_exception_returns_false(self):
        """Test that exception during checkout returns failure result."""
        mock_repository = AsyncMock()
        mock_outbox_service = AsyncMock()
        handler = CheckoutBasketHandler(
            repository=mock_repository, outbox_service=mock_outbox_service
        )

        user_name = "testuser"
        checkout_dto = BasketCheckoutDto(
            user_name=user_name,
            customer_id=uuid4(),
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

        # Mock exception during processing
        mock_repository.get_basket.side_effect = Exception("Database error")

        command = CheckoutBasketCommand(basket_checkout=checkout_dto)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, CheckoutBasketResult)
        assert result.is_success is False

"""Tests for CreateOrderHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.exceptions.bad_request_exception import BadRequestException
from app.core.mediator.cancellation import CancellationToken
from app.modules.ordering.application.dtos.address_dto import AddressDto
from app.modules.ordering.application.dtos.order_dto import OrderDto
from app.modules.ordering.application.dtos.order_item_dto import OrderItemDto
from app.modules.ordering.application.dtos.payment_dto import PaymentDto
from app.modules.ordering.application.features.orders.command.create_order.create_order_command import (
    CreateOrderCommand,
    CreateOrderResult,
)
from app.modules.ordering.application.features.orders.command.create_order.create_order_handler import (
    CreateOrderHandler,
)


class TestCreateOrderHandler:
    """Test CreateOrderHandler."""

    @pytest.fixture
    def sample_order_dto(self) -> OrderDto:
        """Create sample order DTO for testing."""
        order_id = uuid4()
        customer_id = uuid4()
        product_id = uuid4()

        address_dto = AddressDto(
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
        )

        payment_dto = PaymentDto(
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

        item_dto = OrderItemDto(
            order_id=order_id,
            product_id=product_id,
            quantity=2,
            price=Decimal("99.99"),
        )

        return OrderDto(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=address_dto,
            billing_address=address_dto,
            payment=payment_dto,
            items=[item_dto],
        )

    @pytest.mark.asyncio
    async def test_handle_success(self, sample_order_dto: OrderDto) -> None:
        """Test successful order creation."""
        mock_repository = AsyncMock()
        handler = CreateOrderHandler(repository=mock_repository)

        command = CreateOrderCommand(order=sample_order_dto)
        token = CancellationToken()

        # Mock repository methods
        mock_repository.add = AsyncMock()
        mock_repository.save_changes_async = AsyncMock()

        result = await handler.handle(command, token)

        assert isinstance(result, CreateOrderResult)
        assert result.id == sample_order_dto.id
        mock_repository.add.assert_called_once()
        mock_repository.save_changes_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_empty_order_name_raises_error(
        self, sample_order_dto: OrderDto
    ) -> None:
        """Test that empty order name raises validation error."""
        mock_repository = AsyncMock()
        handler = CreateOrderHandler(repository=mock_repository)

        sample_order_dto.order_name = ""  # Empty order name
        command = CreateOrderCommand(order=sample_order_dto)
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "OrderName is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_whitespace_order_name_raises_error(
        self, sample_order_dto: OrderDto
    ) -> None:
        """Test that whitespace-only order name raises validation error."""
        mock_repository = AsyncMock()
        handler = CreateOrderHandler(repository=mock_repository)

        sample_order_dto.order_name = "   "  # Whitespace only
        command = CreateOrderCommand(order=sample_order_dto)
        token = CancellationToken()

        with pytest.raises(BadRequestException) as exc_info:
            await handler.handle(command, token)
        assert "OrderName is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_with_multiple_items(self, sample_order_dto: OrderDto) -> None:
        """Test order creation with multiple items."""
        mock_repository = AsyncMock()
        handler = CreateOrderHandler(repository=mock_repository)

        # Add more items
        product_id2 = uuid4()
        item_dto2 = OrderItemDto(
            order_id=sample_order_dto.id,
            product_id=product_id2,
            quantity=1,
            price=Decimal("49.99"),
        )
        sample_order_dto.items.append(item_dto2)

        command = CreateOrderCommand(order=sample_order_dto)
        token = CancellationToken()

        mock_repository.add = AsyncMock()
        mock_repository.save_changes_async = AsyncMock()

        result = await handler.handle(command, token)

        assert isinstance(result, CreateOrderResult)
        assert result.id == sample_order_dto.id
        mock_repository.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cancellation(self, sample_order_dto: OrderDto) -> None:
        """Test that cancellation is checked."""
        mock_repository = AsyncMock()
        handler = CreateOrderHandler(repository=mock_repository)

        command = CreateOrderCommand(order=sample_order_dto)
        token = CancellationToken()
        token.cancel()

        from app.core.mediator.cancellation import CancellationError

        with pytest.raises(CancellationError):
            await handler.handle(command, token)

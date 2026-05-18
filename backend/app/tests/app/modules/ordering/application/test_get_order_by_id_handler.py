"""Tests for GetOrderByIdHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.core.mediator.cancellation import CancellationToken
from app.modules.ordering.application.features.orders.query.get_order_by_id.get_order_by_id_handler import \
    GetOrderByIdHandler
from app.modules.ordering.application.features.orders.query.get_order_by_id.get_order_by_id_query import (
    GetOrderByIdQuery, GetOrderByIdResult)
from app.modules.ordering.domain.entities.order.order import Order
from app.modules.ordering.domain.exceptions.order import OrderNotFoundException
from app.modules.ordering.domain.value_objects import Address, Payment


class TestGetOrderByIdHandler:
    """Test GetOrderByIdHandler."""

    @pytest.fixture
    def sample_order(self) -> Order:
        """Create sample order for testing."""
        order_id = uuid4()
        customer_id = uuid4()

        shipping_address = Address.of(
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
        )

        billing_address = Address.of(
            first_name="John",
            last_name="Doe",
            email_address="john@example.com",
            address_line="123 Main St",
            country="USA",
            state="CA",
            zip_code="12345",
        )

        payment = Payment.of(
            card_name="John Doe",
            card_number="1234567890123456",
            expiration="12/25",
            cvv="123",
            payment_method=1,
        )

        order = Order.create(
            id=order_id,
            customer_id=customer_id,
            order_name="Test Order",
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment=payment,
        )

        order.add(product_id=uuid4(), quantity=2, price=Decimal("99.99"))

        return order

    @pytest.mark.asyncio
    async def test_handle_success(self, sample_order: Order) -> None:
        """Test successful order retrieval."""
        mock_repository = AsyncMock()
        handler = GetOrderByIdHandler(repository=mock_repository)

        mock_repository.get_by_id.return_value = sample_order

        query = GetOrderByIdQuery(id=sample_order.id)
        token = CancellationToken()

        result = await handler.handle(query, token)

        assert isinstance(result, GetOrderByIdResult)
        assert result.order is not None
        assert result.order.id == sample_order.id
        mock_repository.get_by_id.assert_called_once_with(sample_order.id)

    @pytest.mark.asyncio
    async def test_handle_order_not_found_raises_error(self) -> None:
        """Test that order not found raises error."""
        mock_repository = AsyncMock()
        handler = GetOrderByIdHandler(repository=mock_repository)

        order_id = uuid4()
        mock_repository.get_by_id.return_value = None

        query = GetOrderByIdQuery(id=order_id)
        token = CancellationToken()

        with pytest.raises(OrderNotFoundException):
            await handler.handle(query, token)

    @pytest.mark.asyncio
    async def test_handle_cancellation(self) -> None:
        """Test that cancellation is checked."""
        mock_repository = AsyncMock()
        handler = GetOrderByIdHandler(repository=mock_repository)

        order_id = uuid4()
        query = GetOrderByIdQuery(id=order_id)
        token = CancellationToken()
        token.cancel()

        from app.core.mediator.cancellation import CancellationError

        with pytest.raises(CancellationError):
            await handler.handle(query, token)

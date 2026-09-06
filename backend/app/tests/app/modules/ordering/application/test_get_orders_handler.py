"""Tests for GetOrdersHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from app.core.mediator.cancellation import CancellationToken
from app.modules.ordering.application.features.orders.query.get_orders.get_orders_handler import \
    GetOrdersHandler
from app.modules.ordering.application.features.orders.query.get_orders.get_orders_query import (
    GetOrdersQuery, GetOrdersResult, PaginationRequest)
from app.modules.ordering.domain.entities.order.order import Order
from app.modules.ordering.domain.value_objects import Address, Payment


class TestGetOrdersHandler:
    """Test GetOrdersHandler."""

    @pytest.fixture
    def sample_orders(self) -> list[Order]:
        """Create sample orders for testing."""
        orders = []
        for i in range(3):
            order_id = uuid4()
            customer_id = uuid4()

            shipping_address = Address.of(
                first_name=f"John{i}",
                last_name="Doe",
                email_address=f"john{i}@example.com",
                address_line="123 Main St",
                country="USA",
                state="CA",
                zip_code="12345",
            )

            billing_address = Address.of(
                first_name=f"John{i}",
                last_name="Doe",
                email_address=f"john{i}@example.com",
                address_line="123 Main St",
                country="USA",
                state="CA",
                zip_code="12345",
            )

            payment = Payment.of(
                card_name=f"John{i} Doe",
                card_number="1234567890123456",
                expiration="12/25",
                cvv="123",
                payment_method=1,
            )

            order = Order.create(
                id=order_id,
                customer_id=customer_id,
                order_name=f"Test Order {i}",
                shipping_address=shipping_address,
                billing_address=billing_address,
                payment=payment,
            )

            order.add(product_id=uuid4(), quantity=1, price=Decimal("99.99"))
            orders.append(order)

        return orders

    @pytest.mark.asyncio
    async def test_handle_success(self, sample_orders: list[Order]) -> None:
        """Test successful orders retrieval with pagination."""
        mock_repository = AsyncMock()
        handler = GetOrdersHandler(repository=mock_repository)

        total_count = len(sample_orders)
        mock_repository.get_all.return_value = (sample_orders, total_count)

        pagination_request = PaginationRequest(page_index=0, page_size=10)
        query = GetOrdersQuery(pagination_request=pagination_request)
        token = CancellationToken()

        result = await handler.handle(query, token)

        assert isinstance(result, GetOrdersResult)
        assert result.orders is not None
        assert result.orders.total == total_count
        assert len(result.orders.items) == len(sample_orders)
        assert result.orders.page == 1  # Converted from 0-based to 1-based
        assert result.orders.size == 10
        mock_repository.get_all.assert_called_once_with(skip=0, take=10)

    @pytest.mark.asyncio
    async def test_handle_pagination_second_page(
        self, sample_orders: list[Order]
    ) -> None:
        """Test pagination with second page."""
        mock_repository = AsyncMock()
        handler = GetOrdersHandler(repository=mock_repository)

        # Return empty list for second page
        mock_repository.get_all.return_value = ([], len(sample_orders))

        pagination_request = PaginationRequest(page_index=1, page_size=10)
        query = GetOrdersQuery(pagination_request=pagination_request)
        token = CancellationToken()

        result = await handler.handle(query, token)

        assert isinstance(result, GetOrdersResult)
        assert result.orders.page == 2  # Converted from 0-based to 1-based
        assert result.orders.size == 10
        assert len(result.orders.items) == 0
        mock_repository.get_all.assert_called_once_with(skip=10, take=10)

    @pytest.mark.asyncio
    async def test_handle_empty_orders(self) -> None:
        """Test retrieval when no orders exist."""
        mock_repository = AsyncMock()
        handler = GetOrdersHandler(repository=mock_repository)

        mock_repository.get_all.return_value = ([], 0)

        pagination_request = PaginationRequest(page_index=0, page_size=10)
        query = GetOrdersQuery(pagination_request=pagination_request)
        token = CancellationToken()

        result = await handler.handle(query, token)

        assert isinstance(result, GetOrdersResult)
        assert result.orders.total == 0
        assert len(result.orders.items) == 0

    @pytest.mark.asyncio
    async def test_handle_cancellation(self) -> None:
        """Test that cancellation is checked."""
        mock_repository = AsyncMock()
        handler = GetOrdersHandler(repository=mock_repository)

        pagination_request = PaginationRequest(page_index=0, page_size=10)
        query = GetOrdersQuery(pagination_request=pagination_request)
        token = CancellationToken()
        token.cancel()

        from app.core.mediator.cancellation import CancellationError

        with pytest.raises(CancellationError):
            await handler.handle(query, token)

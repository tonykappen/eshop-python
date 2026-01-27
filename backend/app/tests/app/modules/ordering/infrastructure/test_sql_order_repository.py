"""Tests for SQL Order repository implementation."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ordering.domain.entities.order.order import Order
from app.modules.ordering.domain.value_objects import Address, Payment
from app.modules.ordering.infrastructure.persistence.orm.orders.order_orm import (
    OrderORM,
)
from app.modules.ordering.infrastructure.persistence.repositories.orders.sql_order_repository import (
    SqlOrderRepository,
)


class TestOrderRepositoryGetById:
    """Test get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self) -> None:
        """Test successful get order by ID."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlOrderRepository(mock_session)

        order_id = uuid4()
        mock_orm = MagicMock(spec=OrderORM)
        mock_orm.id = order_id
        mock_orm.items = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm
        mock_session.execute.return_value = mock_result

        with patch.object(repo, "_orm_to_domain") as mock_mapper:
            mock_order = MagicMock(spec=Order)
            mock_order.id = order_id
            mock_mapper.return_value = mock_order

            result = await repo.get_by_id(order_id)

            assert result == mock_order
            mock_session.execute.assert_called_once()
            mock_mapper.assert_called_once_with(mock_orm)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found_returns_none(self) -> None:
        """Test get by ID when order not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlOrderRepository(mock_session)

        order_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id(order_id)

        assert result is None
        mock_session.execute.assert_called_once()


class TestOrderRepositoryAdd:
    """Test add method."""

    @pytest.mark.asyncio
    async def test_add_success(self) -> None:
        """Test successful order addition."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlOrderRepository(mock_session)

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

        with patch.object(repo, "_domain_to_orm") as mock_mapper:
            mock_orm = MagicMock(spec=OrderORM)
            mock_mapper.return_value = mock_orm

            await repo.add(order)

            mock_mapper.assert_called_once_with(order)
            mock_session.add.assert_called_once_with(mock_orm)


class TestOrderRepositoryGetAll:
    """Test get_all method."""

    @pytest.mark.asyncio
    async def test_get_all_success(self) -> None:
        """Test successful get all orders with pagination."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlOrderRepository(mock_session)

        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 10
        mock_session.execute.return_value = mock_count_result

        # Mock orders result
        mock_orm1 = MagicMock(spec=OrderORM)
        mock_orm1.id = uuid4()
        mock_orm2 = MagicMock(spec=OrderORM)
        mock_orm2.id = uuid4()

        mock_orders_result = MagicMock()
        mock_orders_result.scalars.return_value.all.return_value = [
            mock_orm1,
            mock_orm2,
        ]

        # Setup execute to return different results for count and orders
        async def execute_side_effect(stmt: Any) -> Any:
            if "count" in str(stmt).lower() or "func.count" in str(stmt):
                return mock_count_result
            return mock_orders_result

        mock_session.execute.side_effect = execute_side_effect

        with patch.object(repo, "_orm_to_domain") as mock_mapper:
            mock_order1 = MagicMock(spec=Order)
            mock_order2 = MagicMock(spec=Order)
            mock_mapper.side_effect = [mock_order1, mock_order2]

            orders, total = await repo.get_all(skip=0, take=10)

            assert len(orders) == 2
            assert total == 10
            assert mock_mapper.call_count == 2

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self) -> None:
        """Test get all with pagination parameters."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlOrderRepository(mock_session)

        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 25
        mock_session.execute.return_value = mock_count_result

        # Mock empty orders for second page
        mock_orders_result = MagicMock()
        mock_orders_result.scalars.return_value.all.return_value = []

        async def execute_side_effect(stmt: Any) -> Any:
            if "count" in str(stmt).lower() or "func.count" in str(stmt):
                return mock_count_result
            return mock_orders_result

        mock_session.execute.side_effect = execute_side_effect

        with patch.object(repo, "_orm_to_domain"):
            orders, total = await repo.get_all(skip=10, take=10)

            assert len(orders) == 0
            assert total == 25


class TestOrderRepositoryRemove:
    """Test remove method."""

    @pytest.mark.asyncio
    async def test_remove_success(self) -> None:
        """Test successful order removal."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlOrderRepository(mock_session)

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

        with patch.object(repo, "_domain_to_orm") as mock_mapper:
            mock_orm = MagicMock(spec=OrderORM)
            mock_mapper.return_value = mock_orm

            await repo.remove(order)

            mock_mapper.assert_called_once_with(order)
            mock_session.delete.assert_called_once_with(mock_orm)


class TestOrderRepositorySaveChanges:
    """Test save_changes_async method."""

    @pytest.mark.asyncio
    async def test_save_changes_success(self) -> None:
        """Test successful save changes."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlOrderRepository(mock_session)

        mock_session.commit = AsyncMock()

        await repo.save_changes_async()

        mock_session.commit.assert_called_once()

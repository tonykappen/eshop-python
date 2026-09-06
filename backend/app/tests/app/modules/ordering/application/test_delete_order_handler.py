"""Tests for DeleteOrderHandler."""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from app.core.mediator.cancellation import CancellationToken
from app.modules.ordering.application.features.orders.command.delete_order.delete_order_command import (
    DeleteOrderCommand, DeleteOrderResult)
from app.modules.ordering.application.features.orders.command.delete_order.delete_order_handler import \
    DeleteOrderHandler
from app.modules.ordering.domain.exceptions.order import OrderNotFoundException


class TestDeleteOrderHandler:
    """Test DeleteOrderHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        """Test successful order deletion."""
        mock_repository = AsyncMock()
        handler = DeleteOrderHandler(repository=mock_repository)

        order_id = uuid4()

        # Mock order found
        mock_order = MagicMock()
        mock_order.id = order_id
        mock_repository.get_by_id.return_value = mock_order
        mock_repository.remove = AsyncMock()
        mock_repository.save_changes_async = AsyncMock()

        command = DeleteOrderCommand(order_id=order_id)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, DeleteOrderResult)
        assert result.is_success is True
        mock_repository.get_by_id.assert_called_once_with(order_id)
        mock_repository.remove.assert_called_once_with(mock_order)
        mock_repository.save_changes_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_order_not_found_raises_error(self) -> None:
        """Test that order not found raises error."""
        mock_repository = AsyncMock()
        handler = DeleteOrderHandler(repository=mock_repository)

        order_id = uuid4()

        # Mock order not found
        mock_repository.get_by_id.return_value = None

        command = DeleteOrderCommand(order_id=order_id)
        token = CancellationToken()

        with pytest.raises(OrderNotFoundException):
            await handler.handle(command, token)

    @pytest.mark.asyncio
    async def test_handle_missing_order_id_raises_error(self) -> None:
        """Test that missing order ID raises validation error."""
        # Note: DeleteOrderCommand requires UUID, so we test the validator directly
        from app.modules.ordering.application.features.orders.command.delete_order.delete_order_handler import \
            DeleteOrderCommandValidator

        validator = DeleteOrderCommandValidator()
        # Create a command with None order_id using type ignore for testing
        command = DeleteOrderCommand(order_id=None)  # type: ignore[arg-type]
        errors = validator.validate(command)
        assert "OrderId is required" in errors

    @pytest.mark.asyncio
    async def test_handle_cancellation(self) -> None:
        """Test that cancellation is checked."""
        mock_repository = AsyncMock()
        handler = DeleteOrderHandler(repository=mock_repository)

        order_id = uuid4()
        command = DeleteOrderCommand(order_id=order_id)
        token = CancellationToken()
        token.cancel()

        from app.core.mediator.cancellation import CancellationError

        with pytest.raises(CancellationError):
            await handler.handle(command, token)

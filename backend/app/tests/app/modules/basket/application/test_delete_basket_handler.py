"""Tests for DeleteBasketHandler."""

from unittest.mock import AsyncMock

import pytest

from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_command import (
    DeleteBasketCommand,
    DeleteBasketResult,
)
from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_handler import (
    DeleteBasketHandler,
)


class TestDeleteBasketHandler:
    """Test DeleteBasketHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        """Test successful basket deletion."""
        mock_repository = AsyncMock()
        handler = DeleteBasketHandler(repository=mock_repository)

        user_name = "testuser"
        mock_repository.delete_basket = AsyncMock()

        command = DeleteBasketCommand(user_name=user_name)
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert isinstance(result, DeleteBasketResult)
        assert result.is_success is True
        mock_repository.delete_basket.assert_called_once_with(user_name)

    @pytest.mark.asyncio
    async def test_handle_cancellation(self) -> None:
        """Test that cancellation is checked."""
        mock_repository = AsyncMock()
        handler = DeleteBasketHandler(repository=mock_repository)

        user_name = "testuser"
        command = DeleteBasketCommand(user_name=user_name)
        token = CancellationToken()
        token.cancel()

        from app.core.mediator.cancellation import CancellationError

        with pytest.raises(CancellationError):
            await handler.handle(command, token)

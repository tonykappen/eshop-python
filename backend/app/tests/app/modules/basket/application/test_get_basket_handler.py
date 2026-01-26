"""Tests for GetBasketHandler."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.features.basket.query.get_basket.get_basket_handler import (
    GetBasketHandler,
)
from app.modules.basket.application.features.basket.query.get_basket.get_basket_query import (
    GetBasketQuery,
    GetBasketResult,
)


class TestGetBasketHandler:
    """Test GetBasketHandler."""

    @pytest.mark.asyncio
    async def test_handle_success(self):
        """Test successful basket retrieval."""
        mock_repository = AsyncMock()
        handler = GetBasketHandler(repository=mock_repository)

        # Mock basket with items
        mock_basket = MagicMock()
        mock_basket.id = uuid4()
        mock_basket.user_name = "testuser"
        mock_item = MagicMock()
        mock_item.id = uuid4()
        mock_item.shopping_cart_id = mock_basket.id
        mock_item.product_id = uuid4()
        mock_item.quantity = 2
        mock_item.color = "Red"
        mock_item.price = Decimal("10.99")
        mock_item.product_name = "Test Product"
        mock_basket.items = [mock_item]

        mock_repository.get_basket.return_value = mock_basket

        query = GetBasketQuery(user_name="testuser")
        token = CancellationToken()

        result = await handler.handle(query, token)

        assert isinstance(result, GetBasketResult)
        assert result.shopping_cart.user_name == "testuser"
        assert len(result.shopping_cart.items) == 1
        mock_repository.get_basket.assert_called_once_with("testuser", as_no_tracking=True)

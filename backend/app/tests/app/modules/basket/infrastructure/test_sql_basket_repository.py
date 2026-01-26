"""Tests for SQL Basket repository implementation."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.basket.domain.entities.basket import ShoppingCart
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.basket.infrastructure.persistence.orm.basket.shopping_cart_orm import (
    ShoppingCartORM,
)
from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import (
    SqlBasketRepository,
)


class TestBasketRepositoryGetBasket:
    """Test get_basket method."""

    @pytest.mark.asyncio
    async def test_get_basket_success(self):
        """Test successful get basket."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlBasketRepository(mock_session)

        user_name = "testuser"
        mock_orm = MagicMock(spec=ShoppingCartORM)
        mock_orm.id = uuid4()
        mock_orm.user_name = user_name
        mock_orm.items = []

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm
        mock_session.execute.return_value = mock_result

        with patch.object(repo, "_orm_to_domain", new_callable=AsyncMock) as mock_mapper:
            mock_basket = MagicMock(spec=ShoppingCart)
            mock_mapper.return_value = mock_basket

            result = await repo.get_basket(user_name)

            assert result == mock_basket
            mock_session.execute.assert_called_once()
            mock_mapper.assert_called_once_with(mock_orm)

    @pytest.mark.asyncio
    async def test_get_basket_not_found_raises_exception(self):
        """Test get basket when basket not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlBasketRepository(mock_session)

        user_name = "testuser"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(BasketNotFoundException):
            await repo.get_basket(user_name)


class TestBasketRepositoryCreateBasket:
    """Test create_basket method."""

    @pytest.mark.asyncio
    async def test_create_basket_success(self):
        """Test successful basket creation."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlBasketRepository(mock_session)

        basket = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")

        with patch.object(repo, "_domain_to_orm") as mock_mapper:
            mock_orm = MagicMock(spec=ShoppingCartORM)
            mock_orm.id = basket.id
            mock_orm.items = []  # Mock items to avoid lazy loading issues
            mock_mapper.return_value = mock_orm

            # Mock the execute call that reloads the basket after flush
            mock_result = MagicMock()
            mock_result.scalar_one.return_value = mock_orm
            mock_session.execute.return_value = mock_result

            with patch.object(repo, "_orm_to_domain", new_callable=AsyncMock) as mock_domain_mapper:
                mock_domain_mapper.return_value = basket

                result = await repo.create_basket(basket)

                assert result == basket
                mock_session.add.assert_called_once()
                mock_session.flush.assert_called_once()
                # Verify that execute was called to reload the basket with relationships
                assert mock_session.execute.call_count == 1


class TestBasketRepositoryDeleteBasket:
    """Test delete_basket method."""

    @pytest.mark.asyncio
    async def test_delete_basket_success(self):
        """Test successful basket deletion."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlBasketRepository(mock_session)

        user_name = "testuser"
        basket = ShoppingCart.create(cart_id=uuid4(), user_name=user_name)

        # Mock get_basket to return a basket
        mock_repo_get = AsyncMock(return_value=basket)
        repo.get_basket = mock_repo_get

        # Mock session.get to return ORM
        mock_orm = MagicMock(spec=ShoppingCartORM)
        mock_session.get.return_value = mock_orm

        result = await repo.delete_basket(user_name)

        assert result is True
        mock_session.delete.assert_called_once()
        mock_session.flush.assert_called_once()

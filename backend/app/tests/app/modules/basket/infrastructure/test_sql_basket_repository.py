"""Tests for SQL Basket repository implementation."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from app.modules.basket.domain.entities.basket import ShoppingCart
from app.modules.basket.domain.exceptions.basket import BasketNotFoundException
from app.modules.basket.infrastructure.persistence.orm.basket.shopping_cart_orm import \
    ShoppingCartORM
from app.modules.basket.infrastructure.persistence.repositories.basket import (
    sql_basket_repository,
)
from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import (
    SqlBasketRepository,
)


class RecordingAsyncSession:
    """Test double for AsyncSession without unittest.mock Mock markers."""

    def __init__(self) -> None:
        self.execute = AsyncMock()
        self.add = MagicMock()
        self.flush = AsyncMock()
        self.delete = AsyncMock()
        self.get = AsyncMock()
        self.identity_map = MagicMock(values=MagicMock(return_value=[]))


class FakeBasketORM:
    def __init__(self, user_name: str) -> None:
        self.id = uuid4()
        self.user_name = user_name
        self.items = []


class FakeExecuteResult:
    def __init__(self, orm: FakeBasketORM | None) -> None:
        self._orm = orm

    def scalar_one_or_none(self) -> FakeBasketORM | None:
        return self._orm

    def scalar_one(self) -> FakeBasketORM:
        if self._orm is None:
            raise AssertionError("expected ORM")
        return self._orm


class TestExtractValue:
    @pytest.mark.asyncio
    async def test_returns_plain_values(self) -> None:
        assert await sql_basket_repository._extract_value("hello") == "hello"
        assert await sql_basket_repository._extract_value(None) is None

    @pytest.mark.asyncio
    async def test_awaits_coroutine(self) -> None:
        async def inner() -> str:
            return "done"

        assert await sql_basket_repository._extract_value(inner()) == "done"


class TestBasketRepositoryGetBasket:
    """Test get_basket method."""

    @pytest.mark.asyncio
    async def test_get_basket_success(self) -> None:
        session = RecordingAsyncSession()
        repo = SqlBasketRepository(session)

        user_name = "testuser"
        fake_orm = FakeBasketORM(user_name)
        session.execute.return_value = FakeExecuteResult(fake_orm)

        with patch.object(
            repo, "_orm_to_domain", new_callable=AsyncMock
        ) as mock_mapper:
            mock_basket = ShoppingCart.create(cart_id=fake_orm.id, user_name=user_name)
            mock_mapper.return_value = mock_basket

            result = await repo.get_basket(user_name)

            assert result == mock_basket
            session.execute.assert_called_once()
            mock_mapper.assert_called_once_with(fake_orm)

    @pytest.mark.asyncio
    async def test_get_basket_not_found_raises_exception(self) -> None:
        session = RecordingAsyncSession()
        repo = SqlBasketRepository(session)

        mock_result = FakeExecuteResult(None)
        session.execute.return_value = mock_result

        with pytest.raises(BasketNotFoundException):
            await repo.get_basket("missing-user")


class TestBasketRepositoryCreateBasket:
    @pytest.mark.asyncio
    async def test_create_basket_success(self) -> None:
        session = RecordingAsyncSession()
        repo = SqlBasketRepository(session)
        basket = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")

        with patch.object(repo, "_domain_to_orm") as mock_mapper:
            fake_orm = FakeBasketORM(basket.user_name)
            fake_orm.id = basket.id
            mock_mapper.return_value = fake_orm
            session.get = AsyncMock(return_value=fake_orm)

            with patch.object(
                repo, "_orm_to_domain", new_callable=AsyncMock
            ) as mock_domain_mapper:
                mock_domain_mapper.return_value = basket
                result = await repo.create_basket(basket)

                assert result == basket
                session.add.assert_called_once()
                session.flush.assert_called_once()


class TestBasketRepositoryDeleteBasket:
    @pytest.mark.asyncio
    async def test_delete_basket_success(self) -> None:
        session = RecordingAsyncSession()
        repo = SqlBasketRepository(session)
        user_name = "testuser"
        basket = ShoppingCart.create(cart_id=uuid4(), user_name=user_name)

        repo.get_basket = AsyncMock(return_value=basket)  # type: ignore[method-assign]

        session.get = AsyncMock(return_value=FakeBasketORM(user_name))

        result = await repo.delete_basket(user_name)

        assert result is True
        session.delete.assert_awaited_once()


class TestBasketRepositoryAddItems:
    @pytest.mark.asyncio
    async def test_add_items_to_basket_appends_new_item(self) -> None:
        session = RecordingAsyncSession()
        repo = SqlBasketRepository(session)
        basket = ShoppingCart.create(cart_id=uuid4(), user_name="buyer")
        product_id = uuid4()
        basket.add_item(
            product_id=product_id,
            product_name="Gadget",
            price=Decimal("5.00"),
            quantity=1,
            color="Default",
        )

        fake_orm = FakeBasketORM(basket.user_name)
        fake_orm.id = basket.id
        session.execute.return_value = FakeExecuteResult(fake_orm)

        with patch.object(
            repo, "_orm_to_domain", new_callable=AsyncMock
        ) as mock_mapper:
            mock_mapper.return_value = basket
            result = await repo.add_items_to_basket(basket)
            assert result == basket
            session.flush.assert_awaited()

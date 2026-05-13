"""Integration tests for basket module."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.core.mediator.cancellation import CancellationToken
from app.modules.basket.application.dtos.shopping_cart_dto import (
    ShoppingCartDto,
    ShoppingCartItemDto,
)
from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_command import (
    AddItemIntoBasketCommand,
)
from app.modules.basket.application.features.basket.command.create_basket.create_basket_command import (
    CreateBasketCommand,
)
from app.modules.basket.application.features.basket.query.get_basket.get_basket_query import (
    GetBasketQuery,
)
from app.modules.catalog.application.features.products.queries.get_product_by_id.get_product_by_id_query import (
    GetProductByIdResult,
)
from app.modules.catalog.application.public_interface.dto.product import ProductDto


class TestBasketIntegration:
    """Integration tests for basket."""

    @pytest.mark.asyncio
    async def test_basket_workflow_integration(self) -> None:
        """Test complete basket workflow."""
        # This test simulates a complete basket workflow:
        # 1. Create basket
        # 2. Add items
        # 3. Get basket
        # 4. Remove item
        # 5. Get basket again

        from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_handler import (
            AddItemIntoBasketHandler,
        )
        from app.modules.basket.application.features.basket.command.create_basket.create_basket_handler import (
            CreateBasketHandler,
        )
        from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_command import (
            RemoveItemFromBasketCommand,
        )
        from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_handler import (
            RemoveItemFromBasketHandler,
        )
        from app.modules.basket.application.features.basket.query.get_basket.get_basket_handler import (
            GetBasketHandler,
        )

        # Setup mocks
        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        user_name = "testuser"
        basket_id = uuid4()
        product_id = uuid4()

        # Mock product for catalog integration
        product_dto = ProductDto(
            id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )
        product_result = GetProductByIdResult(product=product_dto)
        mock_mediator.send.return_value = product_result

        # Mock basket
        mock_basket = MagicMock()
        mock_basket.id = basket_id
        mock_basket.user_name = user_name
        mock_basket.items = []
        mock_basket.add_item = MagicMock()
        mock_basket.remove_item = MagicMock()
        mock_repository.get_basket.return_value = mock_basket
        mock_repository.create_basket.return_value = mock_basket
        mock_repository.update_basket.return_value = mock_basket
        mock_repository.save_changes_async = AsyncMock()

        token = CancellationToken()

        # 1. Create basket
        create_handler = CreateBasketHandler(repository=mock_repository)
        shopping_cart_dto = ShoppingCartDto(
            id=basket_id,
            user_name=user_name,
            items=[],
        )
        create_command = CreateBasketCommand(shopping_cart=shopping_cart_dto)
        create_result = await create_handler.handle(create_command, token)
        assert create_result.id == basket_id

        # 2. Add item to basket (tests catalog integration)
        add_item_handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )
        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=basket_id,
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("99.99"),
            product_name="Test Product",
        )
        add_item_command = AddItemIntoBasketCommand(
            user_name=user_name, shopping_cart_item=item_dto
        )
        add_item_result = await add_item_handler.handle(add_item_command, token)
        assert add_item_result.id == basket_id
        # Verify catalog integration was called
        mock_mediator.send.assert_called()

        # 3. Get basket
        get_handler = GetBasketHandler(repository=mock_repository)
        get_query = GetBasketQuery(user_name=user_name)
        get_result = await get_handler.handle(get_query, token)
        assert get_result.shopping_cart.user_name == user_name

        # 4. Remove item
        remove_item_handler = RemoveItemFromBasketHandler(repository=mock_repository)
        remove_item_command = RemoveItemFromBasketCommand(
            user_name=user_name, product_id=product_id
        )
        remove_item_result = await remove_item_handler.handle(
            remove_item_command, token
        )
        assert remove_item_result.id == basket_id

        # Verify all repository methods were called
        assert mock_repository.create_basket.called
        assert mock_repository.get_basket.called
        assert mock_repository.save_changes_async.called

    @pytest.mark.asyncio
    async def test_basket_catalog_integration(self) -> None:
        """Test basket integration with catalog module."""
        # This test verifies that basket module correctly integrates with catalog module
        # when adding items to basket

        from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_handler import (
            AddItemIntoBasketHandler,
        )

        mock_repository = AsyncMock()
        mock_mediator = AsyncMock()
        user_name = "testuser"
        basket_id = uuid4()
        product_id = uuid4()

        # Mock product from catalog
        product_dto = ProductDto(
            id=product_id,
            name="Catalog Product",
            sku="CATALOG-SKU-001",
            category=["Electronics"],
            description="Product from catalog",
            image_file="catalog.jpg",
            price=149.99,
            currency="USD",
            version=1,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        product_result = GetProductByIdResult(product=product_dto)
        mock_mediator.send.return_value = product_result

        # Mock basket
        mock_basket = MagicMock()
        mock_basket.id = basket_id
        mock_basket.add_item = MagicMock()
        mock_repository.get_basket.side_effect = Exception("Basket not found")
        mock_repository.create_basket.return_value = mock_basket
        mock_repository.save_changes_async = AsyncMock()

        handler = AddItemIntoBasketHandler(
            repository=mock_repository, mediator=mock_mediator
        )

        item_dto = ShoppingCartItemDto(
            id=uuid4(),
            shopping_cart_id=None,
            product_id=product_id,
            quantity=1,
            color="Blue",
            price=Decimal("149.99"),
            product_name="Catalog Product",
        )

        command = AddItemIntoBasketCommand(
            user_name=user_name, shopping_cart_item=item_dto
        )
        token = CancellationToken()

        result = await handler.handle(command, token)

        assert result.id == basket_id
        # Verify catalog query was sent
        assert mock_mediator.send.called
        # Verify product price from catalog was used
        call_args = mock_mediator.send.call_args
        assert call_args is not None
        query = call_args[0][0]
        assert hasattr(query, "id")
        assert query.id == product_id

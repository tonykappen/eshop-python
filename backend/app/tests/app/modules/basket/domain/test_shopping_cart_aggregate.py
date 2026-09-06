"""Tests for ShoppingCart aggregate root."""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.modules.basket.domain.entities.basket.shopping_cart import \
    ShoppingCart


class TestShoppingCartCreation:
    """Test ShoppingCart creation."""

    def test_create_shopping_cart_success(self) -> None:
        """Test successful shopping cart creation."""
        cart_id = uuid4()
        user_name = "testuser"

        cart = ShoppingCart.create(cart_id=cart_id, user_name=user_name)

        assert cart.id == cart_id
        assert cart.user_name == user_name
        assert len(cart.items) == 0
        assert cart.total_price == Decimal("0")

    def test_create_shopping_cart_empty_user_name_raises_error(self) -> None:
        """Test that empty user name raises error."""
        cart_id = uuid4()

        with pytest.raises(ValueError, match="User name is required"):
            ShoppingCart.create(cart_id=cart_id, user_name="")


class TestShoppingCartAddItem:
    """Test adding items to shopping cart."""

    def test_add_item_success(self) -> None:
        """Test successfully adding an item."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")
        product_id = uuid4()

        cart.add_item(
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        assert len(cart.items) == 1
        item = cart.items[0]
        assert item.product_id == product_id
        assert item.quantity == 2
        assert item.color == "Red"
        assert item.price == Decimal("10.99")
        assert item.product_name == "Test Product"
        assert cart.total_price == Decimal("21.98")

    def test_add_item_increments_existing_item(self) -> None:
        """Test that adding existing item increments quantity."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")
        product_id = uuid4()

        cart.add_item(
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        cart.add_item(
            product_id=product_id,
            quantity=3,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5
        assert cart.total_price == Decimal("54.95")

    def test_add_item_zero_quantity_raises_error(self) -> None:
        """Test that zero quantity raises error."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")

        with pytest.raises(ValueError, match="Quantity must be greater than 0"):
            cart.add_item(
                product_id=uuid4(),
                quantity=0,
                color="Red",
                price=Decimal("10.99"),
                product_name="Test Product",
            )

    def test_add_item_zero_price_raises_error(self) -> None:
        """Test that zero price raises error."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")

        with pytest.raises(ValueError, match="Price must be greater than 0"):
            cart.add_item(
                product_id=uuid4(),
                quantity=1,
                color="Red",
                price=Decimal("0"),
                product_name="Test Product",
            )


class TestShoppingCartRemoveItem:
    """Test removing items from shopping cart."""

    def test_remove_item_success(self) -> None:
        """Test successfully removing an item."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")
        product_id = uuid4()

        cart.add_item(
            product_id=product_id,
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        cart.remove_item(product_id)

        assert len(cart.items) == 0
        assert cart.total_price == Decimal("0")

    def test_remove_nonexistent_item_no_op(self) -> None:
        """Test that removing nonexistent item is a no-op."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")
        product_id = uuid4()

        # Remove item that doesn't exist - should not raise error
        cart.remove_item(product_id)

        assert len(cart.items) == 0


class TestShoppingCartTotalPrice:
    """Test total price calculation."""

    def test_total_price_multiple_items(self) -> None:
        """Test total price with multiple items."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")

        cart.add_item(
            product_id=uuid4(),
            quantity=2,
            color="Red",
            price=Decimal("10.99"),
            product_name="Product 1",
        )

        cart.add_item(
            product_id=uuid4(),
            quantity=1,
            color="Blue",
            price=Decimal("5.50"),
            product_name="Product 2",
        )

        expected_total = Decimal("10.99") * 2 + Decimal("5.50") * 1
        assert cart.total_price == expected_total

    def test_total_price_empty_cart(self) -> None:
        """Test total price for empty cart."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")
        assert cart.total_price == Decimal("0")


class TestShoppingCartVersion:
    """Test version incrementing."""

    def test_version_increments_on_add_item(self) -> None:
        """Test that version increments when adding item."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")
        initial_version = cart.version

        cart.add_item(
            product_id=uuid4(),
            quantity=1,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        assert cart.version == initial_version + 1

    def test_version_increments_on_remove_item(self) -> None:
        """Test that version increments when removing item."""
        cart = ShoppingCart.create(cart_id=uuid4(), user_name="testuser")
        product_id = uuid4()

        cart.add_item(
            product_id=product_id,
            quantity=1,
            color="Red",
            price=Decimal("10.99"),
            product_name="Test Product",
        )

        initial_version = cart.version
        cart.remove_item(product_id)

        assert cart.version == initial_version + 1

"""Tests for legacy Product aggregate."""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.modules.catalog.domain.entities.product.product_legacy import Product


class TestLegacyProduct:
    def test_create_product_via_constructor(self) -> None:
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Widget",
            category=["tools"],
            description="A useful widget",
            image_file="widget.png",
            price=Decimal("19.99"),
        )
        assert product.id == product_id
        assert product.name == "Widget"

    def test_validators_reject_empty_name(self) -> None:
        with pytest.raises(ValueError):
            Product(
                id=uuid4(),
                name="  ",
                category=["tools"],
                description="desc",
                image_file="img.png",
                price=Decimal("1.00"),
            )

    def test_change_price(self) -> None:
        product = Product(
            id=uuid4(),
            name="Widget",
            category=["tools"],
            description="desc",
            image_file="img.png",
            price=Decimal("10.00"),
        )
        product.change_price(Decimal("12.50"))
        assert product.price == Decimal("12.50")

    def test_update_and_categories(self) -> None:
        product = Product(
            id=uuid4(),
            name="Widget",
            category=["tools"],
            description="desc",
            image_file="img.png",
            price=Decimal("10.00"),
        )
        product.add_category("hardware")
        assert "hardware" in product.category
        product.update(
            name="Updated",
            category=["tools", "hardware"],
            description="updated desc",
            image_file="img2.png",
            price=Decimal("15.00"),
        )
        assert product.name == "Updated"
        assert product.price == Decimal("15.00")

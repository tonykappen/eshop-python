"""Tests for Product aggregate root."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.catalog.domain.domain_events.products.product_created_domain_event import (
    ProductCreatedDomainEvent,
)
from app.modules.catalog.domain.domain_events.products.product_deleted_domain_event import (
    ProductDeletedDomainEvent,
)
from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import (
    ProductPriceChangedDomainEvent,
)
from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.value_objects import Money


class TestProductCreation:
    """Test Product creation."""

    def test_create_product_success(self):
        """Test successful product creation."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=price,
        )

        assert product.id == product_id
        assert product.name == "Test Product"
        assert str(product.sku) == "TEST-001"
        assert product.category == ["Electronics"]
        assert product.description == "A test product"
        assert product.image_file == "test.jpg"
        assert product.price == price

        # Check domain event was added
        domain_events = product.domain_events_copy
        assert len(domain_events) == 1
        assert isinstance(domain_events[0], ProductCreatedDomainEvent)
        assert domain_events[0].product == product

    def test_create_product_without_image(self):
        """Test product creation without image file."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-002",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        assert product.image_file == ""

    def test_create_product_validation_name_empty(self):
        """Test product creation fails with empty name."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        with pytest.raises(ValueError, match="Product name cannot be empty"):
            Product.create(
                product_id=product_id,
                name="",
                sku="TEST-003",
                category=["Electronics"],
                description="A test product",
                price=price,
            )

    def test_create_product_validation_description_empty(self):
        """Test product creation fails with empty description."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        with pytest.raises(ValueError, match="Product description cannot be empty"):
            Product.create(
                product_id=product_id,
                name="Test Product",
                sku="TEST-004",
                category=["Electronics"],
                description="",
                price=price,
            )

    def test_create_product_validation_no_categories(self):
        """Test product creation fails with no categories."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        with pytest.raises(ValueError, match="Product must have at least one category"):
            Product.create(
                product_id=product_id,
                name="Test Product",
                sku="TEST-005",
                category=[],
                description="A test product",
                price=price,
            )

    def test_create_product_validation_empty_categories(self):
        """Test product creation fails with empty category strings."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        with pytest.raises(
            ValueError, match="Product must have at least one valid category"
        ):
            Product.create(
                product_id=product_id,
                name="Test Product",
                sku="TEST-006",
                category=["", "  "],
                description="A test product",
                price=price,
            )

    def test_create_product_cleans_category_whitespace(self):
        """Test product creation cleans category whitespace."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-007",
            category=["  Electronics  ", "  Computers  "],
            description="A test product",
            price=price,
        )

        assert product.category == ["Electronics", "Computers"]


class TestProductUpdate:
    """Test Product update operations."""

    def test_update_product_success(self):
        """Test successful product update."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-008",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        old_version = product.version
        new_price = Money(amount=Decimal("89.99"), currency="USD")

        product.update(
            name="Updated Product",
            category=["Electronics", "Sale"],
            description="Updated description",
            image_file="updated.jpg",
            price=new_price,
        )

        assert product.name == "Updated Product"
        assert product.category == ["Electronics", "Sale"]
        assert product.description == "Updated description"
        assert product.image_file == "updated.jpg"
        assert product.price == new_price
        assert product.version > old_version

        # Check price change domain event was added
        domain_events = product.domain_events_copy
        price_change_events = [
            e for e in domain_events if isinstance(e, ProductPriceChangedDomainEvent)
        ]
        assert len(price_change_events) == 1
        assert price_change_events[0].product == product

    def test_update_product_no_price_change(self):
        """Test product update without price change doesn't emit price change event."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-009",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        # Clear initial domain events
        product.clear_domain_events()

        product.update(
            name="Updated Product",
            category=["Electronics"],
            description="Updated description",
            price=price,  # Same price
        )

        # Check no price change event was added
        domain_events = product.domain_events_copy
        price_change_events = [
            e for e in domain_events if isinstance(e, ProductPriceChangedDomainEvent)
        ]
        assert len(price_change_events) == 0


class TestProductPriceChange:
    """Test Product price change operations."""

    def test_change_price_success(self):
        """Test successful price change."""
        product_id = uuid4()
        old_price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-010",
            category=["Electronics"],
            description="A test product",
            price=old_price,
        )

        # Clear initial domain events
        product.clear_domain_events()

        new_price = Money(amount=Decimal("89.99"), currency="USD")
        product.change_price(new_price)

        assert product.price == new_price

        # Check price change domain event was added
        domain_events = product.domain_events_copy
        assert len(domain_events) == 1
        assert isinstance(domain_events[0], ProductPriceChangedDomainEvent)
        assert domain_events[0].product == product

    def test_change_price_validation_zero(self):
        """Test price change fails with zero price."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-011",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        zero_price = Money(amount=Decimal("0"), currency="USD")

        with pytest.raises(ValueError, match="Product price must be positive"):
            product.change_price(zero_price)


class TestProductCategories:
    """Test Product category operations."""

    def test_add_category_success(self):
        """Test successful category addition."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-012",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        old_version = product.version
        product.add_category("Sale")

        assert "Sale" in product.category
        assert product.version > old_version

    def test_add_category_duplicate(self):
        """Test adding duplicate category doesn't add it again."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-013",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        product.add_category("Electronics")

        assert product.category.count("Electronics") == 1

    def test_remove_category_success(self):
        """Test successful category removal."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-014",
            category=["Electronics", "Sale"],
            description="A test product",
            price=price,
        )

        old_version = product.version
        product.remove_category("Sale")

        assert "Sale" not in product.category
        assert "Electronics" in product.category
        assert product.version > old_version

    def test_remove_category_last_category(self):
        """Test removing last category fails."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-015",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        with pytest.raises(ValueError, match="Product must have at least one category"):
            product.remove_category("Electronics")

    def test_update_categories_success(self):
        """Test successful category update."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-016",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        old_version = product.version
        product.update_categories(["Electronics", "Computers", "Sale"])

        assert product.category == ["Electronics", "Computers", "Sale"]
        assert product.version > old_version


class TestProductDeactivation:
    """Test Product deactivation."""

    def test_deactivate_product_success(self):
        """Test successful product deactivation."""
        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")

        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-017",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        # Clear initial domain events
        product.clear_domain_events()

        product.deactivate()

        # Check deactivation domain event was added
        domain_events = product.domain_events_copy
        assert len(domain_events) == 1
        assert isinstance(domain_events[0], ProductDeletedDomainEvent)
        assert domain_events[0].product == product

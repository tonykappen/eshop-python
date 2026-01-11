"""Comprehensive tests for Catalog domain models."""

from decimal import Decimal
from uuid import uuid4

import pytest

from app.modules.catalog.domain.domain_events.products.product_created_domain_event import (
    ProductCreatedDomainEvent,
)
from app.modules.catalog.domain.domain_events.products.product_price_changed_domain_event import (
    ProductPriceChangedDomainEvent,
)
from app.modules.catalog.domain.entities.product.product import Product


class TestProduct:
    """Test Product domain model."""

    def test_product_creation(self):
        """Test basic product creation."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        assert product.id == product_id
        assert product.name == "Test Product"
        assert product.category == ["Electronics"]
        assert product.description == "A test product"
        assert product.image_file == "test.jpg"
        assert product.price == Decimal("99.99")

    def test_product_creation_with_multiple_categories(self):
        """Test product creation with multiple categories."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics", "Smartphones"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        assert product.category == ["Electronics", "Smartphones"]

    def test_product_creation_with_empty_category(self):
        """Test product creation with empty category list."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=[],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        assert product.category == []

    def test_product_name_validation_empty(self):
        """Test that empty product name raises validation error."""
        product_id = uuid4()

        with pytest.raises(ValueError, match="Product name cannot be empty"):
            Product.create(
                product_id=product_id,
                name="",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("99.99"),
            )

    def test_product_name_validation_whitespace(self):
        """Test that whitespace-only product name raises validation error."""
        product_id = uuid4()

        with pytest.raises(ValueError, match="Product name cannot be empty"):
            Product.create(
                product_id=product_id,
                name="   ",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("99.99"),
            )

    def test_product_name_validation_trims_whitespace(self):
        """Test that product name is trimmed of whitespace."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="  Test Product  ",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        assert product.name == "Test Product"

    def test_product_price_validation_zero(self):
        """Test that zero price raises validation error."""
        product_id = uuid4()

        with pytest.raises(ValueError, match="Input should be greater than 0"):
            Product.create(
                product_id=product_id,
                name="Test Product",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("0"),
            )

    def test_product_price_validation_negative(self):
        """Test that negative price raises validation error."""
        product_id = uuid4()

        with pytest.raises(ValueError, match="Input should be greater than 0"):
            Product.create(
                product_id=product_id,
                name="Test Product",
                category=["Electronics"],
                description="A test product",
                image_file="test.jpg",
                price=Decimal("-10"),
            )

    def test_product_creation_adds_domain_event(self):
        """Test that product creation adds a ProductCreatedEvent."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        assert len(product.domain_events) == 1
        event = product.domain_events[0]
        assert isinstance(event, ProductCreatedEvent)
        assert event.product == product

    def test_product_update_success(self):
        """Test successfully updating product details."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Old Name",
            category=["Old Category"],
            description="Old description",
            image_file="old.jpg",
            price=Decimal("99.99"),
        )

        # Clear domain events from creation
        product.clear_domain_events()

        product.update(
            name="New Name",
            category=["New Category"],
            description="New description",
            image_file="new.jpg",
            price=Decimal("149.99"),
        )

        assert product.name == "New Name"
        assert product.category == ["New Category"]
        assert product.description == "New description"
        assert product.image_file == "new.jpg"
        assert product.price == Decimal("149.99")

    def test_product_update_same_price_no_event(self):
        """Test that updating with same price doesn't add price change event."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        # Clear domain events from creation
        product.clear_domain_events()

        product.update(
            name="Updated Name",
            category=["Electronics"],
            description="Updated description",
            image_file="updated.jpg",
            price=Decimal("99.99"),  # Same price
        )

        # Should not have any domain events since price didn't change
        assert len(product.domain_events) == 0

    def test_product_update_different_price_adds_event(self):
        """Test that updating with different price adds price change event."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        # Clear domain events from creation
        product.clear_domain_events()

        product.update(
            name="Updated Name",
            category=["Electronics"],
            description="Updated description",
            image_file="updated.jpg",
            price=Decimal("149.99"),  # Different price
        )

        # Should have a price change event
        assert len(product.domain_events) == 1
        event = product.domain_events[0]
        assert isinstance(event, ProductPriceChangedEvent)
        assert event.product == product

    def test_product_update_multiple_price_changes(self):
        """Test multiple price changes add multiple events."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        # Clear domain events from creation
        product.clear_domain_events()

        # First price change
        product.update(
            name="Updated Name",
            category=["Electronics"],
            description="Updated description",
            image_file="updated.jpg",
            price=Decimal("149.99"),
        )

        # Second price change
        product.update(
            name="Updated Name",
            category=["Electronics"],
            description="Updated description",
            image_file="updated.jpg",
            price=Decimal("199.99"),
        )

        # Should have two price change events
        assert len(product.domain_events) == 2
        assert all(
            isinstance(event, ProductPriceChangedEvent)
            for event in product.domain_events
        )

    def test_product_equality(self):
        """Test product equality based on ID."""
        product_id1 = uuid4()
        product_id2 = uuid4()

        product1 = Product.create(
            product_id=product_id1,
            name="Product 1",
            category=["Electronics"],
            description="Product 1",
            image_file="product1.jpg",
            price=Decimal("99.99"),
        )

        product2 = Product.create(
            product_id=product_id2,
            name="Product 2",
            category=["Electronics"],
            description="Product 2",
            image_file="product2.jpg",
            price=Decimal("149.99"),
        )

        # Different products should not be equal
        assert product1 != product2

        # Same product should be equal to itself
        assert product1 == product1

    def test_product_serialization(self):
        """Test product serialization."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics", "Smartphones"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        product_dict = product.model_dump()
        assert product_dict["id"] == product_id
        assert product_dict["name"] == "Test Product"
        assert product_dict["category"] == ["Electronics", "Smartphones"]
        assert product_dict["description"] == "A test product"
        assert product_dict["image_file"] == "test.jpg"
        assert product_dict["price"] == Decimal("99.99")

    def test_product_copy(self):
        """Test product copying."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        product_copy = product.model_copy()

        # Should be equal but different objects
        assert product == product_copy
        assert product is not product_copy

        # Should have same values
        assert product_copy.name == "Test Product"
        assert product_copy.category == ["Electronics"]
        assert product_copy.description == "A test product"
        assert product_copy.image_file == "test.jpg"
        assert product_copy.price == Decimal("99.99")

    def test_product_inherits_entity_functionality(self):
        """Test that Product inherits Entity functionality."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        # Test domain events functionality
        assert hasattr(product, "add_domain_event")
        assert hasattr(product, "clear_domain_events")
        assert hasattr(product, "domain_events_copy")

        # Test that it's an aggregate (has version)
        assert hasattr(product, "version")
        assert product.version == 1

    def test_product_version_increment(self):
        """Test that Product version increments properly."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        # Initial version should be 1
        assert product.version == 1

        # Update should increment version
        product.update(
            name="Updated Name",
            category=["Electronics"],
            description="Updated description",
            image_file="updated.jpg",
            price=Decimal("149.99"),
        )

        assert product.version == 2

    def test_product_domain_events_immutability(self):
        """Test that domain events list is immutable."""
        product_id = uuid4()
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            category=["Electronics"],
            description="A test product",
            image_file="test.jpg",
            price=Decimal("99.99"),
        )

        # Should have one event from creation
        assert len(product.domain_events) == 1

        # Getting domain_events_copy should return a copy
        events_copy = product.domain_events_copy
        assert events_copy is not product.domain_events
        assert len(events_copy) == len(product.domain_events)

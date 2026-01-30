"""Tests for catalog integration events V1."""

from datetime import datetime
from uuid import uuid4

import pytest

from app.modules.catalog.contracts.products.integration_events.v1.product_created_integration_event import (
    ProductCreatedIntegrationEventV1,
)
from app.modules.catalog.contracts.products.integration_events.v1.product_deleted_integration_event import (
    ProductDeletedIntegrationEvent,
)
from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import (
    ProductPriceChangedIntegrationEventV1,
)


class TestProductCreatedIntegrationEventV1:
    """Test ProductCreatedIntegrationEventV1."""

    def test_create_event_success(self):
        """Test successful event creation."""
        product_id = uuid4()

        event = ProductCreatedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-001",
            product_categories=["Electronics"],
            product_description="A test product",
            product_image_file="test.jpg",
            product_price_amount=99.99,
            product_price_currency="USD",
        )

        assert event.product_id == product_id
        assert event.product_name == "Test Product"
        assert event.product_sku == "TEST-001"
        assert event.product_categories == ["Electronics"]
        assert event.product_description == "A test product"
        assert event.product_image_file == "test.jpg"
        assert event.product_price_amount == 99.99
        assert event.product_price_currency == "USD"
        assert event.event_type == "product.created.v1"
        assert event.event_version == "1.0"
        assert event.source == "catalog-service"
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_create_event_with_metadata(self):
        """Test event creation with metadata."""
        product_id = uuid4()
        metadata = {"key": "value", "source": "test"}

        event = ProductCreatedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-002",
            product_categories=["Electronics"],
            product_description="A test product",
            product_image_file="",
            product_price_amount=99.99,
            metadata=metadata,
        )

        assert event.metadata == metadata

    def test_create_event_with_empty_image(self):
        """Test event creation with empty image file."""
        product_id = uuid4()

        event = ProductCreatedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-003",
            product_categories=["Electronics"],
            product_description="A test product",
            product_image_file="",
            product_price_amount=99.99,
        )

        assert event.product_image_file == ""

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        product_id = uuid4()

        event = ProductCreatedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-004",
            product_categories=["Electronics"],
            product_description="A test product",
            product_image_file="test.jpg",
            product_price_amount=99.99,
        )

        data = event.to_dict()

        assert data["product_id"] == str(product_id)
        assert data["product_name"] == "Test Product"
        assert data["product_sku"] == "TEST-004"
        assert data["product_categories"] == ["Electronics"]
        assert data["product_price_amount"] == 99.99
        assert data["event_type"] == "product.created.v1"
        assert "event_id" in data
        assert "occurred_at" in data


class TestProductPriceChangedIntegrationEventV1:
    """Test ProductPriceChangedIntegrationEventV1."""

    def test_create_event_success(self):
        """Test successful event creation."""
        product_id = uuid4()

        event = ProductPriceChangedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-001",
            old_price_amount=99.99,
            new_price_amount=89.99,
            price_currency="USD",
        )

        assert event.product_id == product_id
        assert event.product_name == "Test Product"
        assert event.product_sku == "TEST-001"
        assert event.old_price_amount == 99.99
        assert event.new_price_amount == 89.99
        assert event.price_currency == "USD"
        assert event.event_type == "product.price_changed.v1"
        assert event.event_version == "1.0"
        assert event.price_change_percentage is not None

    def test_price_change_percentage_calculation(self):
        """Test price change percentage calculation."""
        product_id = uuid4()

        event = ProductPriceChangedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-002",
            old_price_amount=100.0,
            new_price_amount=90.0,
        )

        # 10% decrease
        assert event.price_change_percentage == pytest.approx(-10.0, rel=0.01)

    def test_price_increase_percentage(self):
        """Test price increase percentage calculation."""
        product_id = uuid4()

        event = ProductPriceChangedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-003",
            old_price_amount=100.0,
            new_price_amount=110.0,
        )

        # 10% increase
        assert event.price_change_percentage == pytest.approx(10.0, rel=0.01)

    def test_price_change_with_zero_old_price(self):
        """Test price change when old price is zero."""
        product_id = uuid4()

        event = ProductPriceChangedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-004",
            old_price_amount=0.0,
            new_price_amount=99.99,
        )

        # Should handle zero old price gracefully
        assert event.price_change_percentage == 0.0

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        product_id = uuid4()

        event = ProductPriceChangedIntegrationEventV1.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-005",
            old_price_amount=99.99,
            new_price_amount=89.99,
        )

        data = event.to_dict()

        assert data["product_id"] == str(product_id)
        assert data["old_price_amount"] == 99.99
        assert data["new_price_amount"] == 89.99
        assert data["price_change_percentage"] == pytest.approx(-10.0, rel=0.01)
        assert data["event_type"] == "product.price_changed.v1"


class TestProductDeletedIntegrationEvent:
    """Test ProductDeletedIntegrationEvent."""

    def test_create_event_success(self):
        """Test successful event creation."""
        product_id = uuid4()
        deleted_at = datetime.utcnow()

        event = ProductDeletedIntegrationEvent.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-001",
            deleted_at=deleted_at,
            deletion_reason="No longer available",
        )

        assert event.product_id == product_id
        assert event.product_name == "Test Product"
        assert event.product_sku == "TEST-001"
        assert event.deleted_at == deleted_at
        assert event.deletion_reason == "No longer available"
        assert event.event_type == "product.deleted.v1"
        assert event.event_version == "1.0"
        assert event.source == "catalog-service"

    def test_create_event_without_reason(self):
        """Test event creation without deletion reason."""
        product_id = uuid4()

        event = ProductDeletedIntegrationEvent.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-002",
        )

        assert event.deletion_reason is None
        assert event.deleted_at is not None  # Should default to now

    def test_create_event_with_metadata(self):
        """Test event creation with metadata."""
        product_id = uuid4()
        metadata = {"deleted_by": "admin", "reason_code": "DISCONTINUED"}

        event = ProductDeletedIntegrationEvent.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-003",
            metadata=metadata,
        )

        assert event.metadata == metadata

    def test_event_to_dict(self):
        """Test event serialization to dictionary."""
        product_id = uuid4()
        deleted_at = datetime.utcnow()

        event = ProductDeletedIntegrationEvent.create(
            product_id=product_id,
            product_name="Test Product",
            product_sku="TEST-004",
            deleted_at=deleted_at,
            deletion_reason="Test deletion",
        )

        data = event.to_dict()

        assert data["product_id"] == str(product_id)
        assert data["product_name"] == "Test Product"
        assert data["product_sku"] == "TEST-004"
        assert data["deletion_reason"] == "Test deletion"
        assert data["event_type"] == "product.deleted.v1"
        assert "deleted_at" in data
        assert "occurred_at" in data


class TestIntegrationEventConsistency:
    """Test integration event consistency and metadata."""

    def test_all_events_have_consistent_metadata(self):
        """Test that all integration events have consistent metadata structure."""
        product_id = uuid4()

        events = [
            ProductCreatedIntegrationEventV1.create(
                product_id=product_id,
                product_name="Test",
                product_sku="TEST-001",
                product_categories=["Electronics"],
                product_description="Test",
                product_image_file="",
                product_price_amount=99.99,
            ),
            ProductPriceChangedIntegrationEventV1.create(
                product_id=product_id,
                product_name="Test",
                product_sku="TEST-001",
                old_price_amount=99.99,
                new_price_amount=89.99,
            ),
            ProductDeletedIntegrationEvent.create(
                product_id=product_id,
                product_name="Test",
                product_sku="TEST-001",
            ),
        ]

        for event in events:
            # All events should have consistent metadata structure
            assert hasattr(event, "event_id")
            assert hasattr(event, "event_type")
            assert hasattr(event, "event_version")
            assert hasattr(event, "occurred_at")
            assert hasattr(event, "source")
            assert hasattr(event, "metadata")
            assert event.source == "catalog-service"
            assert event.event_version == "1.0"
            assert event.event_id is not None
            assert event.occurred_at is not None

    def test_all_events_serializable(self):
        """Test that all events can be serialized to dict."""
        product_id = uuid4()

        events = [
            ProductCreatedIntegrationEventV1.create(
                product_id=product_id,
                product_name="Test",
                product_sku="TEST-001",
                product_categories=["Electronics"],
                product_description="Test",
                product_image_file="",
                product_price_amount=99.99,
            ),
            ProductPriceChangedIntegrationEventV1.create(
                product_id=product_id,
                product_name="Test",
                product_sku="TEST-001",
                old_price_amount=99.99,
                new_price_amount=89.99,
            ),
            ProductDeletedIntegrationEvent.create(
                product_id=product_id,
                product_name="Test",
                product_sku="TEST-001",
            ),
        ]

        for event in events:
            data = event.to_dict()
            assert isinstance(data, dict)
            assert "event_id" in data
            assert "event_type" in data
            assert "occurred_at" in data

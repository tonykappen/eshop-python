"""Tests for catalog integration events."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from eshop.modules.catalog.domain.integration_events import (
    CustomRoutingEvent,
    ProductCreatedIntegrationEvent,
    ProductDiscontinuedIntegrationEvent,
    ProductInventoryUpdatedIntegrationEvent,
    ProductPriceChangedIntegrationEvent,
    create_integration_event_from_domain,
)


class TestProductCreatedIntegrationEvent:
    """Test ProductCreatedIntegrationEvent."""

    def test_product_created_event_creation(self) -> None:
        """Test creating a product created integration event."""
        product_id = uuid4()
        category_id = uuid4()

        event = ProductCreatedIntegrationEvent(
            product_id=product_id,
            product_name="Test Product",
            price=99.99,
            category_id=category_id,
        )

        assert event.product_id == product_id
        assert event.product_name == "Test Product"
        assert event.price == 99.99
        assert event.category_id == category_id
        assert event.event_type == "product_created_integration"
        assert event.topic == "eshop.catalog.product_created_integration"
        assert event.routing_key == "eshop.catalog.product_created_integration"
        assert event.source_module == "catalog"

    def test_product_created_event_without_category(self) -> None:
        """Test creating a product created event without category."""
        product_id = uuid4()

        event = ProductCreatedIntegrationEvent(
            product_id=product_id,
            product_name="Test Product",
            price=99.99,
        )

        assert event.product_id == product_id
        assert event.product_name == "Test Product"
        assert event.price == 99.99
        assert event.category_id is None

    def test_product_created_event_validation(self) -> None:
        """Test product created event validation."""
        product_id = uuid4()

        # Should raise validation error for missing required fields
        with pytest.raises(ValidationError):
            ProductCreatedIntegrationEvent(
                product_id=product_id,
                # Missing product_name and price
            )

    def test_product_created_event_serialization(self) -> None:
        """Test product created event serialization."""
        product_id = uuid4()
        category_id = uuid4()

        event = ProductCreatedIntegrationEvent(
            product_id=product_id,
            product_name="Test Product",
            price=99.99,
            category_id=category_id,
        )

        # Test model dump
        data = event.model_dump()
        assert data["product_id"] == product_id
        assert data["product_name"] == "Test Product"
        assert data["price"] == 99.99
        assert data["category_id"] == category_id
        assert data["event_type"] == "product_created_integration"


class TestProductPriceChangedIntegrationEvent:
    """Test ProductPriceChangedIntegrationEvent."""

    def test_price_changed_event_creation(self) -> None:
        """Test creating a price changed integration event."""
        product_id = uuid4()

        event = ProductPriceChangedIntegrationEvent(
            product_id=product_id,
            old_price=99.99,
            new_price=89.99,
            price_change_reason="Sale discount",
        )

        assert event.product_id == product_id
        assert event.old_price == 99.99
        assert event.new_price == 89.99
        assert event.price_change_reason == "Sale discount"
        assert event.event_type == "product_price_changed_integration"
        assert event.topic == "eshop.catalog.product_price_changed_integration"
        assert event.routing_key == "eshop.catalog.product_price_changed_integration"

    def test_price_changed_event_without_reason(self) -> None:
        """Test creating a price changed event without reason."""
        product_id = uuid4()

        event = ProductPriceChangedIntegrationEvent(
            product_id=product_id,
            old_price=99.99,
            new_price=89.99,
        )

        assert event.product_id == product_id
        assert event.old_price == 99.99
        assert event.new_price == 89.99
        assert event.price_change_reason is None

    def test_price_changed_event_validation(self) -> None:
        """Test price changed event validation."""
        product_id = uuid4()

        # Should raise validation error for missing required fields
        with pytest.raises(ValidationError):
            ProductPriceChangedIntegrationEvent(
                product_id=product_id,
                old_price=99.99,
                # Missing new_price
            )


class TestProductInventoryUpdatedIntegrationEvent:
    """Test ProductInventoryUpdatedIntegrationEvent."""

    def test_inventory_updated_event_creation(self) -> None:
        """Test creating an inventory updated integration event."""
        product_id = uuid4()
        warehouse_id = uuid4()

        event = ProductInventoryUpdatedIntegrationEvent(
            product_id=product_id,
            old_quantity=100,
            new_quantity=85,
            warehouse_id=warehouse_id,
        )

        assert event.product_id == product_id
        assert event.old_quantity == 100
        assert event.new_quantity == 85
        assert event.warehouse_id == warehouse_id
        assert event.event_type == "product_inventory_updated_integration"
        assert event.topic == "eshop.catalog.product_inventory_updated_integration"
        assert (
            event.routing_key == "eshop.catalog.product_inventory_updated_integration"
        )

    def test_inventory_updated_event_without_warehouse(self) -> None:
        """Test creating an inventory updated event without warehouse."""
        product_id = uuid4()

        event = ProductInventoryUpdatedIntegrationEvent(
            product_id=product_id,
            old_quantity=100,
            new_quantity=85,
        )

        assert event.product_id == product_id
        assert event.old_quantity == 100
        assert event.new_quantity == 85
        assert event.warehouse_id is None

    def test_inventory_updated_event_validation(self) -> None:
        """Test inventory updated event validation."""
        product_id = uuid4()

        # Should raise validation error for missing required fields
        with pytest.raises(ValidationError):
            ProductInventoryUpdatedIntegrationEvent(
                product_id=product_id,
                old_quantity=100,
                # Missing new_quantity
            )


class TestProductDiscontinuedIntegrationEvent:
    """Test ProductDiscontinuedIntegrationEvent."""

    def test_product_discontinued_event_creation(self) -> None:
        """Test creating a product discontinued integration event."""
        product_id = uuid4()
        replacement_id = uuid4()
        discontinuation_date = "2024-01-15"

        event = ProductDiscontinuedIntegrationEvent(
            product_id=product_id,
            discontinuation_date=discontinuation_date,
            reason="Out of stock permanently",
            replacement_product_id=replacement_id,
        )

        assert event.product_id == product_id
        assert event.discontinuation_date == discontinuation_date
        assert event.reason == "Out of stock permanently"
        assert event.replacement_product_id == replacement_id
        assert event.event_type == "product_discontinued_integration"
        assert event.topic == "eshop.catalog.product_discontinued_integration"
        assert event.routing_key == "eshop.catalog.product_discontinued_integration"

    def test_product_discontinued_event_without_optional_fields(self) -> None:
        """Test creating a discontinued event without optional fields."""
        product_id = uuid4()
        discontinuation_date = "2024-01-15"

        event = ProductDiscontinuedIntegrationEvent(
            product_id=product_id,
            discontinuation_date=discontinuation_date,
        )

        assert event.product_id == product_id
        assert event.discontinuation_date == discontinuation_date
        assert event.reason is None
        assert event.replacement_product_id is None

    def test_product_discontinued_event_validation(self) -> None:
        """Test product discontinued event validation."""
        product_id = uuid4()

        # Should raise validation error for missing required fields
        with pytest.raises(ValidationError):
            ProductDiscontinuedIntegrationEvent(
                product_id=product_id,
                # Missing discontinuation_date
            )


class TestCustomRoutingEvent:
    """Test CustomRoutingEvent."""

    def test_custom_routing_event_creation(self) -> None:
        """Test creating a custom routing event."""
        event = CustomRoutingEvent(
            priority_level="high",
            custom_data={"key": "value"},
        )

        assert event.priority_level == "high"
        assert event.custom_data == {"key": "value"}
        assert event.event_type == "custom_routing"
        assert event.topic == "eshop.catalog.custom_routing"
        # Custom routing pattern should be applied
        assert "custom" in event.routing_key
        assert "priority" in event.routing_key

    def test_custom_routing_event_defaults(self) -> None:
        """Test custom routing event with default values."""
        event = CustomRoutingEvent()

        assert event.priority_level == "normal"
        assert event.custom_data == {}


class TestIntegrationEventHelpers:
    """Test integration event helper functions."""

    def test_create_integration_event_from_domain(self) -> None:
        """Test creating integration event from domain event."""

        # Create a mock domain event with model_dump method
        class MockDomainEvent:
            def __init__(self):
                self.name = "TestEvent"

            def model_dump(self):
                return {"name": self.name}

        domain_event = MockDomainEvent()

        # This should not raise an exception
        integration_event = create_integration_event_from_domain(domain_event)

        # The function should return an IntegrationEvent
        assert integration_event is not None

    def test_integration_event_metadata_consistency(self) -> None:
        """Test that all integration events have consistent metadata."""
        events = [
            ProductCreatedIntegrationEvent(
                product_id=uuid4(),
                product_name="Test",
                price=99.99,
            ),
            ProductPriceChangedIntegrationEvent(
                product_id=uuid4(),
                old_price=99.99,
                new_price=89.99,
            ),
            ProductInventoryUpdatedIntegrationEvent(
                product_id=uuid4(),
                old_quantity=100,
                new_quantity=85,
            ),
            ProductDiscontinuedIntegrationEvent(
                product_id=uuid4(),
                discontinuation_date="2024-01-15",
            ),
        ]

        for event in events:
            # All events should have consistent metadata structure
            assert hasattr(event, "event_type")
            assert hasattr(event, "topic")
            assert hasattr(event, "routing_key")
            assert hasattr(event, "source_module")
            assert event.source_module == "catalog"
            assert event.topic.startswith("eshop.catalog.")
            assert event.routing_key.startswith("eshop.catalog.")


class TestIntegrationEventSerialization:
    """Test integration event serialization and deserialization."""

    def test_product_created_event_round_trip(self) -> None:
        """Test product created event serialization round trip."""
        product_id = uuid4()
        category_id = uuid4()

        original_event = ProductCreatedIntegrationEvent(
            product_id=product_id,
            product_name="Test Product",
            price=99.99,
            category_id=category_id,
        )

        # Serialize
        data = original_event.model_dump()

        # Deserialize
        reconstructed_event = ProductCreatedIntegrationEvent(**data)

        assert reconstructed_event.product_id == original_event.product_id
        assert reconstructed_event.product_name == original_event.product_name
        assert reconstructed_event.price == original_event.price
        assert reconstructed_event.category_id == original_event.category_id
        assert reconstructed_event.event_type == original_event.event_type
        assert reconstructed_event.topic == original_event.topic
        assert reconstructed_event.routing_key == original_event.routing_key

    def test_price_changed_event_round_trip(self) -> None:
        """Test price changed event serialization round trip."""
        product_id = uuid4()

        original_event = ProductPriceChangedIntegrationEvent(
            product_id=product_id,
            old_price=99.99,
            new_price=89.99,
            price_change_reason="Sale discount",
        )

        # Serialize
        data = original_event.model_dump()

        # Deserialize
        reconstructed_event = ProductPriceChangedIntegrationEvent(**data)

        assert reconstructed_event.product_id == original_event.product_id
        assert reconstructed_event.old_price == original_event.old_price
        assert reconstructed_event.new_price == original_event.new_price
        assert (
            reconstructed_event.price_change_reason
            == original_event.price_change_reason
        )


class TestIntegrationEventValidation:
    """Test integration event validation scenarios."""

    def test_invalid_uuid_format(self) -> None:
        """Test validation with invalid UUID format."""
        with pytest.raises(ValidationError):
            ProductCreatedIntegrationEvent(
                product_id="invalid-uuid",
                product_name="Test Product",
                price=99.99,
            )

    def test_negative_price(self) -> None:
        """Test validation with negative price."""
        # Note: Integration events don't have price validation, so this should pass
        event = ProductCreatedIntegrationEvent(
            product_id=uuid4(),
            product_name="Test Product",
            price=-99.99,
        )
        assert event.price == -99.99

    def test_negative_quantity(self) -> None:
        """Test validation with negative quantity."""
        # Note: Integration events don't have quantity validation, so this should pass
        event = ProductInventoryUpdatedIntegrationEvent(
            product_id=uuid4(),
            old_quantity=-100,
            new_quantity=85,
        )
        assert event.old_quantity == -100

    def test_empty_product_name(self) -> None:
        """Test validation with empty product name."""
        # Note: Integration events don't have name validation, so this should pass
        event = ProductCreatedIntegrationEvent(
            product_id=uuid4(),
            product_name="",
            price=99.99,
        )
        assert event.product_name == ""


class TestIntegrationEventEdgeCases:
    """Test integration event edge cases."""

    def test_zero_price(self) -> None:
        """Test event with zero price."""
        event = ProductCreatedIntegrationEvent(
            product_id=uuid4(),
            product_name="Free Product",
            price=0.0,
        )

        assert event.price == 0.0

    def test_zero_quantity(self) -> None:
        """Test event with zero quantity."""
        event = ProductInventoryUpdatedIntegrationEvent(
            product_id=uuid4(),
            old_quantity=100,
            new_quantity=0,
        )

        assert event.new_quantity == 0

    def test_same_price_change(self) -> None:
        """Test price change event with same old and new price."""
        event = ProductPriceChangedIntegrationEvent(
            product_id=uuid4(),
            old_price=99.99,
            new_price=99.99,
        )

        assert event.old_price == event.new_price

    def test_same_quantity_change(self) -> None:
        """Test inventory update with same old and new quantity."""
        event = ProductInventoryUpdatedIntegrationEvent(
            product_id=uuid4(),
            old_quantity=100,
            new_quantity=100,
        )

        assert event.old_quantity == event.new_quantity

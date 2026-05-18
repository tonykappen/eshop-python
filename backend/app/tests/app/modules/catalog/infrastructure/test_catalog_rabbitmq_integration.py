"""Test RabbitMQ messaging integration for catalog module."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from app.core.messaging.event_publisher import (CatalogEventPublisher,
                                                CatalogEventPublisherFactory)


class TestCatalogEventPublisher:
    """Test catalog event publisher functionality."""

    @pytest.fixture
    def event_publisher(self):
        """Create event publisher with mocked broker."""
        with patch(
            "app.modules.catalog.infrastructure.event_publisher.RabbitBroker"
        ) as mock_broker_class:
            mock_broker = AsyncMock()
            mock_broker_class.return_value = mock_broker
            publisher = CatalogEventPublisher()
            publisher.broker = mock_broker
            return publisher

    @pytest.mark.asyncio
    async def test_publish_product_created_event(self, event_publisher):
        """Test publishing product created event."""
        # Arrange
        product_id = uuid4()
        product_name = "Test Product"
        price = 99.99
        category_id = uuid4()
        additional_data = {"description": "Test Description"}

        # Act
        await event_publisher.publish_product_created(
            product_id=product_id,
            product_name=product_name,
            price=price,
            category_id=category_id,
            **additional_data,
        )

        # Assert
        event_publisher.broker.publish.assert_called_once()
        call_args = event_publisher.broker.publish.call_args
        published_data = call_args[0][0]
        routing_key = call_args[1]["routing_key"]
        exchange = call_args[1]["exchange"]

        assert published_data["product_id"] == product_id
        assert published_data["product_name"] == product_name
        assert published_data["price"] == price
        assert published_data["category_id"] == category_id
        assert routing_key == "app.catalog.product_created_integration"
        assert exchange == "catalog.events"

    @pytest.mark.asyncio
    async def test_publish_product_price_changed_event(self, event_publisher):
        """Test publishing product price changed event."""
        # Arrange
        product_id = uuid4()
        old_price = 99.99
        new_price = 89.99
        price_change_reason = "Sale"
        additional_data = {"updated_by": "admin"}

        # Act
        await event_publisher.publish_product_price_changed(
            product_id=product_id,
            old_price=old_price,
            new_price=new_price,
            price_change_reason=price_change_reason,
            **additional_data,
        )

        # Assert
        event_publisher.broker.publish.assert_called_once()
        call_args = event_publisher.broker.publish.call_args
        published_data = call_args[0][0]
        routing_key = call_args[1]["routing_key"]

        assert published_data["product_id"] == product_id
        assert published_data["old_price"] == old_price
        assert published_data["new_price"] == new_price
        assert published_data["price_change_reason"] == price_change_reason
        assert routing_key == "app.catalog.product_price_changed_integration"

    @pytest.mark.asyncio
    async def test_publish_product_inventory_updated_event(self, event_publisher):
        """Test publishing product inventory updated event."""
        # Arrange
        product_id = uuid4()
        old_quantity = 100
        new_quantity = 80
        warehouse_id = uuid4()
        additional_data = {"reason": "sale"}

        # Act
        await event_publisher.publish_product_inventory_updated(
            product_id=product_id,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            warehouse_id=warehouse_id,
            **additional_data,
        )

        # Assert
        event_publisher.broker.publish.assert_called_once()
        call_args = event_publisher.broker.publish.call_args
        published_data = call_args[0][0]
        routing_key = call_args[1]["routing_key"]

        assert published_data["product_id"] == product_id
        assert published_data["old_quantity"] == old_quantity
        assert published_data["new_quantity"] == new_quantity
        assert published_data["warehouse_id"] == warehouse_id
        assert routing_key == "app.catalog.product_inventory_updated_integration"

    @pytest.mark.asyncio
    async def test_publish_product_discontinued_event(self, event_publisher):
        """Test publishing product discontinued event."""
        # Arrange
        product_id = uuid4()
        discontinuation_date = "2024-01-01T00:00:00Z"
        reason = "End of life"
        replacement_product_id = uuid4()
        additional_data = {"discontinued_by": "admin"}

        # Act
        await event_publisher.publish_product_discontinued(
            product_id=product_id,
            discontinuation_date=discontinuation_date,
            reason=reason,
            replacement_product_id=replacement_product_id,
            **additional_data,
        )

        # Assert
        event_publisher.broker.publish.assert_called_once()
        call_args = event_publisher.broker.publish.call_args
        published_data = call_args[0][0]
        routing_key = call_args[1]["routing_key"]

        assert published_data["product_id"] == product_id
        assert published_data["discontinuation_date"] == discontinuation_date
        assert published_data["reason"] == reason
        assert published_data["replacement_product_id"] == replacement_product_id
        assert routing_key == "app.catalog.product_discontinued_integration"

    @pytest.mark.asyncio
    async def test_start_publisher(self, event_publisher):
        """Test starting the event publisher."""
        # Act
        await event_publisher.start()

        # Assert
        event_publisher.broker.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_publisher(self, event_publisher):
        """Test stopping the event publisher."""
        # Act
        await event_publisher.stop()

        # Assert
        event_publisher.broker.close.assert_called_once()


class TestCatalogEventPublisherFactory:
    """Test catalog event publisher factory functionality."""

    def test_get_instance_singleton(self):
        """Test that factory returns singleton instance."""
        # Clear any existing instance
        CatalogEventPublisherFactory._instance = None

        # Act
        instance1 = CatalogEventPublisherFactory.get_instance()
        instance2 = CatalogEventPublisherFactory.get_instance()

        # Assert
        assert instance1 is instance2
        assert isinstance(instance1, CatalogEventPublisher)

    @pytest.mark.asyncio
    async def test_create_and_start(self):
        """Test creating and starting publisher."""
        # Clear any existing instance
        CatalogEventPublisherFactory._instance = None

        with patch(
            "app.modules.catalog.infrastructure.event_publisher.CatalogEventPublisher"
        ) as mock_publisher_class:
            mock_publisher = AsyncMock()
            mock_publisher_class.return_value = mock_publisher

            # Act
            result = await CatalogEventPublisherFactory.create_and_start()

            # Assert
            assert result == mock_publisher
            mock_publisher.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self):
        """Test stopping the publisher."""
        # Arrange
        mock_publisher = AsyncMock()
        CatalogEventPublisherFactory._instance = mock_publisher

        # Act
        await CatalogEventPublisherFactory.stop()

        # Assert
        mock_publisher.stop.assert_called_once()
        assert CatalogEventPublisherFactory._instance is None

    @pytest.mark.asyncio
    async def test_stop_no_instance(self):
        """Test stopping when no instance exists."""
        # Arrange
        CatalogEventPublisherFactory._instance = None

        # Act & Assert - should not raise exception
        await CatalogEventPublisherFactory.stop()


class TestIntegrationEventData:
    """Test integration event data structure."""

    def test_product_created_event_structure(self):
        """Test ProductCreatedIntegrationEvent data structure."""
        from app.modules.catalog.domain.integration_events import \
            ProductCreatedIntegrationEvent

        product_id = uuid4()
        event = ProductCreatedIntegrationEvent(
            product_id=product_id,
            product_name="Test Product",
            price=99.99,
            category_id=uuid4(),
        )

        # Assert auto-generated fields
        assert event.event_type == "product_created_integration"
        assert event.topic == "app.catalog.product_created_integration"
        assert event.routing_key == "app.catalog.product_created_integration"
        assert event.source_module == "catalog"

        # Assert provided fields
        assert event.product_id == product_id
        assert event.product_name == "Test Product"
        assert event.price == 99.99

    def test_product_price_changed_event_structure(self):
        """Test ProductPriceChangedIntegrationEvent data structure."""
        from app.modules.catalog.domain.integration_events import \
            ProductPriceChangedIntegrationEvent

        product_id = uuid4()
        event = ProductPriceChangedIntegrationEvent(
            product_id=product_id,
            old_price=99.99,
            new_price=89.99,
            price_change_reason="Sale",
        )

        # Assert auto-generated fields
        assert event.event_type == "product_price_changed_integration"
        assert event.topic == "app.catalog.product_price_changed_integration"
        assert event.routing_key == "app.catalog.product_price_changed_integration"
        assert event.source_module == "catalog"

        # Assert provided fields
        assert event.product_id == product_id
        assert event.old_price == 99.99
        assert event.new_price == 89.99
        assert event.price_change_reason == "Sale"

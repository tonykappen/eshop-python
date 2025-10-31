"""Event publisher service for catalog integration events."""

from typing import Any
from uuid import UUID

from faststream import FastStream
from faststream.rabbit import RabbitBroker, RabbitMessage

from app.config.settings import settings
from app.core.logging.base_logger import BaseLogger
from app.modules.catalog.domain.integration_events import (
    ProductCreatedIntegrationEvent,
    ProductDiscontinuedIntegrationEvent,
    ProductInventoryUpdatedIntegrationEvent,
    ProductPriceChangedIntegrationEvent,
)

logger = BaseLogger(__name__)


class CatalogEventPublisher:
    """Event publisher for catalog integration events."""

    def __init__(self, broker: RabbitBroker | None = None):
        """Initialize event publisher."""
        self.broker = broker or self._create_broker()
        self.app = FastStream(self.broker)

    def _create_broker(self) -> RabbitBroker:
        """Create RabbitMQ broker with configuration."""
        return RabbitBroker(settings.rabbitmq_connection_string)

    async def publish_product_created(
        self,
        product_id: UUID,
        product_name: str,
        price: float,
        category_id: UUID | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product created integration event."""
        try:
            event = ProductCreatedIntegrationEvent(
                product_id=product_id,
                product_name=product_name,
                price=price,
                category_id=category_id,
                **additional_data,
            )
            
            await self.broker.publish(
                event.model_dump(),
                routing_key=event.routing_key,
                exchange="catalog.events",
            )
            
            logger.info(f"Published ProductCreated event for product {product_id}")
        except Exception as e:
            logger.error(f"Failed to publish ProductCreated event for product {product_id}: {e}")

    async def publish_product_price_changed(
        self,
        product_id: UUID,
        old_price: float,
        new_price: float,
        price_change_reason: str | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product price changed integration event."""
        try:
            event = ProductPriceChangedIntegrationEvent(
                product_id=product_id,
                old_price=old_price,
                new_price=new_price,
                price_change_reason=price_change_reason,
                **additional_data,
            )
            
            await self.broker.publish(
                event.model_dump(),
                routing_key=event.routing_key,
                exchange="catalog.events",
            )
            
            logger.info(f"Published ProductPriceChanged event for product {product_id}")
        except Exception as e:
            logger.error(f"Failed to publish ProductPriceChanged event for product {product_id}: {e}")

    async def publish_product_inventory_updated(
        self,
        product_id: UUID,
        old_quantity: int,
        new_quantity: int,
        warehouse_id: UUID | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product inventory updated integration event."""
        try:
            event = ProductInventoryUpdatedIntegrationEvent(
                product_id=product_id,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                warehouse_id=warehouse_id,
                **additional_data,
            )
            
            await self.broker.publish(
                event.model_dump(),
                routing_key=event.routing_key,
                exchange="catalog.events",
            )
            
            logger.info(f"Published ProductInventoryUpdated event for product {product_id}")
        except Exception as e:
            logger.error(f"Failed to publish ProductInventoryUpdated event for product {product_id}: {e}")

    async def publish_product_discontinued(
        self,
        product_id: UUID,
        discontinuation_date: str,
        reason: str | None = None,
        replacement_product_id: UUID | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product discontinued integration event."""
        try:
            event = ProductDiscontinuedIntegrationEvent(
                product_id=product_id,
                discontinuation_date=discontinuation_date,
                reason=reason,
                replacement_product_id=replacement_product_id,
                **additional_data,
            )
            
            await self.broker.publish(
                event.model_dump(),
                routing_key=event.routing_key,
                exchange="catalog.events",
            )
            
            logger.info(f"Published ProductDiscontinued event for product {product_id}")
        except Exception as e:
            logger.error(f"Failed to publish ProductDiscontinued event for product {product_id}: {e}")

    async def start(self) -> None:
        """Start the event publisher."""
        try:
            await self.broker.start()
            logger.info("Catalog event publisher started")
        except Exception as e:
            logger.error(f"Failed to start catalog event publisher: {e}")
            raise

    async def stop(self) -> None:
        """Stop the event publisher."""
        try:
            await self.broker.close()
            logger.info("Catalog event publisher stopped")
        except Exception as e:
            logger.error(f"Failed to stop catalog event publisher: {e}")


class CatalogEventPublisherFactory:
    """Factory for creating catalog event publishers."""

    _instance: CatalogEventPublisher | None = None

    @classmethod
    def get_instance(cls) -> CatalogEventPublisher:
        """Get singleton instance of event publisher."""
        if cls._instance is None:
            cls._instance = CatalogEventPublisher()
        return cls._instance

    @classmethod
    async def create_and_start(cls) -> CatalogEventPublisher:
        """Create and start event publisher."""
        publisher = cls.get_instance()
        await publisher.start()
        return publisher

    @classmethod
    async def stop(cls) -> None:
        """Stop the event publisher."""
        if cls._instance:
            await cls._instance.stop()
            cls._instance = None

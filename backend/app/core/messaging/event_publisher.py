"""Event publisher service for integration events.

NOTE: This contains CatalogEventPublisher which is catalog-specific.
Other modules should create their own event publishers following this pattern.
"""

from typing import Any
from uuid import UUID

import aio_pika
from faststream import FastStream
from faststream.rabbit import RabbitBroker

from app.config.settings import settings
from app.core.logging.base_logger import BaseLogger

# Integration events are imported directly in the methods that use them
# to avoid circular imports and to use the V1 classes directly

logger = BaseLogger(__name__)


class CatalogEventPublisher:
    """Event publisher for catalog integration events."""

    def __init__(self, broker: RabbitBroker | None = None):
        """Initialize event publisher."""
        self.broker = broker or self._create_broker()
        self.app = FastStream(self.broker)
        self._is_connected = False
        self._exchange_declared = False
        self.exchange_name = "catalog.events"

    def _create_broker(self) -> RabbitBroker:
        """Create RabbitMQ broker with configuration."""
        return RabbitBroker(settings.rabbitmq_connection_string)

    async def _log_connection_event(
        self,
        status: str,
        error: str | None = None,
        outbox_orm_class: Any = None,
        get_session_maker: Any = None,
    ) -> None:
        """
        Log RabbitMQ connection event to outbox table.

        Args:
            status: Connection status (connected, disconnected, failed)
            error: Optional error message
            outbox_orm_class: Optional outbox ORM class (module-specific)
            get_session_maker: Optional session maker function (module-specific)
        """
        # Only log if module-specific dependencies are provided
        if not outbox_orm_class or not get_session_maker:
            logger.debug("Outbox logging skipped - module-specific dependencies not provided")
            return

        try:
            import asyncio
            import json
            from datetime import UTC, datetime
            from uuid import uuid4

            session_maker = get_session_maker()
            async with session_maker() as session:
                try:
                    # Create connection event data
                    event_data = {
                        "event_type": "RabbitMQConnectionEvent",
                        "status": status,
                        "exchange": self.exchange_name,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    if error:
                        event_data["error"] = error

                    # Create outbox record
                    # Use timezone-naive datetime for database (TIMESTAMP WITHOUT TIME ZONE)
                    now_naive = datetime.now(UTC).replace(tzinfo=None)
                    outbox_record = outbox_orm_class(
                        id=uuid4(),
                        event_type="RabbitMQConnectionEvent",
                        event_data=json.dumps(event_data),
                        status="pending",
                        created_at=now_naive,
                    )

                    session.add(outbox_record)
                    await session.commit()

                    logger.debug(
                        f"Logged RabbitMQ connection event to outbox: {status}"
                    )
                except Exception as e:
                    await session.rollback()
                    logger.warning(
                        f"Failed to log RabbitMQ connection event to outbox: {e}"
                    )
        except Exception as e:
            # Don't fail connection if logging fails
            logger.debug(f"Could not log connection event to outbox: {e}")

    async def _ensure_connected(
        self, outbox_orm_class: Any = None, get_session_maker: Any = None
    ) -> None:
        """
        Ensure broker is connected before publishing.

        Args:
            outbox_orm_class: Optional outbox ORM class for logging (module-specific)
            get_session_maker: Optional session maker function for logging (module-specific)
        """
        if not self._is_connected:
            try:
                # Check if broker is already connected (FastStream broker connection state)
                if hasattr(self.broker, "is_connected") and self.broker.is_connected:
                    self._is_connected = True
                else:
                    # Connect the broker
                    await self.broker.connect()
                    self._is_connected = True
                    logger.debug("RabbitMQ broker connected")
                    # Log connection event to outbox if dependencies provided
                    if outbox_orm_class and get_session_maker:
                        import asyncio

                        asyncio.create_task(
                            self._log_connection_event("connected", None, outbox_orm_class, get_session_maker)
                        )
            except Exception as e:
                logger.warning(f"Failed to connect broker: {e}")
                self._is_connected = False
                # Log connection failure to outbox if dependencies provided
                if outbox_orm_class and get_session_maker:
                    import asyncio

                    asyncio.create_task(
                        self._log_connection_event("failed", str(e), outbox_orm_class, get_session_maker)
                    )
                raise

        # Ensure exchange is declared
        await self._ensure_exchange()

    async def _ensure_exchange(self) -> None:
        """Ensure the catalog.events exchange exists.

        Note: FastStream will auto-declare exchanges when publishing.
        We declare it here to ensure it exists with the right configuration
        (topic exchange, durable) before FastStream tries to use it.
        """
        if self._exchange_declared:
            return

        try:
            # Get the connection from the broker after it's connected
            # FastStream broker wraps aio_pika connection
            connection = getattr(self.broker, "_connection", None) or getattr(
                self.broker, "connection", None
            )

            if connection:
                # Create a channel to declare the exchange
                channel = await connection.channel()

                # Declare the exchange as DIRECT exchange (non-durable) to match FastStream's default
                # FastStream auto-declares exchanges as DIRECT when publishing, so we match that behavior
                # This prevents conflicts if the exchange already exists
                exchange = await channel.declare_exchange(
                    self.exchange_name,
                    type=aio_pika.ExchangeType.DIRECT,
                    durable=False,
                    auto_delete=False,
                )

                # Close the channel (broker manages its own channels for publishing)
                await channel.close()

                self._exchange_declared = True
                logger.debug(
                    f"Exchange '{self.exchange_name}' declared as DIRECT (matching FastStream default)"
                )
            else:
                logger.warning("Could not access broker connection to declare exchange")
                # Mark as attempted to avoid infinite retry
                # FastStream will handle it during publish
                self._exchange_declared = True

        except aio_pika.exceptions.ChannelClosed as e:
            # Channel was closed, but exchange might still be declared
            if "406" in str(e) or "precondition_failed" in str(e).lower():
                self._exchange_declared = True
                logger.debug(
                    f"Exchange '{self.exchange_name}' already exists (possibly declared by FastStream)"
                )
            else:
                logger.warning(f"Channel error declaring exchange: {e}")
                self._exchange_declared = True
        except Exception as e:
            # If exchange already exists (406 PRECONDITION_FAILED), that's fine
            error_str = str(e).lower()
            if (
                "already exists" in error_str
                or "406" in error_str
                or "precondition_failed" in error_str
            ):
                self._exchange_declared = True
                logger.debug(f"Exchange '{self.exchange_name}' already exists")
            else:
                logger.warning(
                    f"Could not declare exchange '{self.exchange_name}': {e}. FastStream will handle it during publish."
                )
            # Mark as attempted so we don't retry indefinitely
            self._exchange_declared = True

    async def publish_product_created(
        self,
        product_id: UUID,
        product_name: str,
        price: float,
        category_id: UUID | None = None,
        product_sku: str | None = None,
        product_categories: list[str] | None = None,
        product_description: str | None = None,
        product_image_file: str | None = None,
        product_price_currency: str = "USD",
        **additional_data: Any,
    ) -> None:
        """
        DEPRECATED: ProductCreated events are internal-only and should not be published externally.
        
        Per architecture specification, ProductCreated is an internal-only event.
        External systems must discover products via APIs, not events.
        
        This method is kept for backward compatibility but will not publish events.
        """
        logger.warning(
            f"publish_product_created called for product {product_id} but ProductCreated "
            "events are internal-only and will not be published externally per architecture."
        )
        # Do not publish - ProductCreated is internal-only

    async def publish_product_price_changed(
        self,
        product_id: UUID,
        old_price: float,
        new_price: float,
        price_change_reason: str | None = None,
        product_name: str | None = None,
        product_sku: str | None = None,
        price_currency: str = "USD",
        outbox_orm_class: Any = None,
        get_session_maker: Any = None,
        **additional_data: Any,
    ) -> None:
        """Publish product price changed integration event."""
        try:
            # Ensure broker is connected before publishing
            await self._ensure_connected(outbox_orm_class, get_session_maker)

            # Use the create method from ProductPriceChangedIntegrationEventV1
            # Import the V1 class directly
            from app.modules.catalog.contracts.products.integration_events.v1.product_price_changed_integration_event import (
                ProductPriceChangedIntegrationEventV1,
            )

            event = ProductPriceChangedIntegrationEventV1.create(
                product_id=product_id,
                product_name=product_name or f"Product-{product_id}",
                product_sku=product_sku or f"SKU-{product_id}",
                old_price_amount=old_price,
                new_price_amount=new_price,
                price_currency=price_currency,
                metadata=additional_data,
            )

            event_data = event.model_dump()
            await self.broker.publish(
                event_data,
                routing_key="product.price_changed",
                exchange=self.exchange_name,
            )

            logger.info(
                f"Published ProductPriceChanged event for product {product_id} "
                f"(old_price: {old_price}, new_price: {new_price}, routing_key: product.price_changed, exchange: {self.exchange_name})"
            )
        except Exception as e:
            logger.error(
                f"Failed to publish ProductPriceChanged event for product {product_id}: {e}"
            )

    async def publish_product_inventory_updated(
        self,
        product_id: UUID,
        old_quantity: int,
        new_quantity: int,
        warehouse_id: UUID | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product inventory updated integration event."""
        # TODO: Implement when ProductInventoryUpdatedIntegrationEvent is created
        logger.warning(
            f"ProductInventoryUpdated event not yet implemented for product {product_id}"
        )

    async def publish_product_updated(
        self,
        product_id: UUID,
        product_name: str,
        price: float,
        description: str | None = None,
        category: list[str] | None = None,
        image_file: str | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product updated integration event."""
        # TODO: Implement when ProductUpdatedIntegrationEvent is created
        logger.warning(
            f"ProductUpdated event not yet implemented for product {product_id}"
        )

    async def publish_product_deleted(
        self,
        product_id: UUID,
        product_name: str,
        deleted_at: str,
        reason: str | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product deleted integration event."""
        # TODO: Implement when ProductDeletedIntegrationEvent is created
        logger.warning(
            f"ProductDeleted event not yet implemented for product {product_id}"
        )

    async def publish_product_discontinued(
        self,
        product_id: UUID,
        discontinuation_date: str,
        reason: str | None = None,
        replacement_product_id: UUID | None = None,
        **additional_data: Any,
    ) -> None:
        """Publish product discontinued integration event."""
        # TODO: Implement when ProductDiscontinuedIntegrationEvent is created
        logger.warning(
            f"ProductDiscontinued event not yet implemented for product {product_id}"
        )

    async def start(
        self, outbox_orm_class: Any = None, get_session_maker: Any = None
    ) -> None:
        """
        Start the event publisher.

        Args:
            outbox_orm_class: Optional outbox ORM class for logging (module-specific)
            get_session_maker: Optional session maker function for logging (module-specific)
        """
        try:
            await self.broker.connect()
            self._is_connected = True
            # Declare exchange during startup
            await self._ensure_exchange()
            logger.info("Catalog event publisher started and connected")
            # Log connection event to outbox if dependencies provided
            if outbox_orm_class and get_session_maker:
                import asyncio

                asyncio.create_task(
                    self._log_connection_event("connected", None, outbox_orm_class, get_session_maker)
                )
        except Exception as e:
            logger.error(f"Failed to start catalog event publisher: {e}")
            self._is_connected = False
            # Log connection failure to outbox if dependencies provided
            if outbox_orm_class and get_session_maker:
                import asyncio

                asyncio.create_task(
                    self._log_connection_event("failed", str(e), outbox_orm_class, get_session_maker)
                )
            raise

    async def stop(
        self, outbox_orm_class: Any = None, get_session_maker: Any = None
    ) -> None:
        """
        Stop the event publisher.

        Args:
            outbox_orm_class: Optional outbox ORM class for logging (module-specific)
            get_session_maker: Optional session maker function for logging (module-specific)
        """
        try:
            if self._is_connected and self.broker.is_connected:
                await self.broker.close()
            self._is_connected = False
            logger.info("Catalog event publisher stopped")
            # Log disconnection event to outbox if dependencies provided
            if outbox_orm_class and get_session_maker:
                import asyncio

                asyncio.create_task(
                    self._log_connection_event("disconnected", None, outbox_orm_class, get_session_maker)
                )
        except Exception as e:
            logger.error(f"Failed to stop catalog event publisher: {e}")
            self._is_connected = False


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
    async def create_and_start(
        cls, outbox_orm_class: Any = None, get_session_maker: Any = None
    ) -> CatalogEventPublisher:
        """
        Create and start event publisher.

        Args:
            outbox_orm_class: Optional outbox ORM class for logging (module-specific)
            get_session_maker: Optional session maker function for logging (module-specific)
        """
        publisher = cls.get_instance()
        await publisher.start(outbox_orm_class, get_session_maker)
        return publisher

    @classmethod
    async def stop(
        cls, outbox_orm_class: Any = None, get_session_maker: Any = None
    ) -> None:
        """
        Stop the event publisher.

        Args:
            outbox_orm_class: Optional outbox ORM class for logging (module-specific)
            get_session_maker: Optional session maker function for logging (module-specific)
        """
        if cls._instance:
            await cls._instance.stop(outbox_orm_class, get_session_maker)
            cls._instance = None

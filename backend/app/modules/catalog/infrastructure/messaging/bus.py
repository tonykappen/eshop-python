"""Message bus abstraction for catalog module."""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

try:
    import aio_pika
except ImportError:
    aio_pika = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class IMessageBus(ABC):
    """Interface for message bus."""

    @abstractmethod
    async def publish(self, message: Any, topic: str | None = None) -> None:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish
            topic: Optional topic/channel
        """
        pass

    @abstractmethod
    async def subscribe(self, topic: str, handler: Any) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe to
            handler: Handler function
        """
        pass

    @abstractmethod
    async def unsubscribe(self, topic: str, handler: Any) -> None:
        """
        Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            handler: Handler function
        """
        pass


class InMemoryMessageBus(IMessageBus):
    """In-memory message bus implementation."""

    def __init__(self):
        """Initialize the in-memory message bus."""
        self._subscribers: dict[str, list[Any]] = {}
        self._message_history: list[dict[str, Any]] = []

    async def publish(self, message: Any, topic: str | None = None) -> None:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish
            topic: Optional topic/channel
        """
        topic = topic or "default"

        # Store message in history
        self._message_history.append(
            {
                "topic": topic,
                "message": message,
                "timestamp": None,  # Would be set in real implementation
            }
        )

        # Notify subscribers
        if topic in self._subscribers:
            for handler in self._subscribers[topic]:
                try:
                    if hasattr(handler, "handle"):
                        await handler.handle(message)
                    else:
                        await handler(message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")

        logger.debug(f"Published message to topic '{topic}': {message}")

    async def subscribe(self, topic: str, handler: Any) -> None:
        """
        Subscribe to a topic.

        Args:
            topic: Topic to subscribe to
            handler: Handler function
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []

        self._subscribers[topic].append(handler)
        logger.debug(f"Subscribed handler to topic '{topic}'")

    async def unsubscribe(self, topic: str, handler: Any) -> None:
        """
        Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            handler: Handler function
        """
        if topic in self._subscribers and handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)
            logger.debug(f"Unsubscribed handler from topic '{topic}'")

    def get_message_history(self) -> list[dict[str, Any]]:
        """
        Get message history.

        Returns:
            List of published messages
        """
        return self._message_history.copy()

    def clear_history(self) -> None:
        """Clear message history."""
        self._message_history.clear()


class RabbitMQMessageBus(IMessageBus):
    """RabbitMQ message bus implementation."""

    def __init__(self, connection_string: str):
        """
        Initialize the RabbitMQ message bus.

        Args:
            connection_string: RabbitMQ connection string
        """
        self.connection_string = connection_string
        self._connection = None
        self._channel = None

    async def _log_connection_event(self, status: str, error: str | None = None) -> None:
        """
        Log RabbitMQ connection event to outbox table.

        Args:
            status: Connection status (connected, disconnected, failed)
            error: Optional error message
        """
        try:
            from app.modules.catalog.infrastructure.persistence.db_context import (
                get_session_maker,
            )
            from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import (
                OutboxORM,
            )

            session_maker = get_session_maker()
            async with session_maker() as session:
                try:
                    # Create connection event data
                    event_data = {
                        "event_type": "RabbitMQConnectionEvent",
                        "status": status,
                        "connection_string": self.connection_string.split("@")[
                            -1
                        ],  # Hide credentials
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                    if error:
                        event_data["error"] = error

                    # Create outbox record
                    # Use timezone-naive datetime for database (TIMESTAMP WITHOUT TIME ZONE)
                    now_naive = datetime.now(UTC).replace(tzinfo=None)
                    outbox_record = OutboxORM(
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

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            import aio_pika

            self._connection = await aio_pika.connect_robust(self.connection_string)
            self._channel = await self._connection.channel()

            logger.info("Connected to RabbitMQ")
            # Log connection event to outbox
            asyncio.create_task(self._log_connection_event("connected"))
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            # Log connection failure to outbox
            asyncio.create_task(self._log_connection_event("failed", str(e)))
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._connection:
            await self._connection.close()
            logger.info("Disconnected from RabbitMQ")
            # Log disconnection event to outbox
            asyncio.create_task(self._log_connection_event("disconnected"))

    async def publish(self, message: Any, topic: str | None = None) -> None:
        """
        Publish a message to RabbitMQ.

        Args:
            message: Message to publish
            topic: Optional topic/channel
        """
        # Ensure connection is established
        if not self._connection or not self._channel:
            await self.connect()

        topic = topic or "default"

        try:
            import json

            # Convert message to JSON
            if hasattr(message, "to_dict"):
                message_data = message.to_dict()
            else:
                message_data = str(message)

            message_json = json.dumps(message_data)

            # Publish to exchange
            if aio_pika is None:
                raise ImportError("aio_pika is not installed")
            await self._channel.default_exchange.publish(
                aio_pika.Message(message_json.encode()),
                routing_key=topic,
            )

            logger.debug(f"Published message to RabbitMQ topic '{topic}': {message}")

        except Exception as e:
            logger.error(f"Error publishing message to RabbitMQ: {e}")
            raise

    async def subscribe(self, topic: str, handler: Any) -> None:
        """
        Subscribe to a RabbitMQ topic.

        Args:
            topic: Topic to subscribe to
            handler: Handler function
        """
        if not self._channel:
            await self.connect()

        try:
            import aio_pika

            # Declare queue
            queue = await self._channel.declare_queue(topic, durable=True)

            # Set up consumer
            async def message_handler(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        import json

                        message_data = json.loads(message.body.decode())
                        await handler(message_data)
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

            await queue.consume(message_handler)
            logger.debug(f"Subscribed to RabbitMQ topic '{topic}'")

        except Exception as e:
            logger.error(f"Error subscribing to RabbitMQ topic: {e}")
            raise

    async def unsubscribe(self, topic: str, handler: Any) -> None:
        """
        Unsubscribe from a RabbitMQ topic.

        Args:
            topic: Topic to unsubscribe from
            handler: Handler function
        """
        # RabbitMQ doesn't support direct unsubscribe
        # This would need to be implemented with consumer tags
        logger.warning("RabbitMQ unsubscribe not implemented")

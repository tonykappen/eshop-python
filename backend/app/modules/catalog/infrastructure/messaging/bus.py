"""Message bus abstraction for catalog module."""

import logging
from abc import ABC, abstractmethod
from typing import Any

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

    async def connect(self) -> None:
        """Connect to RabbitMQ."""
        try:
            import aio_pika

            self._connection = await aio_pika.connect_robust(self.connection_string)
            self._channel = await self._connection.channel()

            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        if self._connection:
            await self._connection.close()
            logger.info("Disconnected from RabbitMQ")

    async def publish(self, message: Any, topic: str | None = None) -> None:
        """
        Publish a message to RabbitMQ.

        Args:
            message: Message to publish
            topic: Optional topic/channel
        """
        if not self._channel:
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

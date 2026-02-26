"""Message bus abstraction for messaging infrastructure."""

import asyncio
import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def _message_to_json_serializable(message: Any) -> Any:
    """
    Convert a message payload to a JSON-serializable structure.

    Handles dict, list, Pydantic models (to_dict or model_dump), and str explicitly
    to avoid double serialization (e.g. str(dict) then json.dumps).
    Only falls back to str(message) as a last resort.

    Returns:
        A value that json.dumps() can serialize (dict, list, str, number, bool, None).
    """
    if message is None or isinstance(message, (bool, int, float)):
        return message
    if isinstance(message, dict):
        return message
    if isinstance(message, list):
        return message
    if hasattr(message, "to_dict") and callable(getattr(message, "to_dict")):
        return message.to_dict()
    if hasattr(message, "model_dump") and callable(getattr(message, "model_dump")):
        return message.model_dump(mode="json")
    if isinstance(message, str):
        return message
    # Last resort: string representation (e.g. custom objects without to_dict)
    return str(message)

try:
    import aio_pika
except ImportError:
    aio_pika = None  # type: ignore[assignment]

from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


class IMessageBus(ABC):
    """Interface for message bus."""

    @abstractmethod
    async def publish(self, message: Any, topic: str | None = None, exchange: str | None = None) -> None:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish
            topic: Optional topic/channel (routing key)
            exchange: Optional exchange name (defaults to default exchange)
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

    async def publish(self, message: Any, topic: str | None = None, exchange: str | None = None) -> None:
        """
        Publish a message to the bus.

        Args:
            message: Message to publish
            topic: Optional topic/channel (routing key)
            exchange: Optional exchange name (ignored for in-memory bus)
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
                    logger.log_error_with_context(
                        "Error in message handler",
                        error=e,
                        context={"topic": topic}
                    )

        logger.log_debug_with_context(
            "Published message to topic",
            context={"topic": topic, "message": str(message)}
        )

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
        logger.log_debug_with_context(
            "Subscribed handler to topic",
            context={"topic": topic}
        )

    async def unsubscribe(self, topic: str, handler: Any) -> None:
        """
        Unsubscribe from a topic.

        Args:
            topic: Topic to unsubscribe from
            handler: Handler function
        """
        if topic in self._subscribers and handler in self._subscribers[topic]:
            self._subscribers[topic].remove(handler)
            logger.log_debug_with_context(
                "Unsubscribed handler from topic",
                context={"topic": topic}
            )

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

    async def _log_connection_event(
        self, status: str, error: str | None = None, outbox_orm_class: Any = None, get_session_maker: Any = None
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
            logger.log_debug_with_context(
                "Outbox logging skipped - module-specific dependencies not provided"
            )
            return

        try:
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
                    outbox_record = outbox_orm_class(
                        id=uuid4(),
                        event_type="RabbitMQConnectionEvent",
                        event_data=json.dumps(event_data),
                        status="pending",
                        created_at=now_naive,
                    )

                    session.add(outbox_record)
                    await session.commit()

                    logger.log_debug_with_context(
                        "Logged RabbitMQ connection event to outbox",
                        context={"status": status}
                    )
                except Exception as e:
                    await session.rollback()
                    logger.log_warning_with_context(
                        "Failed to log RabbitMQ connection event to outbox",
                        context={"error": str(e), "status": status}
                    )
        except Exception as e:
            # Don't fail connection if logging fails
            logger.log_debug_with_context(
                "Could not log connection event to outbox",
                context={"error": str(e)}
            )

    async def connect(self, outbox_orm_class: Any = None, get_session_maker: Any = None) -> None:
        """
        Connect to RabbitMQ.

        Args:
            outbox_orm_class: Optional outbox ORM class for logging (module-specific)
            get_session_maker: Optional session maker function for logging (module-specific)
        """
        try:
            import aio_pika

            self._connection = await aio_pika.connect_robust(self.connection_string)
            # When using connect_robust(), channel() automatically returns a RobustChannel
            # RobustChannel will handle automatic restoration when connection is restored
            self._channel = await self._connection.channel()

            logger.log_with_context("Connected to RabbitMQ")
            # Log connection event to outbox if dependencies provided
            if outbox_orm_class and get_session_maker:
                asyncio.create_task(
                    self._log_connection_event("connected", None, outbox_orm_class, get_session_maker)
                )
        except Exception as e:
            logger.log_error_with_context(
                "Failed to connect to RabbitMQ",
                error=e
            )
            # Log connection failure to outbox if dependencies provided
            if outbox_orm_class and get_session_maker:
                asyncio.create_task(
                    self._log_connection_event("failed", str(e), outbox_orm_class, get_session_maker)
                )
            raise

    async def disconnect(self, outbox_orm_class: Any = None, get_session_maker: Any = None) -> None:
        """
        Disconnect from RabbitMQ.

        Args:
            outbox_orm_class: Optional outbox ORM class for logging (module-specific)
            get_session_maker: Optional session maker function for logging (module-specific)
        """
        # Close channel first before closing connection
        if self._channel:
            try:
                # Robust channels should be closed gracefully
                if hasattr(self._channel, 'close') and not (hasattr(self._channel, 'is_closed') and self._channel.is_closed):
                    await self._channel.close()
            except Exception as e:
                logger.log_warning_with_context(
                    "Error closing channel during disconnect",
                    context={"error": str(e)}
                )
            finally:
                self._channel = None
        
        if self._connection:
            try:
                await self._connection.close()
                logger.log_with_context("Disconnected from RabbitMQ")
            except Exception as e:
                logger.log_warning_with_context(
                    "Error closing connection during disconnect",
                    context={"error": str(e)}
                )
            finally:
                self._connection = None
            
            # Log disconnection event to outbox if dependencies provided
            if outbox_orm_class and get_session_maker:
                asyncio.create_task(
                    self._log_connection_event("disconnected", None, outbox_orm_class, get_session_maker)
                )

    async def publish(self, message: Any, topic: str | None = None, exchange: str | None = None) -> None:
        """
        Publish a message to RabbitMQ.

        Args:
            message: Message to publish
            topic: Optional topic/channel (routing key)
            exchange: Optional exchange name (defaults to default exchange)
        """
        # Ensure connection is established and ready
        if not self._connection or not self._channel:
            await self.connect()
        
        # Check if connection is closed and wait for it to be restored
        # Robust connections automatically restore, but we should wait if it's currently closed
        if hasattr(self._connection, 'is_closed') and self._connection.is_closed:
            # Wait a bit for robust connection to restore
            await asyncio.sleep(0.1)
            # If still closed after wait, try to reconnect
            if hasattr(self._connection, 'is_closed') and self._connection.is_closed:
                await self.connect()
        
        # Robust channels automatically restore when connection is restored
        # Just ensure we have a channel reference
        if not self._channel:
            self._channel = await self._connection.channel()

        topic = topic or "default"

        try:
            # Convert message to JSON-serializable form (avoids double serialization for dicts)
            message_data = _message_to_json_serializable(message)
            message_json = json.dumps(message_data)

            # Publish to exchange
            if aio_pika is None:
                raise ImportError("aio_pika is not installed")
            
            if exchange:
                # Try to get existing exchange first (passive=True doesn't create, just checks)
                # If exchange exists, use it as-is to avoid type mismatch errors
                try:
                    exchange_obj = await self._channel.declare_exchange(
                        exchange, aio_pika.ExchangeType.DIRECT, passive=True
                    )
                    logger.log_debug_with_context(
                        "Using existing exchange",
                        context={"exchange": exchange}
                    )
                except Exception:
                    # Exchange doesn't exist, declare it as DIRECT to match CatalogEventPublisher
                    # DIRECT exchange matches FastStream's default behavior
                    exchange_obj = await self._channel.declare_exchange(
                        exchange, aio_pika.ExchangeType.DIRECT, durable=False
                    )
                    logger.log_debug_with_context(
                        "Declared new exchange as DIRECT",
                        context={"exchange": exchange}
                    )
                
                await exchange_obj.publish(
                    aio_pika.Message(message_json.encode()),
                    routing_key=topic,
                )
                logger.log_debug_with_context(
                    "Published message to RabbitMQ exchange",
                    context={"exchange": exchange, "topic": topic, "message": str(message)}
                )
            else:
                # Use default exchange
                await self._channel.default_exchange.publish(
                    aio_pika.Message(message_json.encode()),
                    routing_key=topic,
                )
                logger.log_debug_with_context(
                    "Published message to RabbitMQ topic",
                    context={"topic": topic, "message": str(message)}
                )

        except RuntimeError as e:
            # Handle connection closed errors - robust connection should restore automatically
            if "closed" in str(e).lower():
                logger.log_warning_with_context(
                    "Connection closed during publish, waiting for restoration",
                    context={"topic": topic, "exchange": exchange, "error": str(e)}
                )
                # Wait a bit for robust connection to restore
                await asyncio.sleep(0.5)
                # Retry once after waiting
                try:
                    # Re-ensure connection
                    if not self._connection or (hasattr(self._connection, 'is_closed') and self._connection.is_closed):
                        await self.connect()
                    if not self._channel:
                        self._channel = await self._connection.robust_channel()
                    # Retry the publish operation (simplified - just log for now)
                    # In production, you might want to queue the message for retry
                    logger.log_warning_with_context(
                        "Retry after connection restoration not implemented, message may be lost",
                        context={"topic": topic, "exchange": exchange}
                    )
                except Exception as retry_error:
                    logger.log_error_with_context(
                        "Failed to restore connection for retry",
                        error=retry_error,
                        context={"topic": topic, "exchange": exchange}
                    )
                    raise
            else:
                raise
        except Exception as e:
            logger.log_error_with_context(
                "Error publishing message to RabbitMQ",
                error=e,
                context={"topic": topic, "exchange": exchange}
            )
            raise

    async def subscribe(self, topic: str, handler: Any) -> None:
        """
        Subscribe to a RabbitMQ topic.

        Args:
            topic: Topic to subscribe to
            handler: Handler function
        """
        if not self._connection or not self._channel:
            await self.connect()
        
        # Check if connection is closed and wait for it to be restored
        if hasattr(self._connection, 'is_closed') and self._connection.is_closed:
            import asyncio
            await asyncio.sleep(0.1)
            if self._connection.is_closed:
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
                        logger.log_error_with_context(
                            "Error processing message",
                            error=e,
                            context={"topic": topic}
                        )

            await queue.consume(message_handler)
            logger.log_debug_with_context(
                "Subscribed to RabbitMQ topic",
                context={"topic": topic}
            )

        except Exception as e:
            logger.log_error_with_context(
                "Error subscribing to RabbitMQ topic",
                error=e,
                context={"topic": topic}
            )
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
        logger.log_warning_with_context("RabbitMQ unsubscribe not implemented")

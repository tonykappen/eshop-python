"""Background publisher for basket outbox table."""

import asyncio
import json
import logging
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.core.messaging.bus import RabbitMQMessageBus
from app.core.messaging.exchange_resolver import get_exchange_for_event_type
from app.core.messaging.outbox import OutboxMessage, OutboxMessageStatus
from app.modules.basket.infrastructure.persistence.db_context import get_session_maker
from app.modules.basket.infrastructure.persistence.orm.basket.outbox_orm import (
    OutboxORM,
    OutboxMessageStatus as BasketOutboxMessageStatus,
)

logger = logging.getLogger(__name__)


_basket_message_bus: RabbitMQMessageBus | None = None


def _get_basket_message_bus() -> RabbitMQMessageBus:
    """Return the singleton RabbitMQ bus used by the basket outbox publisher."""
    global _basket_message_bus
    if _basket_message_bus is None:
        _basket_message_bus = RabbitMQMessageBus(settings.rabbitmq_connection_string)
    return _basket_message_bus


class BasketOutboxPublisherWorker:
    """Background worker for publishing basket outbox messages."""

    def __init__(
        self,
        message_bus=None,
        batch_size: int = 10,
        poll_interval: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Initialize the basket outbox publisher worker.

        Args:
            message_bus: Message bus for publishing (defaults to shared message bus)
            batch_size: Number of messages to process in each batch
            poll_interval: Interval between polls in seconds
            max_retries: Maximum number of retries for failed messages
        """
        self.message_bus = message_bus or _get_basket_message_bus()
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.is_running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the outbox publisher worker."""
        if self.is_running:
            logger.warning("Basket outbox publisher worker is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Basket outbox publisher worker started")

    async def stop(self) -> None:
        """Stop the outbox publisher worker."""
        if not self.is_running:
            logger.warning("Basket outbox publisher worker is not running")
            return

        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Basket outbox publisher worker stopped")

    async def _run_loop(self) -> None:
        """Main worker loop."""
        logger.info("Basket outbox publisher worker loop started")

        while self.is_running:
            try:
                await self._process_pending_messages()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                logger.info("Basket outbox publisher worker loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in basket outbox publisher worker loop: {e}")
                await asyncio.sleep(self.poll_interval)

        logger.info("Basket outbox publisher worker loop ended")

    async def _process_pending_messages(self) -> None:
        """Process pending messages from outbox."""
        try:
            session_maker = get_session_maker()
            async with session_maker() as session:
                # Get pending messages
                pending_messages = await self._get_pending_messages(session)

                if not pending_messages:
                    return

                # Process each message
                for message_orm in pending_messages:
                    try:
                        await self._process_message(session, message_orm)
                    except Exception as e:
                        logger.error(
                            f"Error processing message {message_orm.id}: {e}",
                            exc_info=True
                        )
                        # Continue with next message
                        continue

                # Commit changes
                await session.commit()

        except Exception as e:
            logger.error(
                f"Error processing pending basket outbox messages: {e}",
                exc_info=True
            )

    async def _get_pending_messages(self, session: AsyncSession) -> list[OutboxORM]:
        """
        Get pending messages from basket outbox.

        Args:
            session: Database session

        Returns:
            List of pending outbox messages
        """
        stmt = (
            select(OutboxORM)
            .where(
                OutboxORM.status == BasketOutboxMessageStatus.PENDING,
                OutboxORM.retry_count < self.max_retries,
            )
            .order_by(OutboxORM.created_at.asc())
            .limit(self.batch_size)
        )

        result = await session.execute(stmt)
        return result.scalars().all()

    async def _process_message(
        self, session: AsyncSession, message_orm: OutboxORM
    ) -> None:
        """
        Process a single outbox message.

        Args:
            session: Database session
            message_orm: Outbox message ORM
        """
        try:
            # Mark as processing
            await self._mark_as_processing(session, message_orm.id)
            await session.flush()

            # Parse event_data from JSON string
            try:
                if isinstance(message_orm.event_data, str):
                    event_data = json.loads(message_orm.event_data)
                else:
                    event_data = message_orm.event_data
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse event_data for message {message_orm.id}: {e}")
                await self._mark_as_failed(
                    session, message_orm.id, f"Failed to parse event_data: {e}"
                )
                await session.flush()
                return

            # Reconstruct the event object from the event_data
            try:
                from decimal import Decimal
                from uuid import UUID
                from app.modules.basket.application.integration_events.basket.basket_checkout_integration_event import (
                    BasketCheckoutIntegrationEvent,
                )
                
                # Convert string UUIDs and Decimals back to proper types
                if isinstance(event_data, dict):
                    if 'customer_id' in event_data and isinstance(event_data['customer_id'], str):
                        try:
                            event_data['customer_id'] = UUID(event_data['customer_id'])
                        except (ValueError, AttributeError):
                            pass
                    
                    if 'total_price' in event_data:
                        if isinstance(event_data['total_price'], str):
                            try:
                                event_data['total_price'] = Decimal(event_data['total_price'])
                            except (ValueError, AttributeError):
                                pass
                        elif isinstance(event_data['total_price'], (int, float)):
                            event_data['total_price'] = Decimal(str(event_data['total_price']))
                
                # Create event instance from parsed data
                event = BasketCheckoutIntegrationEvent(**event_data)

                # Publish event object to message bus using event_type as
                # routing key on the module exchange (e.g. basket.events).
                exchange = get_exchange_for_event_type(event.event_type)
                await self.message_bus.publish(
                    event, event.event_type, exchange=exchange
                )

            except Exception as e:
                logger.error(
                    f"Failed to reconstruct/publish event for message {message_orm.id}: {e}",
                    exc_info=True
                )
                # Fallback: publish raw event_data dict on the same exchange
                fallback_exchange = get_exchange_for_event_type(message_orm.event_type)
                await self.message_bus.publish(
                    event_data, message_orm.event_type, exchange=fallback_exchange
                )

            # Mark as published
            await self._mark_as_published(session, message_orm.id)
            await session.flush()

        except Exception as e:
            # Mark as failed
            await self._mark_as_failed(session, message_orm.id, str(e))
            await session.flush()
            logger.error(
                f"Failed to publish basket outbox message {message_orm.id}: {e}",
                exc_info=True
            )

    async def _mark_as_processing(self, session: AsyncSession, message_id) -> None:
        """
        Mark message as processing.

        Args:
            session: Database session
            message_id: Message ID
        """
        stmt = (
            update(OutboxORM)
            .where(OutboxORM.id == message_id)
            .values(
                status=BasketOutboxMessageStatus.PROCESSING,
                processed_at=datetime.utcnow(),
            )
        )
        await session.execute(stmt)

    async def _mark_as_published(self, session: AsyncSession, message_id) -> None:
        """
        Mark message as published.

        Args:
            session: Database session
            message_id: Message ID
        """
        stmt = (
            update(OutboxORM)
            .where(OutboxORM.id == message_id)
            .values(
                status=BasketOutboxMessageStatus.PUBLISHED,
                processed_at=datetime.utcnow(),
            )
        )
        await session.execute(stmt)

    async def _mark_as_failed(
        self, session: AsyncSession, message_id, error_message: str
    ) -> None:
        """
        Mark message as failed.

        Args:
            session: Database session
            message_id: Message ID
            error_message: Error message
        """
        stmt = (
            update(OutboxORM)
            .where(OutboxORM.id == message_id)
            .values(
                status=BasketOutboxMessageStatus.FAILED,
                retry_count=OutboxORM.retry_count + 1,
                error_message=error_message,
                processed_at=datetime.utcnow(),
            )
        )
        await session.execute(stmt)

    async def get_worker_status(self) -> dict:
        """
        Get worker status information.

        Returns:
            Dictionary with worker status
        """
        return {
            "is_running": self.is_running,
            "batch_size": self.batch_size,
            "poll_interval": self.poll_interval,
            "max_retries": self.max_retries,
        }

    async def get_outbox_stats(self) -> dict:
        """
        Get outbox statistics.

        Returns:
            Dictionary with outbox statistics
        """
        try:
            session_maker = get_session_maker()
            async with session_maker() as session:
                # Get counts by status
                pending_count = await self._get_message_count(
                    session, BasketOutboxMessageStatus.PENDING
                )
                processing_count = await self._get_message_count(
                    session, BasketOutboxMessageStatus.PROCESSING
                )
                published_count = await self._get_message_count(
                    session, BasketOutboxMessageStatus.PUBLISHED
                )
                failed_count = await self._get_message_count(
                    session, BasketOutboxMessageStatus.FAILED
                )

                return {
                    "pending": pending_count,
                    "processing": processing_count,
                    "published": published_count,
                    "failed": failed_count,
                    "total": pending_count
                    + processing_count
                    + published_count
                    + failed_count,
                }
        except Exception as e:
            logger.error(f"Error getting basket outbox stats: {e}")
            return {}

    async def _get_message_count(
        self, session: AsyncSession, status: BasketOutboxMessageStatus
    ) -> int:
        """
        Get message count by status.

        Args:
            session: Database session
            status: Message status

        Returns:
            Message count
        """
        stmt = select(func.count(OutboxORM.id)).where(OutboxORM.status == status)
        result = await session.execute(stmt)
        return result.scalar() or 0


# Global worker instance
basket_outbox_publisher_worker = BasketOutboxPublisherWorker()

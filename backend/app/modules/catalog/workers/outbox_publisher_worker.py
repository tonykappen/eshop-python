"""Background publisher for outbox table."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.infrastructure.messaging.outbox import OutboxPublisher, OutboxMessage, OutboxMessageStatus
from app.modules.catalog.infrastructure.messaging.bus import InMemoryMessageBus
from app.modules.catalog.infrastructure.persistence.db_session import get_session
from app.modules.catalog.infrastructure.persistence.models.outbox_orm import OutboxORM

logger = logging.getLogger(__name__)


class OutboxPublisherWorker:
    """Background worker for publishing outbox messages."""

    def __init__(
        self,
        message_bus: Optional[InMemoryMessageBus] = None,
        batch_size: int = 10,
        poll_interval: float = 5.0,
        max_retries: int = 3,
    ):
        """
        Initialize the outbox publisher worker.
        
        Args:
            message_bus: Message bus for publishing
            batch_size: Number of messages to process in each batch
            poll_interval: Interval between polls in seconds
            max_retries: Maximum number of retries for failed messages
        """
        self.message_bus = message_bus or InMemoryMessageBus()
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the outbox publisher worker."""
        if self.is_running:
            logger.warning("Outbox publisher worker is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Outbox publisher worker started")

    async def stop(self) -> None:
        """Stop the outbox publisher worker."""
        if not self.is_running:
            logger.warning("Outbox publisher worker is not running")
            return
        
        self.is_running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Outbox publisher worker stopped")

    async def _run_loop(self) -> None:
        """Main worker loop."""
        logger.info("Outbox publisher worker loop started")
        
        while self.is_running:
            try:
                await self._process_pending_messages()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                logger.info("Outbox publisher worker loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in outbox publisher worker loop: {e}")
                await asyncio.sleep(self.poll_interval)
        
        logger.info("Outbox publisher worker loop ended")

    async def _process_pending_messages(self) -> None:
        """Process pending messages from outbox."""
        try:
            async with get_session() as session:
                # Get pending messages
                pending_messages = await self._get_pending_messages(session)
                
                if not pending_messages:
                    return
                
                logger.debug(f"Processing {len(pending_messages)} pending messages")
                
                # Process each message
                for message_orm in pending_messages:
                    await self._process_message(session, message_orm)
                
                # Commit changes
                await session.commit()
                
        except Exception as e:
            logger.error(f"Error processing pending messages: {e}")

    async def _get_pending_messages(self, session: AsyncSession) -> list[OutboxORM]:
        """
        Get pending messages from outbox.
        
        Args:
            session: Database session
            
        Returns:
            List of pending outbox messages
        """
        stmt = select(OutboxORM).where(
            OutboxORM.status == OutboxMessageStatus.PENDING,
            OutboxORM.retry_count < self.max_retries
        ).limit(self.batch_size)
        
        result = await session.execute(stmt)
        return result.scalars().all()

    async def _process_message(self, session: AsyncSession, message_orm: OutboxORM) -> None:
        """
        Process a single outbox message.
        
        Args:
            session: Database session
            message_orm: Outbox message ORM
        """
        try:
            # Mark as processing
            await self._mark_as_processing(session, message_orm.id)
            
            # Create outbox message
            outbox_message = OutboxMessage(
                id=message_orm.id,
                event_type=message_orm.event_type,
                event_data=message_orm.event_data,
                status=OutboxMessageStatus.PROCESSING,
                created_at=message_orm.created_at,
                retry_count=message_orm.retry_count,
                max_retries=message_orm.max_retries,
                correlation_id=message_orm.correlation_id,
            )
            
            # Publish message
            await self.message_bus.publish(
                outbox_message.event_data,
                outbox_message.event_type
            )
            
            # Mark as published
            await self._mark_as_published(session, message_orm.id)
            
            logger.debug(f"Successfully published outbox message: {message_orm.id}")
            
        except Exception as e:
            # Mark as failed
            await self._mark_as_failed(session, message_orm.id, str(e))
            logger.error(f"Failed to publish outbox message {message_orm.id}: {e}")

    async def _mark_as_processing(self, session: AsyncSession, message_id: str) -> None:
        """
        Mark message as processing.
        
        Args:
            session: Database session
            message_id: Message ID
        """
        stmt = update(OutboxORM).where(
            OutboxORM.id == message_id
        ).values(
            status=OutboxMessageStatus.PROCESSING,
            processed_at=datetime.utcnow()
        )
        await session.execute(stmt)

    async def _mark_as_published(self, session: AsyncSession, message_id: str) -> None:
        """
        Mark message as published.
        
        Args:
            session: Database session
            message_id: Message ID
        """
        stmt = update(OutboxORM).where(
            OutboxORM.id == message_id
        ).values(
            status=OutboxMessageStatus.PUBLISHED,
            processed_at=datetime.utcnow()
        )
        await session.execute(stmt)

    async def _mark_as_failed(self, session: AsyncSession, message_id: str, error_message: str) -> None:
        """
        Mark message as failed.
        
        Args:
            session: Database session
            message_id: Message ID
            error_message: Error message
        """
        stmt = update(OutboxORM).where(
            OutboxORM.id == message_id
        ).values(
            status=OutboxMessageStatus.FAILED,
            retry_count=OutboxORM.retry_count + 1,
            error_message=error_message,
            processed_at=datetime.utcnow()
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
            async with get_session() as session:
                # Get counts by status
                pending_count = await self._get_message_count(session, OutboxMessageStatus.PENDING)
                processing_count = await self._get_message_count(session, OutboxMessageStatus.PROCESSING)
                published_count = await self._get_message_count(session, OutboxMessageStatus.PUBLISHED)
                failed_count = await self._get_message_count(session, OutboxMessageStatus.FAILED)
                
                return {
                    "pending": pending_count,
                    "processing": processing_count,
                    "published": published_count,
                    "failed": failed_count,
                    "total": pending_count + processing_count + published_count + failed_count,
                }
        except Exception as e:
            logger.error(f"Error getting outbox stats: {e}")
            return {}

    async def _get_message_count(self, session: AsyncSession, status: OutboxMessageStatus) -> int:
        """
        Get message count by status.
        
        Args:
            session: Database session
            status: Message status
            
        Returns:
            Message count
        """
        from sqlalchemy import func
        
        stmt = select(func.count(OutboxORM.id)).where(
            OutboxORM.status == status
        )
        result = await session.execute(stmt)
        return result.scalar() or 0


# Global worker instance
outbox_publisher_worker = OutboxPublisherWorker()



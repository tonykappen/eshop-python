"""Background publisher for outbox table - generic implementation for all modules."""

import asyncio
import json
import uuid as uuid_mod
from collections.abc import Callable
from datetime import datetime
from typing import Any, AsyncContextManager
from uuid import UUID

from app.core.logging.base_logger import BaseLogger
from app.core.messaging.outbox import OutboxMessage, OutboxMessageStatus
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = BaseLogger(__name__)


class OutboxPublisherWorker:
    """Background worker for publishing outbox messages with atomic claim."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncContextManager[AsyncSession]],
        message_bus: Any,
        outbox_orm_class: type[Any],
        batch_size: int = 10,
        poll_interval: float = 5.0,
        max_retries: int = 3,
    ):
        self.session_factory = session_factory
        self.message_bus = message_bus
        self.outbox_orm_class = outbox_orm_class
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.max_retries = max_retries
        self.is_running = False
        self._task: asyncio.Task | None = None
        self._worker_id = str(uuid_mod.uuid4())[:8]

    async def start(self) -> None:
        """Start the outbox publisher worker."""
        if self.is_running:
            logger.log_warning_with_context(
                "Outbox publisher worker is already running"
            )
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.log_with_context(
            "Outbox publisher worker started",
            context={"worker_id": self._worker_id},
        )

    async def stop(self) -> None:
        """Stop the outbox publisher worker."""
        if not self.is_running:
            logger.log_warning_with_context("Outbox publisher worker is not running")
            return

        self.is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.log_with_context("Outbox publisher worker stopped")

    async def _run_loop(self) -> None:
        """Main worker loop."""
        while self.is_running:
            try:
                await self._process_pending_messages()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.log_error_with_context(
                    "Error in outbox publisher worker loop", error=e
                )
                await asyncio.sleep(self.poll_interval)

    async def _process_pending_messages(self) -> None:
        """Claim and process pending messages atomically."""
        try:
            async with self.session_factory() as session:
                claimed_ids = await self._claim_batch(session)
                if not claimed_ids:
                    return

                await session.commit()

            for message_id in claimed_ids:
                await self._publish_single(message_id)

        except Exception as e:
            logger.log_error_with_context("Error processing pending messages", error=e)

    async def _claim_batch(self, session: AsyncSession) -> list[UUID]:
        """
        Atomically claim a batch of pending messages using SELECT FOR UPDATE SKIP LOCKED.
        Returns the list of claimed message IDs. Caller must commit.
        """
        orm = self.outbox_orm_class

        select_stmt = (
            select(orm.id)
            .where(
                orm.status == OutboxMessageStatus.PENDING,
                orm.retry_count < self.max_retries,
            )
            .order_by(orm.created_at)
            .limit(self.batch_size)
            .with_for_update(skip_locked=True)
        )
        result = await session.execute(select_stmt)
        ids = [row[0] for row in result.all()]

        if not ids:
            return []

        update_stmt = (
            update(orm)
            .where(orm.id.in_(ids))
            .values(
                status=OutboxMessageStatus.PROCESSING,
                claimed_by=self._worker_id,
                claimed_at=datetime.utcnow(),
            )
        )
        await session.execute(update_stmt)

        logger.log_debug_with_context(
            "Claimed outbox batch",
            context={"count": len(ids), "worker_id": self._worker_id},
        )
        return ids

    async def _publish_single(self, message_id: UUID) -> None:
        """Publish a single claimed message; mark published or failed."""
        try:
            async with self.session_factory() as session:
                orm = self.outbox_orm_class
                result = await session.execute(select(orm).where(orm.id == message_id))
                message_orm = result.scalar_one_or_none()
                if message_orm is None:
                    return

                event_data = message_orm.event_data
                if isinstance(event_data, str):
                    try:
                        event_data = json.loads(event_data)
                    except json.JSONDecodeError:
                        pass

                outbox_message = OutboxMessage(
                    id=message_orm.id,
                    event_type=message_orm.event_type,
                    event_data=event_data,
                    status=OutboxMessageStatus.PROCESSING,
                    created_at=message_orm.created_at,
                    retry_count=message_orm.retry_count,
                    max_retries=message_orm.max_retries,
                    correlation_id=message_orm.correlation_id,
                )

                if hasattr(self.message_bus, "connect") and (
                    not hasattr(self.message_bus, "_connection")
                    or self.message_bus._connection is None
                ):
                    try:
                        await self.message_bus.connect()
                    except Exception as e:
                        logger.log_warning_with_context(
                            "Failed to connect message bus", context={"error": str(e)}
                        )

                from app.core.messaging.exchange_resolver import \
                    get_exchange_for_event_type

                exchange = get_exchange_for_event_type(outbox_message.event_type)

                await self.message_bus.publish(
                    outbox_message.event_data,
                    outbox_message.event_type,
                    exchange=exchange,
                )

                await session.execute(
                    update(orm)
                    .where(orm.id == message_id)
                    .values(
                        status=OutboxMessageStatus.PUBLISHED,
                        processed_at=datetime.utcnow(),
                    )
                )
                await session.commit()

                logger.log_debug_with_context(
                    "Published outbox message",
                    context={"message_id": str(message_id)},
                )

        except Exception as e:
            logger.log_error_with_context(
                "Failed to publish outbox message",
                error=e,
                context={"message_id": str(message_id)},
            )
            try:
                async with self.session_factory() as session:
                    await session.execute(
                        update(self.outbox_orm_class)
                        .where(self.outbox_orm_class.id == message_id)
                        .values(
                            status=OutboxMessageStatus.FAILED,
                            retry_count=self.outbox_orm_class.retry_count + 1,
                            error_message=str(e),
                            processed_at=datetime.utcnow(),
                        )
                    )
                    await session.commit()
            except Exception as mark_err:
                logger.log_error_with_context(
                    "Failed to mark outbox message as failed", error=mark_err
                )

    async def get_worker_status(self) -> dict:
        """Get worker status information."""
        return {
            "is_running": self.is_running,
            "worker_id": self._worker_id,
            "batch_size": self.batch_size,
            "poll_interval": self.poll_interval,
            "max_retries": self.max_retries,
        }

    async def get_outbox_stats(self) -> dict:
        """Get outbox statistics."""
        try:
            async with self.session_factory() as session:
                pending = await self._count_by_status(
                    session, OutboxMessageStatus.PENDING
                )
                processing = await self._count_by_status(
                    session, OutboxMessageStatus.PROCESSING
                )
                published = await self._count_by_status(
                    session, OutboxMessageStatus.PUBLISHED
                )
                failed = await self._count_by_status(
                    session, OutboxMessageStatus.FAILED
                )

                return {
                    "pending": pending,
                    "processing": processing,
                    "published": published,
                    "failed": failed,
                    "total": pending + processing + published + failed,
                }
        except Exception as e:
            logger.log_error_with_context("Error getting outbox stats", error=e)
            return {}

    async def _count_by_status(
        self, session: AsyncSession, status: OutboxMessageStatus
    ) -> int:
        result = await session.execute(
            select(func.count(self.outbox_orm_class.id)).where(
                self.outbox_orm_class.status == status
            )
        )
        return result.scalar() or 0

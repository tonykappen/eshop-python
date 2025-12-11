"""Database session management with cancellation token integration for automatic rollback."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import AsyncSessionLocal
from app.core.logging.base_logger import BaseLogger
from app.core.mediator.cancellation import (
    CancellationToken,
    get_cancellation_token_with_session,
)

logger = BaseLogger(__name__)


async def get_db_session_with_cancellation(
    request: Request,
) -> AsyncGenerator[tuple[AsyncSession, CancellationToken], None]:
    """Get database session with integrated cancellation token for automatic rollback."""
    async with AsyncSessionLocal() as session:
        # Create cancellation token with session for automatic rollback
        cancellation_token = get_cancellation_token_with_session(request, session)

        try:
            yield session, cancellation_token
            # Mark as completed if we reach here (no exception)
            cancellation_token.mark_completed()
        except Exception as e:
            # If any exception occurs, rollback the session
            logger.log_error_with_context(
                "Database operation failed, rolling back transaction", error=e
            )
            await session.rollback()
            raise
        finally:
            # Cleanup cancellation token
            await cancellation_token.cleanup()


@asynccontextmanager
async def db_transaction_with_cancellation(
    request: Request,
) -> AsyncGenerator[tuple[AsyncSession, CancellationToken], None]:
    """Database transaction context manager with cancellation token integration."""
    async with AsyncSessionLocal() as session:
        cancellation_token = get_cancellation_token_with_session(request, session)

        try:
            # Begin transaction
            await session.begin()
            yield session, cancellation_token

            # If we reach here without cancellation, commit
            if not cancellation_token.is_cancellation_requested:
                await session.commit()
                logger.log_debug_with_context(
                    "Database transaction committed successfully"
                )
                # Mark as completed after successful commit
                cancellation_token.mark_completed()
            else:
                # If cancelled, rollback
                await session.rollback()
                logger.log_debug_with_context(
                    "Database transaction rolled back due to cancellation"
                )

        except Exception as e:
            # Any exception triggers rollback
            logger.log_error_with_context(
                "Database transaction failed, rolling back", error=e
            )
            await session.rollback()
            raise
        finally:
            await cancellation_token.cleanup()


async def get_cancellation_token_for_session(
    request: Request, session: AsyncSession
) -> CancellationToken:
    """Get cancellation token for an existing database session."""
    return get_cancellation_token_with_session(request, session)

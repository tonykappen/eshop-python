"""Example of using cancellation token with automatic SQLAlchemy rollback."""

from typing import Any
from uuid import UUID

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session_with_cancellation import (
    db_transaction_with_cancellation,
    get_db_session_with_cancellation,
)
from app.core.mediator.cancellation import CancellationToken
from app.core.mediator.fastapi_integration import get_mediator_dependency
from app.core.mediator.mediator import Mediator


# Example 1: Using the enhanced cancellation token in a handler
async def create_product_with_rollback_example(
    request: dict,
    http_request: Request,
    _mediator: Mediator = Depends(get_mediator_dependency),
) -> dict:
    """Example handler that uses cancellation token with automatic rollback."""

    # Use the database session with cancellation token
    async with db_transaction_with_cancellation(http_request) as (
        session,
        cancellation_token,
    ):
        try:
            # Check for cancellation before starting
            cancellation_token.throw_if_cancellation_requested()

            # Perform database operations
            # These will be automatically rolled back if cancellation occurs
            result = await _create_product_in_db(session, request, cancellation_token)

            # More operations...
            await _update_inventory(session, result.id, cancellation_token)
            await _send_notification(result.id, cancellation_token)

            # If we reach here, everything succeeded
            return {"id": str(result.id), "status": "created"}

        except Exception:
            # The transaction will be automatically rolled back
            # due to the context manager
            raise


# Example 2: Using execute_with_rollback for individual operations
async def update_product_with_rollback_example(
    product_id: UUID,
    request: dict,
    http_request: Request,
) -> dict:
    """Example of using execute_with_rollback for individual operations."""

    async with get_db_session_with_cancellation(http_request) as (
        session,
        cancellation_token,
    ):
        # Use execute_with_rollback for automatic rollback on cancellation
        result = await cancellation_token.execute_with_rollback(
            lambda: _update_product_operation(
                session, product_id, request, cancellation_token
            )
        )

        return result


# Example 3: Manual rollback callback registration
async def complex_operation_with_manual_rollback_example(
    http_request: Request,
) -> dict:
    """Example of manually registering rollback callbacks."""

    async with get_db_session_with_cancellation(http_request) as (
        session,
        cancellation_token,
    ):
        # Register custom rollback callbacks
        cancellation_token.register_rollback_callback(
            lambda: _cleanup_external_resources()
        )
        cancellation_token.register_rollback_callback(
            lambda: _send_rollback_notification()
        )

        # Perform operations
        result = await _complex_database_operation(session, cancellation_token)

        return result


# Helper functions (these would be in your actual handlers)
async def _create_product_in_db(
    _session: AsyncSession, _request: dict, token: CancellationToken
) -> Any:
    """Create product in database with cancellation support."""
    # Check for cancellation during operation
    token.throw_if_cancellation_requested()

    # Simulate database operation
    # In real code: session.add(product), await session.flush()
    pass


async def _update_inventory(
    _session: AsyncSession, _product_id: UUID, token: CancellationToken
) -> None:
    """Update inventory with cancellation support."""
    token.throw_if_cancellation_requested()
    # Simulate inventory update
    pass


async def _send_notification(_product_id: UUID, token: CancellationToken) -> None:
    """Send notification with cancellation support."""
    token.throw_if_cancellation_requested()
    # Simulate notification sending
    pass


async def _update_product_operation(
    _session: AsyncSession, _product_id: UUID, _request: dict, token: CancellationToken
) -> dict:
    """Update product operation with cancellation checks."""
    token.throw_if_cancellation_requested()
    # Simulate product update
    return {"id": str(_product_id), "updated": True}


async def _complex_database_operation(
    _session: AsyncSession, token: CancellationToken
) -> dict:
    """Complex database operation with multiple steps."""
    token.throw_if_cancellation_requested()
    # Simulate complex operation
    return {"result": "success"}


def _cleanup_external_resources() -> None:
    """Cleanup external resources on rollback."""
    print("Cleaning up external resources...")


def _send_rollback_notification() -> None:
    """Send notification about rollback."""
    print("Sending rollback notification...")

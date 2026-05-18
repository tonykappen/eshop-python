"""SQLAlchemy event listeners for session commits."""

from typing import Any

from app.core.logging.base_logger import BaseLogger
from app.core.transactions.commit_interceptors import \
    commit_interceptor_registry
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

logger = BaseLogger(__name__)


def register_session_event_listeners() -> None:
    """Register SQLAlchemy event listeners for session commits."""

    @event.listens_for(AsyncSession, "before_flush")
    def before_flush_listener(
        session: AsyncSession, flush_context: Any, instances: Any
    ) -> None:
        """
        Hook into before_flush to collect domain events from entities.

        This ensures domain events are available to interceptors even when
        handlers don't use UoW pattern.
        """
        try:
            # Collect entities from session's identity map and new/deleted collections
            entities: list[Any] = []

            # Get all objects in the session
            for obj in session.identity_map.values():
                entities.append(obj)

            # Also check new and deleted collections
            for obj in session.new:
                if obj not in entities:
                    entities.append(obj)

            # Store entities in session info for use in before_commit
            if not hasattr(session.info, "entities"):
                session.info["entities"] = []
            session.info["entities"].extend(entities)

        except Exception as e:
            logger.log_warning_with_context(
                "Error in before_flush listener", context={"error": str(e)}
            )

    @event.listens_for(AsyncSession, "before_commit")
    async def before_commit_listener(session: AsyncSession) -> None:
        """
        Execute before_commit interceptors.

        Args:
            session: Database session
        """
        try:
            # Get entities from session info (collected in before_flush)
            entities = session.info.get("entities", [])
            await commit_interceptor_registry.execute_before_commit(session, entities)
        except Exception as e:
            logger.log_error_with_context("Error in before_commit listener", error=e)

    @event.listens_for(AsyncSession, "after_commit")
    async def after_commit_listener(session: AsyncSession) -> None:
        """
        Execute after_commit interceptors.

        Args:
            session: Database session
        """
        try:
            # Get entities from session info
            entities = session.info.get("entities", [])
            await commit_interceptor_registry.execute_after_commit(session, entities)
        except Exception as e:
            logger.log_error_with_context("Error in after_commit listener", error=e)

    @event.listens_for(AsyncSession, "after_rollback")
    async def after_rollback_listener(session: AsyncSession) -> None:
        """
        Execute on_rollback interceptors.

        Args:
            session: Database session
        """
        try:
            # Get entities from session info
            entities = session.info.get("entities", [])
            # Create a generic exception for rollback
            error = Exception("Transaction rolled back")
            await commit_interceptor_registry.execute_on_rollback(
                session, entities, error
            )
        except Exception as e:
            logger.log_error_with_context("Error in after_rollback listener", error=e)

    logger.log_with_context("Registered SQLAlchemy session event listeners")

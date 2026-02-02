"""SQLAlchemy event listeners for catalog module to hook into session commits.

NOTE: This file is kept for backward compatibility.
New code should use app.core.database.session_event_listener instead.
"""

import logging
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.transactions.commit_interceptors import (
    commit_interceptor_registry,
)

logger = logging.getLogger(__name__)


def register_session_event_listeners() -> None:
    """Register SQLAlchemy event listeners for session commits."""
    
    @event.listens_for(AsyncSession, "before_flush")
    def before_flush_listener(session: AsyncSession, flush_context: Any, instances: Any) -> None:
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
            if not hasattr(session.info, "catalog_entities"):
                session.info["catalog_entities"] = []
            session.info["catalog_entities"].extend(entities)
            
        except Exception as e:
            logger.warning(f"Error in before_flush listener: {e}")

    logger.info("Registered SQLAlchemy session event listeners for catalog module")

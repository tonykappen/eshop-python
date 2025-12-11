"""Category created domain event handler - internal reactions."""

import logging
from typing import Any

from app.core.domain.events import DomainEventHandler
from app.modules.catalog.domain.category.domain_events.category_created_domain_event import (
    CategoryCreatedDomainEvent,
)

logger = logging.getLogger(__name__)


class CategoryCreatedDomainEventHandler(DomainEventHandler[CategoryCreatedDomainEvent]):
    """Handler for category created domain events - internal reactions."""

    async def handle(self, event: CategoryCreatedDomainEvent) -> None:
        """
        Handle category created domain event.
        
        Args:
            event: The category created domain event
        """
        logger.info(
            f"Category created: {event.category_name} (ID: {event.category_id})"
        )
        
        if event.parent_id:
            logger.info(f"Parent category ID: {event.parent_id}")
        
        # Internal reactions (no integration event):
        # 1. Update read models
        # 2. Update search indexes
        # 3. Update metrics
        
        # For now, just log the event
        logger.info("Category creation processed")

    async def _update_search_index(self, category: Any) -> None:
        """Update search index with new category."""
        # Implementation would go here
        pass

    async def _update_metrics(self, event: CategoryCreatedDomainEvent) -> None:
        """Update metrics for category creation."""
        # Implementation would go here
        pass


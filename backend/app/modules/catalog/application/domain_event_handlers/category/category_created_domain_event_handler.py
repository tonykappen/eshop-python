"""Category created domain event handler - internal reactions."""

from typing import Any

from app.core.domain.events import DomainEventHandler
from app.core.logging.base_logger import BaseLogger
from app.modules.catalog.domain.category.domain_events.category_created_domain_event import (
    CategoryCreatedDomainEvent,
)

logger = BaseLogger(__name__)


class CategoryCreatedDomainEventHandler(DomainEventHandler[CategoryCreatedDomainEvent]):
    """Handler for category created domain events - internal reactions."""

    async def handle(self, event: CategoryCreatedDomainEvent) -> None:
        """
        Handle category created domain event.

        Args:
            event: The category created domain event
        """
        logger.log_with_context(
            "Category created",
            context={
                "category_name": event.category_name,
                "category_id": str(event.category_id)
            }
        )

        if event.parent_id:
            logger.log_with_context(
                "Parent category ID",
                context={"parent_id": str(event.parent_id)}
            )

        # Internal reactions (no integration event):
        # 1. Update read models
        # 2. Update search indexes
        # 3. Update metrics

        # For now, just log the event
        logger.log_with_context("Category creation processed")

    async def _update_search_index(self, category: Any) -> None:
        """Update search index with new category."""
        # Implementation would go here
        pass

    async def _update_metrics(self, event: CategoryCreatedDomainEvent) -> None:
        """Update metrics for category creation."""
        # Implementation would go here
        pass

"""Domain event to integration event subscriptions."""

import logging
from typing import Any

from app.modules.catalog.application.integration_event_handlers.inventory.react_to_stock_adjusted_integration_event_handler import (
    ReactToStockAdjustedIntegrationEventHandler,
)
from app.modules.catalog.application.integration_event_handlers.product.publish_product_created_integration_event_handler import (
    PublishProductCreatedIntegrationEventHandler,
)
from app.modules.catalog.domain.category.domain_event_handlers.category_created_domain_event_handler import (
    CategoryCreatedDomainEventHandler,
)
from app.modules.catalog.domain.inventory.domain_event_handlers.stock_adjusted_domain_event_handler import (
    StockAdjustedDomainEventHandler,
)
from app.modules.catalog.domain.product.domain_event_handlers.product_created_domain_event_handler import (
    ProductCreatedDomainEventHandler,
)
from app.modules.catalog.domain.product.domain_event_handlers.product_price_changed_domain_event_handler import (
    ProductPriceChangedDomainEventHandler,
)
from app.modules.catalog.infrastructure.messaging.domain_dispatcher import (
    domain_event_dispatcher,
)

logger = logging.getLogger(__name__)


class DomainEventSubscriptions:
    """Manages domain event to integration event subscriptions."""

    def __init__(self, event_publisher: Any = None):
        """
        Initialize the subscriptions.

        Args:
            event_publisher: Event publisher service
        """
        self.event_publisher = event_publisher
        self._setup_subscriptions()

    def _setup_subscriptions(self) -> None:
        """Set up domain event subscriptions."""
        logger.info("Setting up domain event subscriptions")

        # Product domain events
        self._setup_product_subscriptions()

        # Category domain events
        self._setup_category_subscriptions()

        # Inventory domain events
        self._setup_inventory_subscriptions()

        logger.info("Domain event subscriptions set up successfully")

    def _setup_product_subscriptions(self) -> None:
        """Set up product domain event subscriptions."""
        from app.modules.catalog.domain.product.domain_events.product_created_domain_event import (
            ProductCreatedDomainEvent,
        )
        from app.modules.catalog.domain.product.domain_events.product_price_changed_domain_event import (
            ProductPriceChangedDomainEvent,
        )

        # Product created domain event
        product_created_handler = ProductCreatedDomainEventHandler()
        domain_event_dispatcher.register_handler(
            ProductCreatedDomainEvent, product_created_handler
        )

        # Product created integration event publisher
        if self.event_publisher:
            product_created_integration_handler = (
                PublishProductCreatedIntegrationEventHandler(self.event_publisher)
            )
            domain_event_dispatcher.register_handler(
                ProductCreatedDomainEvent, product_created_integration_handler.handle
            )

        # Product price changed domain event
        product_price_changed_handler = ProductPriceChangedDomainEventHandler()
        domain_event_dispatcher.register_handler(
            ProductPriceChangedDomainEvent, product_price_changed_handler
        )

        logger.debug("Product domain event subscriptions set up")

    def _setup_category_subscriptions(self) -> None:
        """Set up category domain event subscriptions."""
        from app.modules.catalog.domain.category.domain_events.category_created_domain_event import (
            CategoryCreatedDomainEvent,
        )

        # Category created domain event
        category_created_handler = CategoryCreatedDomainEventHandler()
        domain_event_dispatcher.register_handler(
            CategoryCreatedDomainEvent, category_created_handler
        )

        logger.debug("Category domain event subscriptions set up")

    def _setup_inventory_subscriptions(self) -> None:
        """Set up inventory domain event subscriptions."""
        from app.modules.catalog.domain.inventory.domain_events.stock_adjusted_domain_event import (
            StockAdjustedDomainEvent,
        )

        # Stock adjusted domain event
        stock_adjusted_handler = StockAdjustedDomainEventHandler()
        domain_event_dispatcher.register_handler(
            StockAdjustedDomainEvent, stock_adjusted_handler
        )

        # Stock adjusted integration event handler
        if self.event_publisher:
            stock_adjusted_integration_handler = (
                ReactToStockAdjustedIntegrationEventHandler()
            )
            domain_event_dispatcher.register_handler(
                StockAdjustedDomainEvent, stock_adjusted_integration_handler.handle
            )

        logger.debug("Inventory domain event subscriptions set up")

    def get_subscription_summary(self) -> dict:
        """
        Get a summary of all subscriptions.

        Returns:
            Dictionary with subscription summary
        """
        registered_types = domain_event_dispatcher.get_registered_event_types()

        summary = {
            "total_event_types": len(registered_types),
            "event_types": [event_type.__name__ for event_type in registered_types],
            "subscriptions": {},
        }

        for event_type in registered_types:
            handlers = domain_event_dispatcher.get_handlers(event_type)
            summary["subscriptions"][event_type.__name__] = {
                "handler_count": len(handlers),
                "handler_types": [type(handler).__name__ for handler in handlers],
            }

        return summary

    def clear_subscriptions(self) -> None:
        """Clear all subscriptions."""
        domain_event_dispatcher.clear_handlers()
        logger.info("All domain event subscriptions cleared")

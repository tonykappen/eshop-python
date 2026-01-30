"""Register commit interceptors for catalog module."""

import logging

from app.modules.catalog.application.transactions.commit_interceptor_impl import (
    DomainEventPublisherInterceptor,
    OutboxEnqueuerInterceptor,
)
from app.modules.catalog.application.transactions.commit_interceptors import (
    commit_interceptor_registry,
)
from app.modules.catalog.infrastructure.messaging.domain_dispatcher import (
    DomainEventDispatcher,
)
from app.modules.catalog.module_interface.di.products.products_providers import (
    get_catalog_dispatcher,
)
from app.modules.catalog.infrastructure.event_publisher import CatalogEventPublisher

logger = logging.getLogger(__name__)


def register_catalog_commit_interceptors() -> None:
    """
    Register commit interceptors for catalog module.

    This should be called during module initialization.
    """
    try:
        # Register OutboxEnqueuerInterceptor (runs before commit)
        outbox_interceptor = OutboxEnqueuerInterceptor()
        commit_interceptor_registry.register(outbox_interceptor)
        logger.info("Registered OutboxEnqueuerInterceptor")

        # Register DomainEventPublisherInterceptor (runs after commit)
        # Get dependencies
        try:
            # Create event publisher (will be initialized lazily)
            event_publisher = CatalogEventPublisher()
            domain_event_dispatcher = get_catalog_dispatcher()
        except Exception as e:
            logger.warning(
                f"Could not get event publisher/dispatcher for DomainEventPublisherInterceptor: {e}. "
                "Interceptor will be registered but may not function properly."
            )
            event_publisher = None
            domain_event_dispatcher = None

        domain_event_interceptor = DomainEventPublisherInterceptor(
            event_publisher=event_publisher,
            domain_event_dispatcher=domain_event_dispatcher,
        )
        commit_interceptor_registry.register(domain_event_interceptor)
        logger.info("Registered DomainEventPublisherInterceptor")

        logger.info(
            f"Registered {len(commit_interceptor_registry.get_interceptors())} commit interceptors"
        )

    except Exception as e:
        logger.error(f"Error registering commit interceptors: {e}", exc_info=True)
        raise

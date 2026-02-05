"""Register commit interceptors for catalog module."""

from app.core.context.application_context import RequestContext
from app.core.logging.base_logger import BaseLogger
from app.core.transactions.commit_interceptors import (
    commit_interceptor_registry,
)
from app.core.transactions.interceptor_implementations import (
    AuditStampInterceptor,
    CacheInvalidationInterceptor,
)
from app.core.messaging.domain_dispatcher import (
    DomainEventDispatcher,
)
from app.modules.catalog.application.transactions.commit_interceptor_impl import (
    DomainEventPublisherInterceptor,
    OutboxEnqueuerInterceptor,
)
from app.modules.catalog.module_interface.di.products.products_providers import (
    get_catalog_dispatcher,
    get_catalog_message_bus,
)

logger = BaseLogger(__name__)


def register_catalog_commit_interceptors() -> None:
    """
    Register commit interceptors for catalog module.

    This should be called during module initialization.
    """
    try:
        # Register core AuditStampInterceptor
        # RequestContext will be resolved per-request from DI container
        # For now, create a default one - it will be replaced per-request
        default_request_context = RequestContext()
        audit_interceptor = AuditStampInterceptor(default_request_context)
        commit_interceptor_registry.register(audit_interceptor)
        logger.log_with_context("Registered AuditStampInterceptor", "info")

        # Register core CacheInvalidationInterceptor
        # Cache service will be resolved per-request if needed
        # For now, register without cache service - it can be set per-request if needed
        cache_interceptor = CacheInvalidationInterceptor(cache_service=None)
        commit_interceptor_registry.register(cache_interceptor)
        logger.log_with_context("Registered CacheInvalidationInterceptor", "info")

        # Register OutboxEnqueuerInterceptor (runs before commit)
        outbox_interceptor = OutboxEnqueuerInterceptor()
        commit_interceptor_registry.register(outbox_interceptor)
        logger.log_with_context("Registered OutboxEnqueuerInterceptor", "info")

        # Register DomainEventPublisherInterceptor (runs after commit)
        # Get dependencies
        try:
            # Get message bus (will be initialized lazily)
            message_bus = get_catalog_message_bus()
            domain_event_dispatcher = get_catalog_dispatcher()
        except Exception as e:
            logger.log_warning_with_context(
                "Could not get message bus/dispatcher for DomainEventPublisherInterceptor. "
                "Interceptor will be registered but may not function properly.",
                context={"error": str(e)},
            )
            message_bus = None
            domain_event_dispatcher = None

        domain_event_interceptor = DomainEventPublisherInterceptor(
            message_bus=message_bus,
            domain_event_dispatcher=domain_event_dispatcher,
        )
        commit_interceptor_registry.register(domain_event_interceptor)
        logger.log_with_context("Registered DomainEventPublisherInterceptor", "info")

        logger.log_with_context(
            f"Registered {len(commit_interceptor_registry.get_interceptors())} commit interceptors",
            "info",
            context={"interceptor_count": len(commit_interceptor_registry.get_interceptors())},
        )

    except Exception as e:
        logger.log_exception_detailed("Error registering commit interceptors", exception=e)
        raise

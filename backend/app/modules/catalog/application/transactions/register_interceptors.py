"""Register commit interceptors for catalog module."""

from app.core.context.application_context import RequestContext
from app.core.logging.base_logger import BaseLogger
from app.core.transactions.commit_interceptors import \
    commit_interceptor_registry
from app.core.transactions.interceptor_implementations import (
    AuditStampInterceptor, CacheInvalidationInterceptor)
from app.modules.catalog.application.transactions.commit_interceptor_impl import (
    DomainEventPublisherInterceptor, OutboxEnqueuerInterceptor)
from app.modules.catalog.module_interface.di.products.products_providers import (
    get_catalog_dispatcher, get_catalog_message_bus)

logger = BaseLogger(__name__)

_interceptors_registered = False


class InterceptorDependencyError(RuntimeError):
    """Raised when a required interceptor dependency is missing at registration time."""

    pass


def register_catalog_commit_interceptors() -> None:
    """Register commit interceptors for catalog module.

    This should be called during module initialization.
    Idempotent — duplicate calls are no-ops.

    Raises:
        InterceptorDependencyError: If a required dependency (e.g. outbox) is unavailable.
    """
    global _interceptors_registered
    if _interceptors_registered:
        logger.log_with_context(
            "Catalog commit interceptors already registered — skipping", "info"
        )
        return

    errors: list[str] = []

    # 1. AuditStampInterceptor
    default_request_context = RequestContext()
    audit_interceptor = AuditStampInterceptor(default_request_context)
    commit_interceptor_registry.register(audit_interceptor)
    logger.log_with_context("Registered AuditStampInterceptor", "info")

    # 2. CacheInvalidationInterceptor (after_commit only — best-effort)
    cache_service = None
    try:
        from app.modules.catalog.application.services.catalog_cache_service import (
            CatalogCacheService, RedisCacheService)

        cache_service = CatalogCacheService(RedisCacheService())
    except Exception as e:
        logger.log_warning_with_context(
            "Cache service unavailable — CacheInvalidationInterceptor will be a no-op",
            context={"error": str(e)},
        )
    cache_interceptor = CacheInvalidationInterceptor(cache_service=cache_service)
    commit_interceptor_registry.register(cache_interceptor)
    logger.log_with_context("Registered CacheInvalidationInterceptor", "info")

    # 3. OutboxEnqueuerInterceptor (critical — must be present)
    outbox_interceptor = OutboxEnqueuerInterceptor()
    commit_interceptor_registry.register(outbox_interceptor)
    logger.log_with_context("Registered OutboxEnqueuerInterceptor", "info")

    # 4. DomainEventPublisherInterceptor (after commit — validate deps)
    message_bus = None
    domain_event_dispatcher = None
    try:
        message_bus = get_catalog_message_bus()
        domain_event_dispatcher = get_catalog_dispatcher()
    except Exception as e:
        msg = f"Message bus or dispatcher unavailable for DomainEventPublisherInterceptor: {e}"
        logger.log_warning_with_context(msg)
        errors.append(msg)

    domain_event_interceptor = DomainEventPublisherInterceptor(
        message_bus=message_bus,
        domain_event_dispatcher=domain_event_dispatcher,
    )
    commit_interceptor_registry.register(domain_event_interceptor)
    logger.log_with_context("Registered DomainEventPublisherInterceptor", "info")

    _interceptors_registered = True

    count = len(commit_interceptor_registry.get_interceptors())
    logger.log_with_context(
        f"Registered {count} commit interceptors",
        "info",
        context={"interceptor_count": count},
    )

    if errors:
        logger.log_warning_with_context(
            "Some interceptor dependencies were unavailable at startup",
            context={"issues": errors},
        )

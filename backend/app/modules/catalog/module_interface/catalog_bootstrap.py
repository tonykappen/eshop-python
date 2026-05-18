"""Catalog module bootstrap — single entry point for module registration."""

from typing import Any

from app.core.mediator.handler_registry import HandlerRegistry
from app.core.module_bootstrap import IModuleBootstrap, LifecycleHookRegistry


class CatalogModuleBootstrap(IModuleBootstrap):
    """Catalog bounded-context bootstrap implementation."""

    def register_handlers(self, handler_registry: HandlerRegistry) -> None:
        from app.modules.catalog.module_interface.catalog_handler_registration import \
            register_catalog_handlers

        register_catalog_handlers(handler_registry)

    def register_event_handlers(self, dispatcher: Any) -> None:
        from app.modules.catalog.module_interface.di.products import \
            subscribe_domain_events_to_integration_events

        subscribe_domain_events_to_integration_events(dispatcher)

    def register_interceptors(self) -> None:
        from app.modules.catalog.application.transactions.register_interceptors import \
            register_catalog_commit_interceptors

        register_catalog_commit_interceptors()

    def register_routes(self, app: Any) -> Any:
        from app.modules.catalog.router.product_router import \
            router as product_router
        from fastapi import APIRouter

        router = APIRouter(prefix="/api/v1", tags=["catalog"])
        router.include_router(product_router)
        return router

    def register_lifecycle_hooks(self, registry: LifecycleHookRegistry) -> None:
        registry.add_startup_hook(self._startup_messaging)
        registry.add_shutdown_hook(self._shutdown_messaging)

    async def _startup_messaging(self) -> None:
        """Connect RabbitMQ message bus and start outbox workers."""
        from app.modules.catalog.infrastructure.persistence.db_context import \
            get_session_maker
        from app.modules.catalog.module_interface.di.products.products_providers import \
            get_catalog_message_bus

        message_bus = get_catalog_message_bus()
        if hasattr(message_bus, "connect"):
            outbox_orm = self.get_outbox_orm_class()
            await message_bus.connect(
                outbox_orm_class=outbox_orm,
                get_session_maker=get_session_maker,
            )

    async def _shutdown_messaging(self) -> None:
        """Disconnect RabbitMQ message bus."""
        from app.modules.catalog.module_interface.di.products.products_providers import \
            get_catalog_message_bus

        message_bus = get_catalog_message_bus()
        if hasattr(message_bus, "disconnect"):
            await message_bus.disconnect()

    def get_outbox_orm_class(self) -> type | None:
        try:
            from app.modules.catalog.infrastructure.persistence.orm.outbox_orm import \
                OutboxORM

            return OutboxORM
        except ImportError:
            return None

    def get_session_maker_factory(self) -> Any:
        from app.modules.catalog.infrastructure.persistence.db_context import \
            get_session_maker

        return get_session_maker

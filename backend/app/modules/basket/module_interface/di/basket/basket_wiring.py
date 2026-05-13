"""Dependency injection wiring for basket module."""

import logging
from typing import Any

from fastapi import FastAPI

from app.core.mediator.mediator import Mediator
from app.core.messaging.outbox.outbox_service import IOutboxService
from app.modules.basket.application.unit_of_work.basket_unit_of_work import (
    IBasketUnitOfWork,
)
from app.modules.basket.domain.repositories.basket import IBasketRepository
from app.modules.basket.infrastructure.persistence.repositories.basket.cached_basket_repository import (
    CachedBasketRepository,
)
from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import (
    SqlBasketRepository,
)
from app.modules.basket.infrastructure.persistence.unit_of_work.sql_basket_unit_of_work import (
    SqlBasketUnitOfWork,
)
from app.modules.basket.module_interface.di.basket.basket_containers import (
    get_basket_container,
)
from app.modules.basket.module_interface.di.basket.basket_providers import (
    get_basket_cache_service,
    get_basket_engine,
    get_basket_mediator,
    get_basket_session_maker,
)

logger = logging.getLogger(__name__)


def wire_basket_dependencies(container) -> None:
    """
    Wire basket dependencies into the container.

    Args:
        container: Basket container instance
    """
    # Register core services
    _register_core_services(container)

    # Register repositories
    _register_repositories(container)

    # Register application services
    _register_application_services(container)

    logger.info("Wired basket dependencies")


def _register_core_services(container) -> None:
    """Register core services in the container."""
    # Register engine and session maker as singletons
    container.register_singleton(type(get_basket_engine()), get_basket_engine())
    container.register_singleton(
        type(get_basket_session_maker()), get_basket_session_maker()
    )

    # Register cache service as singleton
    container.register_singleton(type(get_basket_cache_service()), get_basket_cache_service())

    logger.debug("Registered core services")


def _register_repositories(container) -> None:
    """Register repository factories in the container."""
    # Register repository factories
    container.register_factory(
        IBasketRepository, lambda: None
    )  # Will be resolved per request

    logger.debug("Registered repository factories")


def _register_application_services(container) -> None:
    """Register application services in the container."""
    # Register mediator factory
    container.register_factory(Mediator, get_basket_mediator)

    # Register unit of work factory
    container.register_factory(
        IBasketUnitOfWork, lambda: None
    )  # Will be resolved per request

    logger.debug("Registered application services")


def wire_basket_dependencies_to_fastapi(
    app: FastAPI, main_container=None, mediator: Mediator | None = None
) -> None:
    """
    Wire basket dependencies to FastAPI app with proper dependency injection.

    Args:
        app: FastAPI application instance
        main_container: Main application DI container (optional)
        mediator: Main application mediator (optional)
    """
    basket_container = get_basket_container()

    # Register core services in basket container
    _register_core_services(basket_container)
    _register_repositories(basket_container)
    _register_application_services(basket_container)

    # Get cache service
    cache_service = get_basket_cache_service()

    # Override FastAPI dependency providers
    app.dependency_overrides.update(
        {
            # Database dependencies
            get_basket_engine: lambda: basket_container.get(
                type(get_basket_engine())
            ),
            get_basket_session_maker: lambda: basket_container.get(
                type(get_basket_session_maker())
            ),
            # Repository dependencies - use cached repository
            IBasketRepository: lambda session: CachedBasketRepository(
                repository=SqlBasketRepository(session),
                cache_service=cache_service,
            ),
            # Application dependencies
            IBasketUnitOfWork: lambda session: SqlBasketUnitOfWork(session),
            # Mediator dependency - use main mediator if available
            Mediator: lambda: (
                mediator if mediator else basket_container.get(Mediator)
            ),
        }
    )

    logger.info("Wired basket dependencies to FastAPI with overrides")


def register_basket_handlers_with_mediator(mediator: Mediator) -> None:
    """
    Register basket handlers with the mediator.

    Args:
        mediator: Mediator instance
    """
    import asyncio
    from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_handler import (
        AddItemIntoBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_command import (
        AddItemIntoBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_handler import (
        CheckoutBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_command import (
        CheckoutBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.create_basket.create_basket_handler import (
        CreateBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.create_basket.create_basket_command import (
        CreateBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_handler import (
        DeleteBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_command import (
        DeleteBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_handler import (
        RemoveItemFromBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_command import (
        RemoveItemFromBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_handler import (
        UpdateItemPriceInBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_command import (
        UpdateItemPriceInBasketCommand,
    )
    from app.modules.basket.application.features.basket.query.get_basket.get_basket_handler import (
        GetBasketHandler,
    )
    from app.modules.basket.application.features.basket.query.get_basket.get_basket_query import (
        GetBasketQuery,
    )

    async def _register_handlers():
        """Create and register handlers with real dependencies."""
        from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import (
            SqlBasketRepository,
        )
        from app.modules.basket.infrastructure.persistence.unit_of_work.sql_basket_unit_of_work import (
            SqlBasketUnitOfWork,
        )
        from app.modules.basket.module_interface.di.basket.basket_providers import (
            get_basket_cache_service,
            get_basket_mediator,
        )
        from app.modules.basket.infrastructure.persistence.repositories.basket.cached_basket_repository import (
            CachedBasketRepository,
        )
        from app.core.messaging.outbox.outbox_service import OutboxService
        from app.modules.basket.infrastructure.persistence.orm.basket.outbox_orm import (
            OutboxORM as BasketOutboxORM,
        )

        # Get session maker and create a temporary session for handler registration
        session_maker = get_basket_session_maker()
        
        async with session_maker() as temp_session:
            # Create repository with temporary session
            sql_repo = SqlBasketRepository(temp_session)
            cache_service = get_basket_cache_service()
            repo = CachedBasketRepository(repository=sql_repo, cache_service=cache_service)
            
            # Create unit of work
            uow = SqlBasketUnitOfWork(temp_session)
            
            # Get mediator
            basket_mediator = await get_basket_mediator(mediator)
            
            # Create outbox service
            outbox_service = OutboxService(
                temp_session, outbox_orm_class=BasketOutboxORM
            )
            
            # Create and register handlers
            mediator.register_handler(GetBasketQuery, GetBasketHandler(repository=repo))
            mediator.register_handler(AddItemIntoBasketCommand, AddItemIntoBasketHandler(repository=repo, mediator=basket_mediator))
            mediator.register_handler(CreateBasketCommand, CreateBasketHandler(repository=repo))
            mediator.register_handler(DeleteBasketCommand, DeleteBasketHandler(repository=repo))
            mediator.register_handler(RemoveItemFromBasketCommand, RemoveItemFromBasketHandler(repository=repo))
            mediator.register_handler(UpdateItemPriceInBasketCommand, UpdateItemPriceInBasketHandler(repository=repo))
            mediator.register_handler(CheckoutBasketCommand, CheckoutBasketHandler(repository=repo, outbox_service=outbox_service))
            
            logger.info("Registered basket handlers with mediator")
    
    # Run the async registration
    try:
        # Try to run with asyncio.run (creates new event loop)
        # If there's already a running loop, we'll handle it
        try:
            asyncio.run(_register_handlers())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                # Event loop is already running, use a different approach
                # Create a new event loop in a new thread
                import threading
                exception_holder = [None]
                
                def run_in_new_loop():
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_loop.run_until_complete(_register_handlers())
                        new_loop.close()
                    except Exception as ex:
                        exception_holder[0] = ex
                
                thread = threading.Thread(target=run_in_new_loop, daemon=False)
                thread.start()
                thread.join(timeout=10)
                if exception_holder[0]:
                    raise exception_holder[0]
            else:
                raise
    except Exception as e:
        logger.error(f"Failed to register basket handlers: {e}", exc_info=True)
        raise

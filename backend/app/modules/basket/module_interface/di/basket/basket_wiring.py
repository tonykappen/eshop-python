"""Dependency injection wiring for basket module."""

import logging

from app.core.mediator.mediator import Mediator
from app.modules.basket.application.basket_handler_registration import (
    register_basket_handlers, register_basket_handlers_with_mediator)
from app.modules.basket.application.unit_of_work.basket_unit_of_work import \
    IBasketUnitOfWork
from app.modules.basket.domain.repositories.basket import IBasketRepository
from app.modules.basket.infrastructure.persistence.repositories.basket.cached_basket_repository import \
    CachedBasketRepository
from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import \
    SqlBasketRepository
from app.modules.basket.infrastructure.persistence.unit_of_work.sql_basket_unit_of_work import \
    SqlBasketUnitOfWork
from app.modules.basket.module_interface.di.basket.basket_containers import \
    get_basket_container
from app.modules.basket.module_interface.di.basket.basket_providers import (
    get_basket_cache_service, get_basket_engine, get_basket_mediator,
    get_basket_session_maker)
from fastapi import FastAPI

logger = logging.getLogger(__name__)

__all__ = [
    "register_basket_handlers_with_mediator",
    "wire_basket_dependencies",
    "wire_basket_dependencies_to_fastapi",
]


def wire_basket_dependencies(container) -> None:
    """
    Wire basket dependencies into the container.

    Args:
        container: Basket container instance
    """
    _register_core_services(container)
    _register_repositories(container)
    _register_application_services(container)

    logger.info("Wired basket dependencies")


def _register_core_services(container) -> None:
    """Register core services in the container."""
    container.register_singleton(type(get_basket_engine()), get_basket_engine())
    container.register_singleton(
        type(get_basket_session_maker()), get_basket_session_maker()
    )
    container.register_singleton(
        type(get_basket_cache_service()), get_basket_cache_service()
    )

    logger.debug("Registered core services")


def _register_repositories(container) -> None:
    """Register repository factories in the container."""
    container.register_factory(IBasketRepository, lambda: None)

    logger.debug("Registered repository factories")


def _register_application_services(container) -> None:
    """Register application services in the container."""
    container.register_factory(Mediator, get_basket_mediator)
    container.register_factory(IBasketUnitOfWork, lambda: None)

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

    _register_core_services(basket_container)
    _register_repositories(basket_container)
    _register_application_services(basket_container)

    cache_service = get_basket_cache_service()

    app.dependency_overrides.update(
        {
            get_basket_engine: lambda: basket_container.get(type(get_basket_engine())),
            get_basket_session_maker: lambda: basket_container.get(
                type(get_basket_session_maker())
            ),
            IBasketRepository: lambda session: CachedBasketRepository(
                repository=SqlBasketRepository(session),
                cache_service=cache_service,
            ),
            IBasketUnitOfWork: lambda session: SqlBasketUnitOfWork(session),
            Mediator: lambda: (
                mediator if mediator else basket_container.get(Mediator)
            ),
        }
    )

    logger.info("Wired basket dependencies to FastAPI with overrides")

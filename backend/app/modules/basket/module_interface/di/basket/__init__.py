"""Basket DI module."""

from .basket_containers import BasketContainer, get_basket_container
from .basket_providers import (
    BasketCache,
    BasketEngine,
    BasketMediator,
    BasketOutboxService,
    BasketRepo,
    BasketSession,
    BasketSessionMaker,
    BasketUoW,
    get_basket_cache_service,
    get_basket_engine,
    get_basket_mediator,
    get_basket_outbox_service,
    get_basket_repository,
    get_basket_session,
    get_basket_session_maker,
    get_basket_unit_of_work,
)
from .basket_wiring import (
    register_basket_handlers_with_mediator,
    wire_basket_dependencies,
    wire_basket_dependencies_to_fastapi,
)

__all__ = [
    "BasketContainer",
    "get_basket_container",
    "get_basket_engine",
    "get_basket_session_maker",
    "get_basket_session",
    "get_basket_repository",
    "get_basket_unit_of_work",
    "get_basket_outbox_service",
    "get_basket_cache_service",
    "get_basket_mediator",
    "BasketEngine",
    "BasketSessionMaker",
    "BasketSession",
    "BasketRepo",
    "BasketUoW",
    "BasketOutboxService",
    "BasketCache",
    "BasketMediator",
    "wire_basket_dependencies",
    "wire_basket_dependencies_to_fastapi",
    "register_basket_handlers_with_mediator",
]

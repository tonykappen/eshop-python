"""Per-request basket handler dependencies."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from app.modules.basket.domain.repositories.basket import IBasketRepository


@dataclass
class BasketHandlerContext:
    """Repository and related services scoped to one database session."""

    repository: IBasketRepository
    outbox_service: Any | None = None


@asynccontextmanager
async def use_basket_context(
    context_factory: Callable[[], Any] | None = None,
    repository: IBasketRepository | None = None,
    outbox_service: Any | None = None,
) -> AsyncIterator[BasketHandlerContext]:
    """Resolve handler dependencies for production (factory) or tests (direct mocks)."""
    if context_factory is not None:
        async with context_factory() as ctx:
            yield ctx
        return

    if repository is not None:
        yield BasketHandlerContext(
            repository=repository,
            outbox_service=outbox_service,
        )
        return

    raise RuntimeError(
        "Handler not properly configured: missing basket context factory"
    )

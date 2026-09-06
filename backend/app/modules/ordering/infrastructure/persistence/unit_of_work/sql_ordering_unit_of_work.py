"""SQL-based unit of work implementation for ordering module."""

from app.modules.ordering.application.unit_of_work.ordering_unit_of_work import \
    IOrderingUnitOfWork
from app.modules.ordering.domain.repositories.order import IOrderRepository
from app.modules.ordering.infrastructure.persistence.repositories.orders.sql_order_repository import \
    SqlOrderRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SqlOrderingUnitOfWork(IOrderingUnitOfWork):
    """SQL-based unit of work for ordering module."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize unit of work.

        Args:
            session: Real database session (no mocking)
        """
        self._session = session
        self._orders: IOrderRepository | None = None

    @property
    def orders(self) -> IOrderRepository:
        """Get order repository."""
        if self._orders is None:
            self._orders = SqlOrderRepository(self._session)
        return self._orders

    async def __aenter__(self):
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self) -> None:
        """Commit the unit of work."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the unit of work."""
        await self._session.rollback()

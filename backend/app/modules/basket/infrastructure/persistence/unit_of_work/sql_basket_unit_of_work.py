"""SQL implementation of IBasketUnitOfWork."""

from app.modules.basket.application.unit_of_work.basket_unit_of_work import \
    IBasketUnitOfWork
from app.modules.basket.domain.repositories.basket import IBasketRepository
from app.modules.basket.infrastructure.persistence.repositories.basket.sql_basket_repository import \
    SqlBasketRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SqlBasketUnitOfWork(IBasketUnitOfWork):
    """SQL-based implementation of IBasketUnitOfWork."""

    def __init__(self, session: AsyncSession):
        """
        Initialize unit of work.

        Args:
            session: Database session
        """
        self._session = session
        self._baskets: IBasketRepository | None = None

    @property
    def baskets(self) -> IBasketRepository:
        """Get basket repository."""
        if self._baskets is None:
            self._baskets = SqlBasketRepository(self._session)
        return self._baskets

    async def commit(self) -> int:
        """
        Commit the unit of work.

        Returns:
            Number of affected rows
        """
        await self._session.commit()
        return 1  # SQLAlchemy doesn't return exact row count

    async def rollback(self) -> None:
        """Rollback the unit of work."""
        await self._session.rollback()

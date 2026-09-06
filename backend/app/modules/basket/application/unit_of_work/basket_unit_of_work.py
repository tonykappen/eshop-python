"""Basket unit of work interface."""

from abc import ABC, abstractmethod

from app.modules.basket.domain.repositories.basket import IBasketRepository


class IBasketUnitOfWork(ABC):
    """Interface for basket unit of work."""

    @property
    @abstractmethod
    def baskets(self) -> IBasketRepository:
        """Get basket repository."""
        pass

    @abstractmethod
    async def commit(self) -> int:
        """
        Commit the unit of work.

        Returns:
            Number of affected rows
        """
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the unit of work."""
        pass

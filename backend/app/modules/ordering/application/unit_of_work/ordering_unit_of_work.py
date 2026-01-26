"""Ordering unit of work interface."""

from abc import ABC, abstractmethod

from app.core.database.unit_of_work import IUnitOfWork


class IOrderingUnitOfWork(IUnitOfWork, ABC):
    """Unit of work interface for ordering module."""

    @abstractmethod
    async def __aenter__(self):
        """Enter async context manager."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        pass

"""Order repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID

from app.modules.ordering.domain.entities.order.order import Order


class IOrderRepository(ABC):
    """Repository interface for Order aggregate."""

    @abstractmethod
    async def add(self, order: Order) -> None:
        """
        Add a new order.

        Args:
            order: Order to add
        """
        pass

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        """
        Get an order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(
        self, skip: int = 0, take: int = 10
    ) -> tuple[list[Order], int]:
        """
        Get all orders with pagination.

        Args:
            skip: Number of orders to skip
            take: Number of orders to take

        Returns:
            Tuple of (list of orders, total count)
        """
        pass

    @abstractmethod
    async def remove(self, order: Order) -> None:
        """
        Remove an order.

        Args:
            order: Order to remove
        """
        pass

    @abstractmethod
    async def save_changes_async(self) -> None:
        """
        Save changes to the database.

        This method should commit the current transaction.
        """
        pass

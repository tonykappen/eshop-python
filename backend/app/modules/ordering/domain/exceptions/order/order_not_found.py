"""Order not found exception."""

from uuid import UUID

from app.core.exceptions.not_found_exception import NotFoundException


class OrderNotFoundException(NotFoundException):
    """Exception raised when an order is not found."""

    def __init__(self, order_id: UUID):
        """
        Initialize the exception.

        Args:
            order_id: The ID of the order that was not found
        """
        super().__init__(
            message=f"Order with ID {order_id} was not found",
            name="Order",
            key=str(order_id),
        )
        self.order_id = order_id

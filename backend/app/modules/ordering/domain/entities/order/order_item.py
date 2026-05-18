"""OrderItem entity for ordering domain."""

from decimal import Decimal
from uuid import UUID

from app.core.domain.entity import Entity
from pydantic import Field


class OrderItem(Entity):
    """OrderItem entity matching .NET OrderItem class."""

    order_id: UUID = Field(..., description="Order ID")
    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., description="Quantity")
    price: Decimal = Field(..., description="Price")

    def __init__(
        self,
        order_id: UUID,
        product_id: UUID,
        quantity: int,
        price: Decimal,
        **kwargs,
    ):
        """
        Initialize OrderItem, matching .NET internal constructor pattern.

        Args:
            order_id: Order ID
            product_id: Product ID
            quantity: Quantity
            price: Price
            **kwargs: Additional fields for Entity base class
        """
        super().__init__(
            order_id=order_id,
            product_id=product_id,
            quantity=quantity,
            price=price,
            **kwargs,
        )

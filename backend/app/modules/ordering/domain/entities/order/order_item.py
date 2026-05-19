"""OrderItem entity for ordering domain."""

from decimal import Decimal
from uuid import UUID

from app.core.domain.entity import Entity
from pydantic import Field


class OrderItem(Entity):
    """OrderItem entity matching .NET OrderItem class.

    Pydantic auto-generates an ``__init__`` accepting all fields as keyword
    arguments; we don't override it because doing so was a no-op (the body
    just forwarded the same kwargs to ``super().__init__``).
    """

    order_id: UUID = Field(..., description="Order ID")
    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., description="Quantity")
    price: Decimal = Field(..., description="Price")

"""Order aggregate root for ordering domain."""

from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import Field, field_validator

from app.core.domain.entity import Aggregate
from app.modules.ordering.domain.value_objects import Address, Payment

from .order_item import OrderItem

if TYPE_CHECKING:
    from app.modules.ordering.domain.domain_events.orders.order_created_domain_event import (
        OrderCreatedDomainEvent,
    )


class Order(Aggregate):
    """Order aggregate root matching .NET Order class."""

    customer_id: UUID = Field(..., description="Customer ID")
    order_name: str = Field(..., description="Order name")
    shipping_address: Address = Field(..., description="Shipping address")
    billing_address: Address = Field(..., description="Billing address")
    payment: Payment = Field(..., description="Payment information")
    items: list[OrderItem] = Field(
        default_factory=list, description="Order items"
    )

    @property
    def total_price(self) -> Decimal:
        """
        Calculate total price of all items, matching .NET TotalPrice property.

        Returns:
            Total price as Decimal
        """
        return sum(item.price * Decimal(item.quantity) for item in self.items)

    @classmethod
    def create(
        cls,
        id: UUID,
        customer_id: UUID,
        order_name: str,
        shipping_address: Address,
        billing_address: Address,
        payment: Payment,
    ) -> "Order":
        """
        Create a new order, matching .NET Order.Create static method.

        Args:
            id: Order ID
            customer_id: Customer ID
            order_name: Order name
            shipping_address: Shipping address
            billing_address: Billing address
            payment: Payment information

        Returns:
            Created Order instance with OrderCreatedDomainEvent
        """
        order = cls(
            id=id,
            customer_id=customer_id,
            order_name=order_name,
            shipping_address=shipping_address,
            billing_address=billing_address,
            payment=payment,
            items=[],
        )

        # Lazy import to avoid circular dependency
        from app.modules.ordering.domain.domain_events.orders.order_created_domain_event import (
            OrderCreatedDomainEvent,
        )

        order.add_domain_event(OrderCreatedDomainEvent(order))

        return order

    def add(self, product_id: UUID, quantity: int, price: Decimal) -> None:
        """
        Add an item to the order, matching .NET Add method.

        If the item already exists (same product_id), increment the quantity.
        Otherwise, add a new item.

        Args:
            product_id: Product ID
            quantity: Quantity to add (must be > 0)
            price: Price (must be > 0)

        Raises:
            ValueError: If quantity or price is invalid
        """
        if quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        if price <= 0:
            raise ValueError("Price must be greater than 0")

        # Check if item already exists
        existing_item = next(
            (item for item in self.items if item.product_id == product_id), None
        )

        if existing_item:
            # Increment quantity
            existing_item.quantity += quantity
        else:
            # Create new item
            new_item = OrderItem(
                order_id=self.id,
                product_id=product_id,
                quantity=quantity,
                price=price,
            )
            self.items.append(new_item)

    def remove(self, product_id: UUID) -> None:
        """
        Remove an item from the order, matching .NET Remove method.

        Args:
            product_id: Product ID to remove
        """
        item_to_remove = next(
            (item for item in self.items if item.product_id == product_id), None
        )
        if item_to_remove:
            self.items.remove(item_to_remove)

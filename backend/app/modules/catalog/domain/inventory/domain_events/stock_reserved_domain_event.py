# isort: skip_file
"""Stock reserved domain event."""

from uuid import UUID

from pydantic import Field

from app.core.domain.events import DomainEvent
from app.modules.catalog.domain.inventory.models.inventory_item import InventoryItem


class StockReservedDomainEvent(DomainEvent):
    """Domain event raised when stock is reserved."""

    event_type: str = Field(
        default="inventory.stock_reserved", description="Event type"
    )
    inventory_item: InventoryItem = Field(..., description="The inventory item")
    reserved_quantity: int = Field(..., description="Reserved quantity")

    def __init__(self, inventory_item: InventoryItem, reserved_quantity: int, **data):
        """Initialize the domain event."""
        super().__init__(
            aggregate_id=inventory_item.id,
            event_type="inventory.stock_reserved",
            inventory_item=inventory_item,
            reserved_quantity=reserved_quantity,
            **data,
        )

    @property
    def inventory_item_id(self) -> UUID:
        """Get the inventory item ID."""
        return self.inventory_item.id

    @property
    def product_id(self) -> UUID:
        """Get the product ID."""
        return self.inventory_item.product_id

    @property
    def total_reserved_quantity(self) -> int:
        """Get the total reserved quantity after this reservation."""
        return self.inventory_item.reserved_quantity

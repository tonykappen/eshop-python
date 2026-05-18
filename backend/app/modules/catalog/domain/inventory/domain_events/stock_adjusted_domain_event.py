"""Stock adjusted domain event."""

from uuid import UUID

from app.core.domain.events import DomainEvent
from app.modules.catalog.domain.entities.inventory import InventoryItem
from pydantic import Field


class StockAdjustedDomainEvent(DomainEvent):
    """Domain event raised when stock is adjusted."""

    event_type: str = Field(
        default="inventory.stock_adjusted", description="Event type"
    )
    inventory_item: InventoryItem = Field(..., description="The inventory item")
    old_quantity: int = Field(..., description="Old quantity")
    new_quantity: int = Field(..., description="New quantity")
    adjustment: int = Field(..., description="Quantity adjustment")

    def __init__(
        self,
        inventory_item: InventoryItem,
        old_quantity: int,
        new_quantity: int,
        adjustment: int,
        **data,
    ):
        """Initialize the domain event."""
        super().__init__(
            aggregate_id=inventory_item.id,
            event_type="inventory.stock_adjusted",
            inventory_item=inventory_item,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            adjustment=adjustment,
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
    def is_stock_increase(self) -> bool:
        """Check if this is a stock increase."""
        return self.adjustment > 0

    @property
    def is_stock_decrease(self) -> bool:
        """Check if this is a stock decrease."""
        return self.adjustment < 0

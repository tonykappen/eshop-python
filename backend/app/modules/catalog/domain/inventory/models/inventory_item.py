"""Inventory item domain model."""

from uuid import UUID

from pydantic import Field, field_validator

from app.core.domain.entity import Aggregate


class InventoryItem(Aggregate):
    """Inventory item aggregate."""

    product_id: UUID = Field(..., description="Product ID")
    quantity: int = Field(..., description="Available quantity", ge=0)
    reserved_quantity: int = Field(default=0, description="Reserved quantity", ge=0)
    reorder_threshold: int = Field(default=10, description="Reorder threshold", ge=0)
    max_stock_threshold: int = Field(default=1000, description="Max stock threshold", ge=0)

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: int) -> int:
        """Validate quantity is non-negative."""
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v

    @field_validator("reserved_quantity")
    @classmethod
    def validate_reserved_quantity(cls, v: int) -> int:
        """Validate reserved quantity is non-negative."""
        if v < 0:
            raise ValueError("Reserved quantity cannot be negative")
        return v

    @field_validator("reorder_threshold")
    @classmethod
    def validate_reorder_threshold(cls, v: int) -> int:
        """Validate reorder threshold is non-negative."""
        if v < 0:
            raise ValueError("Reorder threshold cannot be negative")
        return v

    @field_validator("max_stock_threshold")
    @classmethod
    def validate_max_stock_threshold(cls, v: int) -> int:
        """Validate max stock threshold is non-negative."""
        if v < 0:
            raise ValueError("Max stock threshold cannot be negative")
        return v

    @classmethod
    def create(
        cls,
        inventory_item_id: UUID,
        product_id: UUID,
        quantity: int,
        reorder_threshold: int = 10,
        max_stock_threshold: int = 1000,
    ) -> "InventoryItem":
        """
        Create a new inventory item.
        
        Args:
            inventory_item_id: Unique identifier for the inventory item
            product_id: Product ID
            quantity: Initial quantity
            reorder_threshold: Reorder threshold
            max_stock_threshold: Max stock threshold
            
        Returns:
            Created InventoryItem instance
            
        Raises:
            ValueError: If any validation fails
        """
        return cls(
            id=inventory_item_id,
            product_id=product_id,
            quantity=quantity,
            reserved_quantity=0,
            reorder_threshold=reorder_threshold,
            max_stock_threshold=max_stock_threshold,
        )

    @property
    def available_quantity(self) -> int:
        """Get available quantity (total - reserved)."""
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self) -> bool:
        """Check if stock is low (below reorder threshold)."""
        return self.available_quantity <= self.reorder_threshold

    @property
    def is_out_of_stock(self) -> bool:
        """Check if item is out of stock."""
        return self.available_quantity <= 0

    def adjust_stock(self, quantity: int) -> None:
        """
        Adjust stock quantity.
        
        Args:
            quantity: Quantity to adjust (positive to add, negative to subtract)
            
        Raises:
            ValueError: If adjustment would result in negative quantity
        """
        new_quantity = self.quantity + quantity
        if new_quantity < 0:
            raise ValueError("Cannot adjust stock below zero")
        
        old_quantity = self.quantity
        self.quantity = new_quantity
        self.increment_version()

        # Add domain event for stock adjustment
        from app.modules.catalog.domain.inventory.domain_events.stock_adjusted_domain_event import (
            StockAdjustedDomainEvent,
        )
        self.add_domain_event(
            StockAdjustedDomainEvent(
                inventory_item=self,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                adjustment=quantity,
            )
        )

    def reserve_stock(self, quantity: int) -> None:
        """
        Reserve stock quantity.
        
        Args:
            quantity: Quantity to reserve
            
        Raises:
            ValueError: If not enough available stock
        """
        if quantity <= 0:
            raise ValueError("Reservation quantity must be positive")
        
        if self.available_quantity < quantity:
            raise ValueError("Not enough available stock to reserve")
        
        self.reserved_quantity += quantity
        self.increment_version()

        # Add domain event for stock reservation
        from app.modules.catalog.domain.inventory.domain_events.stock_reserved_domain_event import (
            StockReservedDomainEvent,
        )
        self.add_domain_event(
            StockReservedDomainEvent(
                inventory_item=self,
                reserved_quantity=quantity,
            )
        )

    def release_reservation(self, quantity: int) -> None:
        """
        Release reserved stock quantity.
        
        Args:
            quantity: Quantity to release from reservation
            
        Raises:
            ValueError: If not enough reserved stock
        """
        if quantity <= 0:
            raise ValueError("Release quantity must be positive")
        
        if self.reserved_quantity < quantity:
            raise ValueError("Not enough reserved stock to release")
        
        self.reserved_quantity -= quantity
        self.increment_version()

    def consume_reserved_stock(self, quantity: int) -> None:
        """
        Consume reserved stock (remove from both reserved and total).
        
        Args:
            quantity: Quantity to consume
            
        Raises:
            ValueError: If not enough reserved stock
        """
        if quantity <= 0:
            raise ValueError("Consumption quantity must be positive")
        
        if self.reserved_quantity < quantity:
            raise ValueError("Not enough reserved stock to consume")
        
        self.reserved_quantity -= quantity
        self.quantity -= quantity
        self.increment_version()



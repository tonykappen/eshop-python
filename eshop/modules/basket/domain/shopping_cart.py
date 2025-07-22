"""ShoppingCart domain model."""

from typing import List
from uuid import UUID

from eshop.core.domain.entity import Aggregate
from .shopping_cart_item import ShoppingCartItem


class ShoppingCart(Aggregate):
    """ShoppingCart aggregate following DDD patterns."""
    
    def __init__(self, id: UUID, user_name: str):
        super().__init__(id=id)
        self._user_name = user_name
        self._items: List[ShoppingCartItem] = []
    
    @property
    def user_name(self) -> str:
        """Get the user name."""
        return self._user_name
    
    @property
    def items(self) -> List['ShoppingCartItem']:
        """Get the shopping cart items."""
        return self._items.copy()
    
    @property
    def total_price(self) -> float:
        """Calculate the total price of all items."""
        return sum(item.price * item.quantity for item in self._items)
    
    @classmethod
    def create(cls, id: UUID, user_name: str) -> 'ShoppingCart':
        """Create a new shopping cart."""
        if not user_name or not user_name.strip():
            raise ValueError("User name cannot be null or empty")
        
        return cls(id=id, user_name=user_name)
    
    def add_item(self, product_id: UUID, quantity: int, color: str, price: float, product_name: str) -> None:
        """Add an item to the shopping cart."""
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        if price <= 0:
            raise ValueError("Price must be greater than zero")
        
        # Check if item already exists
        existing_item = next((item for item in self._items if item.product_id == product_id), None)
        
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = ShoppingCartItem(
                shopping_cart_id=self.id,
                product_id=product_id,
                quantity=quantity,
                color=color,
                price=price,
                product_name=product_name
            )
            self._items.append(new_item)
    
    def remove_item(self, product_id: UUID) -> None:
        """Remove an item from the shopping cart."""
        existing_item = next((item for item in self._items if item.product_id == product_id), None)
        
        if existing_item:
            self._items.remove(existing_item) 
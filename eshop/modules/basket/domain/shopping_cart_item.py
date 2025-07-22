"""ShoppingCartItem domain model."""

from uuid import UUID

from eshop.core.domain.entity import Entity


class ShoppingCartItem(Entity):
    """ShoppingCartItem entity following DDD patterns."""
    
    def __init__(self, id: UUID, shopping_cart_id: UUID, product_id: UUID, quantity: int, color: str, price: float, product_name: str):
        super().__init__(id=id)
        self._shopping_cart_id = shopping_cart_id
        self._product_id = product_id
        self._quantity = quantity
        self._color = color
        self._price = price
        self._product_name = product_name
    
    @property
    def shopping_cart_id(self) -> UUID:
        """Get the shopping cart ID."""
        return self._shopping_cart_id
    
    @property
    def product_id(self) -> UUID:
        """Get the product ID."""
        return self._product_id
    
    @property
    def quantity(self) -> int:
        """Get the quantity."""
        return self._quantity
    
    @quantity.setter
    def quantity(self, value: int) -> None:
        """Set the quantity."""
        self._quantity = value
    
    @property
    def color(self) -> str:
        """Get the color."""
        return self._color
    
    @property
    def price(self) -> float:
        """Get the price."""
        return self._price
    
    @property
    def product_name(self) -> str:
        """Get the product name."""
        return self._product_name
    
    def update_price(self, new_price: float) -> None:
        """Update the price of the item."""
        if new_price <= 0:
            raise ValueError("Price must be greater than zero")
        self._price = new_price 
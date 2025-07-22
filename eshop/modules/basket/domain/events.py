"""Basket domain events."""

from uuid import UUID

from eshop.core.domain.entity import DomainEvent


class BasketCheckoutEvent(DomainEvent):
    """Event raised when a basket is checked out."""
    
    def __init__(self, basket_id: UUID, user_name: str, total_price: float, shipping_address: str, payment_method: str):
        super().__init__(event_type="BasketCheckoutEvent")
        self.basket_id = basket_id
        self.user_name = user_name
        self.total_price = total_price
        self.shipping_address = shipping_address
        self.payment_method = payment_method


class ProductPriceChangedEvent(DomainEvent):
    """Event raised when a product price changes."""
    
    def __init__(self, product_id: UUID, old_price: float, new_price: float):
        super().__init__(event_type="ProductPriceChangedEvent")
        self.product_id = product_id
        self.old_price = old_price
        self.new_price = new_price 
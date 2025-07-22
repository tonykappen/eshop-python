"""Basket API request models."""

from uuid import UUID

from eshop.core.repr.base import BaseRequest


class CreateBasketRequest(BaseRequest):
    """Request to create a new basket."""
    
    user_name: str


class AddItemIntoBasketRequest(BaseRequest):
    """Request to add an item to basket."""
    
    product_id: UUID
    quantity: int
    color: str
    price: float
    product_name: str


class RemoveItemFromBasketRequest(BaseRequest):
    """Request to remove an item from basket."""
    
    product_id: UUID


class UpdateItemPriceInBasketRequest(BaseRequest):
    """Request to update item price in basket."""
    
    product_id: UUID
    new_price: float


class CheckoutBasketRequest(BaseRequest):
    """Request to checkout a basket."""
    
    shipping_address: str
    payment_method: str 
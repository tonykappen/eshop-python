"""Basket CQRS commands."""

from typing import Optional
from uuid import UUID

from eshop.core.cqrs.base import ICommand


class CreateBasketCommand(ICommand):
    """Command to create a new basket."""
    
    user_name: str


class AddItemIntoBasketCommand(ICommand):
    """Command to add an item to basket."""
    
    basket_id: UUID
    product_id: UUID
    quantity: int
    color: str
    price: float
    product_name: str


class RemoveItemFromBasketCommand(ICommand):
    """Command to remove an item from basket."""
    
    basket_id: UUID
    product_id: UUID


class UpdateItemPriceInBasketCommand(ICommand):
    """Command to update item price in basket."""
    
    basket_id: UUID
    product_id: UUID
    new_price: float


class DeleteBasketCommand(ICommand):
    """Command to delete a basket."""
    
    basket_id: UUID


class CheckoutBasketCommand(ICommand):
    """Command to checkout a basket."""
    
    basket_id: UUID
    shipping_address: str
    payment_method: str 
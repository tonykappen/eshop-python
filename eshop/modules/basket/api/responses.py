"""Basket API response models."""

from eshop.core.repr.base import BaseResponse
from ..domain.dtos import ShoppingCartDto


class CreateBasketResponse(BaseResponse):
    """Response for creating a new basket."""
    
    basket_id: str


class GetBasketResponse(BaseResponse):
    """Response for getting a basket."""
    
    data: ShoppingCartDto


class AddItemIntoBasketResponse(BaseResponse):
    """Response for adding an item to basket."""
    pass


class RemoveItemFromBasketResponse(BaseResponse):
    """Response for removing an item from basket."""
    pass


class UpdateItemPriceInBasketResponse(BaseResponse):
    """Response for updating item price in basket."""
    pass


class DeleteBasketResponse(BaseResponse):
    """Response for deleting a basket."""
    pass


class CheckoutBasketResponse(BaseResponse):
    """Response for checking out a basket."""
    pass 
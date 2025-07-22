"""Basket DTOs."""

from typing import List
from uuid import UUID

from pydantic import BaseModel, Field


class ShoppingCartItemDto(BaseModel):
    """Shopping cart item DTO."""
    
    id: UUID
    product_id: UUID
    quantity: int
    color: str
    price: float
    product_name: str
    
    class Config:
        from_attributes = True


class ShoppingCartDto(BaseModel):
    """Shopping cart DTO."""
    
    id: UUID
    user_name: str
    items: List[ShoppingCartItemDto] = Field(default_factory=list)
    total_price: float = 0.0
    
    class Config:
        from_attributes = True


class BasketCheckoutDto(BaseModel):
    """Basket checkout DTO."""
    
    user_name: str
    total_price: float
    shipping_address: str
    payment_method: str
    
    class Config:
        from_attributes = True 
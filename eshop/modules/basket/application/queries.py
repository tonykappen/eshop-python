"""Basket CQRS queries."""

from uuid import UUID

from eshop.core.cqrs.base import IQuery


class GetBasketQuery(IQuery):
    """Query to get a basket by ID."""
    
    basket_id: UUID 
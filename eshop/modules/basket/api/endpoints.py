"""Basket API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path

from eshop.core.repr.base import Endpoint
from .requests import (
    CreateBasketRequest,
    AddItemIntoBasketRequest,
    RemoveItemFromBasketRequest,
    UpdateItemPriceInBasketRequest,
    CheckoutBasketRequest
)
from .responses import (
    CreateBasketResponse,
    GetBasketResponse,
    AddItemIntoBasketResponse,
    RemoveItemFromBasketResponse,
    UpdateItemPriceInBasketResponse,
    DeleteBasketResponse,
    CheckoutBasketResponse
)
from ..application.commands import (
    CreateBasketCommand,
    AddItemIntoBasketCommand,
    RemoveItemFromBasketCommand,
    UpdateItemPriceInBasketCommand,
    DeleteBasketCommand,
    CheckoutBasketCommand
)
from ..application.queries import GetBasketQuery
from ..domain.exceptions import BasketNotFoundException

router = APIRouter(prefix="/api/basket", tags=["Basket"])


class CreateBasketEndpoint(Endpoint[CreateBasketRequest, CreateBasketResponse]):
    """Endpoint for creating a new basket."""
    
    def __init__(self, command_handler):
        self.command_handler = command_handler
    
    async def handle(self, request, data: CreateBasketRequest) -> CreateBasketResponse:
        """Handle create basket request."""
        command = CreateBasketCommand(user_name=data.user_name)
        result = await self.command_handler.handle(command)
        
        return CreateBasketResponse(
            success=result.success,
            message=result.message,
            basket_id=result.data["basket_id"]
        )


class GetBasketEndpoint(Endpoint[None, GetBasketResponse]):
    """Endpoint for getting a basket."""
    
    def __init__(self, query_handler):
        self.query_handler = query_handler
    
    async def handle(self, request, data: None) -> GetBasketResponse:
        """Handle get basket request."""
        basket_id = request.path_params.get("basket_id")
        query = GetBasketQuery(basket_id=UUID(basket_id))
        result = await self.query_handler.handle(query)
        
        # Convert domain model to DTO
        from ..domain.dtos import ShoppingCartDto, ShoppingCartItemDto
        items_dto = [
            ShoppingCartItemDto(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                color=item.color,
                price=item.price,
                product_name=item.product_name
            )
            for item in result.data.items
        ]
        
        basket_dto = ShoppingCartDto(
            id=result.data.id,
            user_name=result.data.user_name,
            items=items_dto,
            total_price=result.data.total_price
        )
        
        return GetBasketResponse(
            success=result.success,
            message=result.message,
            data=basket_dto
        )


class AddItemIntoBasketEndpoint(Endpoint[AddItemIntoBasketRequest, AddItemIntoBasketResponse]):
    """Endpoint for adding an item to basket."""
    
    def __init__(self, command_handler):
        self.command_handler = command_handler
    
    async def handle(self, request, data: AddItemIntoBasketRequest) -> AddItemIntoBasketResponse:
        """Handle add item request."""
        basket_id = request.path_params.get("basket_id")
        command = AddItemIntoBasketCommand(
            basket_id=UUID(basket_id),
            product_id=data.product_id,
            quantity=data.quantity,
            color=data.color,
            price=data.price,
            product_name=data.product_name
        )
        result = await self.command_handler.handle(command)
        
        return AddItemIntoBasketResponse(
            success=result.success,
            message=result.message
        )


class RemoveItemFromBasketEndpoint(Endpoint[RemoveItemFromBasketRequest, RemoveItemFromBasketResponse]):
    """Endpoint for removing an item from basket."""
    
    def __init__(self, command_handler):
        self.command_handler = command_handler
    
    async def handle(self, request, data: RemoveItemFromBasketRequest) -> RemoveItemFromBasketResponse:
        """Handle remove item request."""
        basket_id = request.path_params.get("basket_id")
        command = RemoveItemFromBasketCommand(
            basket_id=UUID(basket_id),
            product_id=data.product_id
        )
        result = await self.command_handler.handle(command)
        
        return RemoveItemFromBasketResponse(
            success=result.success,
            message=result.message
        )


class UpdateItemPriceInBasketEndpoint(Endpoint[UpdateItemPriceInBasketRequest, UpdateItemPriceInBasketResponse]):
    """Endpoint for updating item price in basket."""
    
    def __init__(self, command_handler):
        self.command_handler = command_handler
    
    async def handle(self, request, data: UpdateItemPriceInBasketRequest) -> UpdateItemPriceInBasketResponse:
        """Handle update item price request."""
        basket_id = request.path_params.get("basket_id")
        command = UpdateItemPriceInBasketCommand(
            basket_id=UUID(basket_id),
            product_id=data.product_id,
            new_price=data.new_price
        )
        result = await self.command_handler.handle(command)
        
        return UpdateItemPriceInBasketResponse(
            success=result.success,
            message=result.message
        )


class DeleteBasketEndpoint(Endpoint[None, DeleteBasketResponse]):
    """Endpoint for deleting a basket."""
    
    def __init__(self, command_handler):
        self.command_handler = command_handler
    
    async def handle(self, request, data: None) -> DeleteBasketResponse:
        """Handle delete basket request."""
        basket_id = request.path_params.get("basket_id")
        command = DeleteBasketCommand(basket_id=UUID(basket_id))
        result = await self.command_handler.handle(command)
        
        return DeleteBasketResponse(
            success=result.success,
            message=result.message
        )


class CheckoutBasketEndpoint(Endpoint[CheckoutBasketRequest, CheckoutBasketResponse]):
    """Endpoint for checking out a basket."""
    
    def __init__(self, command_handler):
        self.command_handler = command_handler
    
    async def handle(self, request, data: CheckoutBasketRequest) -> CheckoutBasketResponse:
        """Handle checkout basket request."""
        basket_id = request.path_params.get("basket_id")
        command = CheckoutBasketCommand(
            basket_id=UUID(basket_id),
            shipping_address=data.shipping_address,
            payment_method=data.payment_method
        )
        result = await self.command_handler.handle(command)
        
        return CheckoutBasketResponse(
            success=result.success,
            message=result.message
        ) 
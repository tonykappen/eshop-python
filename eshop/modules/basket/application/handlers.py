"""Basket CQRS handlers."""

from uuid import uuid4

from eshop.core.cqrs.base import ICommandHandler, IQueryHandler, CommandResult, QueryResult

from .commands import (
    CreateBasketCommand,
    AddItemIntoBasketCommand,
    RemoveItemFromBasketCommand,
    UpdateItemPriceInBasketCommand,
    DeleteBasketCommand,
    CheckoutBasketCommand
)
from .queries import GetBasketQuery
from ..domain.shopping_cart import ShoppingCart
from ..domain.exceptions import BasketNotFoundException


class CreateBasketHandler(ICommandHandler[CommandResult]):
    """Handler for creating a new basket."""
    
    def __init__(self, basket_repository):
        self.basket_repository = basket_repository
    
    async def handle(self, command: CreateBasketCommand) -> CommandResult:
        """Handle create basket command."""
        basket_id = uuid4()
        basket = ShoppingCart.create(basket_id, command.user_name)
        
        await self.basket_repository.save(basket)
        
        return CommandResult(
            success=True,
            message="Basket created successfully",
            data={"basket_id": str(basket_id)}
        )


class AddItemIntoBasketHandler(ICommandHandler[CommandResult]):
    """Handler for adding an item to basket."""
    
    def __init__(self, basket_repository):
        self.basket_repository = basket_repository
    
    async def handle(self, command: AddItemIntoBasketCommand) -> CommandResult:
        """Handle add item command."""
        basket = await self.basket_repository.get_by_id(command.basket_id)
        if not basket:
            raise BasketNotFoundException(str(command.basket_id))
        
        basket.add_item(
            command.product_id,
            command.quantity,
            command.color,
            command.price,
            command.product_name
        )
        
        await self.basket_repository.save(basket)
        
        return CommandResult(
            success=True,
            message="Item added to basket successfully"
        )


class RemoveItemFromBasketHandler(ICommandHandler[CommandResult]):
    """Handler for removing an item from basket."""
    
    def __init__(self, basket_repository):
        self.basket_repository = basket_repository
    
    async def handle(self, command: RemoveItemFromBasketCommand) -> CommandResult:
        """Handle remove item command."""
        basket = await self.basket_repository.get_by_id(command.basket_id)
        if not basket:
            raise BasketNotFoundException(str(command.basket_id))
        
        basket.remove_item(command.product_id)
        
        await self.basket_repository.save(basket)
        
        return CommandResult(
            success=True,
            message="Item removed from basket successfully"
        )


class UpdateItemPriceInBasketHandler(ICommandHandler[CommandResult]):
    """Handler for updating item price in basket."""
    
    def __init__(self, basket_repository):
        self.basket_repository = basket_repository
    
    async def handle(self, command: UpdateItemPriceInBasketCommand) -> CommandResult:
        """Handle update item price command."""
        basket = await self.basket_repository.get_by_id(command.basket_id)
        if not basket:
            raise BasketNotFoundException(str(command.basket_id))
        
        # Find the item and update its price
        for item in basket.items:
            if item.product_id == command.product_id:
                item.update_price(command.new_price)
                break
        
        await self.basket_repository.save(basket)
        
        return CommandResult(
            success=True,
            message="Item price updated successfully"
        )


class DeleteBasketHandler(ICommandHandler[CommandResult]):
    """Handler for deleting a basket."""
    
    def __init__(self, basket_repository):
        self.basket_repository = basket_repository
    
    async def handle(self, command: DeleteBasketCommand) -> CommandResult:
        """Handle delete basket command."""
        basket = await self.basket_repository.get_by_id(command.basket_id)
        if not basket:
            raise BasketNotFoundException(str(command.basket_id))
        
        await self.basket_repository.delete(command.basket_id)
        
        return CommandResult(
            success=True,
            message="Basket deleted successfully"
        )


class CheckoutBasketHandler(ICommandHandler[CommandResult]):
    """Handler for checking out a basket."""
    
    def __init__(self, basket_repository, event_publisher):
        self.basket_repository = basket_repository
        self.event_publisher = event_publisher
    
    async def handle(self, command: CheckoutBasketCommand) -> CommandResult:
        """Handle checkout basket command."""
        basket = await self.basket_repository.get_by_id(command.basket_id)
        if not basket:
            raise BasketNotFoundException(str(command.basket_id))
        
        # Create checkout event
        from ..domain.events import BasketCheckoutEvent
        checkout_event = BasketCheckoutEvent(
            basket_id=command.basket_id,
            user_name=basket.user_name,
            total_price=basket.total_price,
            shipping_address=command.shipping_address,
            payment_method=command.payment_method
        )
        
        # Publish event
        await self.event_publisher.publish_domain_event(checkout_event)
        
        # Delete basket after checkout
        await self.basket_repository.delete(command.basket_id)
        
        return CommandResult(
            success=True,
            message="Basket checked out successfully"
        )


class GetBasketHandler(IQueryHandler[ShoppingCart]):
    """Handler for getting a basket."""
    
    def __init__(self, basket_repository):
        self.basket_repository = basket_repository
    
    async def handle(self, query: GetBasketQuery) -> QueryResult[ShoppingCart]:
        """Handle get basket query."""
        basket = await self.basket_repository.get_by_id(query.basket_id)
        if not basket:
            raise BasketNotFoundException(str(query.basket_id))
        
        return QueryResult(
            success=True,
            data=basket,
            message="Basket retrieved successfully"
        ) 
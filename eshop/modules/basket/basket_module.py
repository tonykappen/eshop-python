"""Basket module configuration."""

from fastapi import APIRouter

from .api.endpoints import router as basket_router


class BasketModule:
    """Basket module configuration."""
    
    @staticmethod
    def get_router() -> APIRouter:
        """Get the basket module router."""
        return basket_router
    
    @staticmethod
    def register_services(container):
        """Register basket module services in the DI container."""
        from .infrastructure.repositories import BasketRepository, CachedBasketRepository
        from .application.handlers import (
            CreateBasketHandler,
            AddItemIntoBasketHandler,
            RemoveItemFromBasketHandler,
            UpdateItemPriceInBasketHandler,
            DeleteBasketHandler,
            CheckoutBasketHandler,
            GetBasketHandler
        )
        
        # Register repositories
        container.basket_repository = container.providers.Singleton(BasketRepository)
        container.cached_basket_repository = container.providers.Singleton(
            CachedBasketRepository,
            basket_repository=container.basket_repository,
            cache_service=container.cache_service
        )
        
        # Register handlers
        container.create_basket_handler = container.providers.Singleton(
            CreateBasketHandler,
            basket_repository=container.cached_basket_repository
        )
        
        container.add_item_into_basket_handler = container.providers.Singleton(
            AddItemIntoBasketHandler,
            basket_repository=container.cached_basket_repository
        )
        
        container.remove_item_from_basket_handler = container.providers.Singleton(
            RemoveItemFromBasketHandler,
            basket_repository=container.cached_basket_repository
        )
        
        container.update_item_price_in_basket_handler = container.providers.Singleton(
            UpdateItemPriceInBasketHandler,
            basket_repository=container.cached_basket_repository
        )
        
        container.delete_basket_handler = container.providers.Singleton(
            DeleteBasketHandler,
            basket_repository=container.cached_basket_repository
        )
        
        container.checkout_basket_handler = container.providers.Singleton(
            CheckoutBasketHandler,
            basket_repository=container.cached_basket_repository,
            event_publisher=container.event_publisher
        )
        
        container.get_basket_handler = container.providers.Singleton(
            GetBasketHandler,
            basket_repository=container.cached_basket_repository
        ) 
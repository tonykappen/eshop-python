"""Basket module handler registration for mediator pattern."""

from app.core.mediator.handler_registry import HandlerRegistry


def register_basket_handlers(handler_registry: HandlerRegistry) -> None:
    """Register basket module handlers with the mediator."""
    # Import commands and queries
    from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_command import (
        AddItemIntoBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_handler import (
        AddItemIntoBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_command import (
        CheckoutBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_handler import (
        CheckoutBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.create_basket.create_basket_command import (
        CreateBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.create_basket.create_basket_handler import (
        CreateBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_command import (
        DeleteBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_handler import (
        DeleteBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_command import (
        RemoveItemFromBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_handler import (
        RemoveItemFromBasketHandler,
    )
    from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_command import (
        UpdateItemPriceInBasketCommand,
    )
    from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_handler import (
        UpdateItemPriceInBasketHandler,
    )
    from app.modules.basket.application.features.basket.query.get_basket.get_basket_handler import (
        GetBasketHandler,
    )
    from app.modules.basket.application.features.basket.query.get_basket.get_basket_query import (
        GetBasketQuery,
    )

    # Note: Basket handlers require dependencies (repository, mediator, unit of work, etc.)
    # These will be injected via FastAPI DI when handlers are actually called.
    # For registration, we create handlers with dependencies that will be resolved at runtime.
    # However, since handlers need dependencies, we'll need to use a factory pattern or
    # register them with the mediator's dependency injection system.
    
    # For now, we'll register handler classes/types rather than instances.
    # The actual handler resolution will happen via FastAPI DI when endpoints are called.
    # This is a temporary solution - handlers will be created per-request with proper DI.
    
    # Since HandlerRegistry.register_handler expects instances, we need to create them.
    # But handlers need dependencies. The solution is to create handlers with dependencies
    # from FastAPI's dependency injection system when they're needed.
    
    # For registration purposes, we'll create handlers with dependencies resolved from
    # FastAPI's dependency injection. However, this requires access to the FastAPI app.
    
    # Alternative: Register handlers directly in the router where we have access to DI.
    # This is what the catalog module does - it registers handlers in router.py
    
    # For now, we'll leave this as a placeholder. Handlers will be registered in router.py
    # where we have access to FastAPI's dependency injection system.
    pass

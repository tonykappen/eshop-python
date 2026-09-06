"""Basket module handler registration for mediator pattern."""

from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import Mediator


def register_basket_handlers(handler_registry: HandlerRegistry) -> None:
    """Register basket module handlers with the mediator."""
    _register_handlers(handler_registry)


def register_basket_handlers_with_mediator(mediator: Mediator) -> None:
    """Register basket handlers on the application mediator."""
    _register_handlers(mediator.handler_registry, mediator=mediator)


def _register_handlers(
    handler_registry: HandlerRegistry, mediator: Mediator | None = None
) -> None:
    """Register basket handlers with per-request session factories."""
    from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_command import \
        AddItemIntoBasketCommand
    from app.modules.basket.application.features.basket.command.add_item_into_basket.add_item_into_basket_handler import \
        AddItemIntoBasketHandler
    from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_command import \
        CheckoutBasketCommand
    from app.modules.basket.application.features.basket.command.checkout_basket.checkout_basket_handler import \
        CheckoutBasketHandler
    from app.modules.basket.application.features.basket.command.create_basket.create_basket_command import \
        CreateBasketCommand
    from app.modules.basket.application.features.basket.command.create_basket.create_basket_handler import \
        CreateBasketHandler
    from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_command import \
        DeleteBasketCommand
    from app.modules.basket.application.features.basket.command.delete_basket.delete_basket_handler import \
        DeleteBasketHandler
    from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_command import \
        RemoveItemFromBasketCommand
    from app.modules.basket.application.features.basket.command.remove_item_from_basket.remove_item_from_basket_handler import \
        RemoveItemFromBasketHandler
    from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_command import \
        UpdateItemPriceInBasketCommand
    from app.modules.basket.application.features.basket.command.update_item_price_in_basket.update_item_price_in_basket_handler import \
        UpdateItemPriceInBasketHandler
    from app.modules.basket.application.features.basket.query.get_basket.get_basket_handler import \
        GetBasketHandler
    from app.modules.basket.application.features.basket.query.get_basket.get_basket_query import \
        GetBasketQuery
    from app.modules.basket.module_interface.di.basket.basket_providers import \
        create_basket_handler_context_factory

    context_factory = create_basket_handler_context_factory()
    if mediator is None:
        raise RuntimeError(
            "Basket handlers require the application mediator for cross-module queries"
        )

    handler_registry.register_handler(
        GetBasketQuery, GetBasketHandler(context_factory=context_factory)
    )
    handler_registry.register_handler(
        AddItemIntoBasketCommand,
        AddItemIntoBasketHandler(
            context_factory=context_factory,
            mediator=mediator,
        ),
    )
    handler_registry.register_handler(
        CreateBasketCommand,
        CreateBasketHandler(context_factory=context_factory),
    )
    handler_registry.register_handler(
        DeleteBasketCommand,
        DeleteBasketHandler(context_factory=context_factory),
    )
    handler_registry.register_handler(
        RemoveItemFromBasketCommand,
        RemoveItemFromBasketHandler(context_factory=context_factory),
    )
    handler_registry.register_handler(
        UpdateItemPriceInBasketCommand,
        UpdateItemPriceInBasketHandler(context_factory=context_factory),
    )
    handler_registry.register_handler(
        CheckoutBasketCommand,
        CheckoutBasketHandler(context_factory=context_factory),
    )

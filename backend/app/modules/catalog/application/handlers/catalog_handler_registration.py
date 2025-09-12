"""Catalog module handler registration for mediator pattern."""

from app.core.mediator.handler_registry import HandlerRegistry


def register_catalog_handlers(handler_registry: HandlerRegistry) -> None:
    """Register catalog module handlers with the mediator."""
    from app.modules.catalog.application.handlers.create_product_handler import (
        CreateProductCommand,
        CreateProductHandler,
    )
    from app.modules.catalog.application.handlers.get_product_by_id_handler import (
        GetProductByIdHandler,
    )
    from app.modules.catalog.application.handlers.get_products_handler import (
        GetProductsHandler,
        GetProductsQuery,
    )
    from app.modules.catalog.contracts.products.features.get_product_by_id import (
        GetProductByIdQuery,
    )

    # Register handlers with their corresponding query/command types
    handler_registry.register_handler(GetProductByIdQuery, GetProductByIdHandler(None))
    handler_registry.register_handler(GetProductsQuery, GetProductsHandler(None))
    handler_registry.register_handler(CreateProductCommand, CreateProductHandler(None))

"""Catalog module handler registration for mediator pattern."""

from app.core.mediator.handler_registry import HandlerRegistry


def register_catalog_handlers(handler_registry: HandlerRegistry) -> None:
    """Register catalog module handlers with the mediator."""
    from app.modules.catalog.api.endpoints.products import CreateProductCommand
    from app.modules.catalog.application.features.product.queries.get_product_by_id.query import (
        GetProductByIdQuery,
    )
    from app.modules.catalog.application.handlers.create_product_handler import (
        CreateProductHandler,
    )
    from app.modules.catalog.application.handlers.delete_product_handler import (
        DeleteProductCommand,
        DeleteProductHandler,
    )
    from app.modules.catalog.application.handlers.get_product_by_id_handler import (
        GetProductByIdHandler,
    )
    from app.modules.catalog.application.handlers.get_products_handler import (
        GetProductsHandler,
        GetProductsQuery,
    )
    from app.modules.catalog.application.handlers.update_product_handler import (
        UpdateProductCommand,
        UpdateProductHandler,
    )

    # Register handlers with their corresponding query/command types
    handler_registry.register_handler(GetProductByIdQuery, GetProductByIdHandler())
    handler_registry.register_handler(GetProductsQuery, GetProductsHandler())
    handler_registry.register_handler(CreateProductCommand, CreateProductHandler())
    handler_registry.register_handler(UpdateProductCommand, UpdateProductHandler())
    handler_registry.register_handler(DeleteProductCommand, DeleteProductHandler())

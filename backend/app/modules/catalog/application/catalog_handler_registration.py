"""Catalog module handler registration for mediator pattern."""

from app.core.mediator.handler_registry import HandlerRegistry


def register_catalog_handlers(handler_registry: HandlerRegistry) -> None:
    """Register catalog module handlers with the mediator."""
    # Import commands from application layer
    from app.modules.catalog.application.features.products.commands.create_product.command import (
        CreateProductCommand,
    )
    from app.modules.catalog.application.features.products.commands.create_product.handler import (
        CreateProductHandler,
    )
    from app.modules.catalog.application.features.products.commands.delete_product.command import (
        DeleteProductCommand,
    )
    from app.modules.catalog.application.features.products.commands.delete_product.handler import (
        DeleteProductHandler,
    )
    from app.modules.catalog.application.features.products.commands.update_product.command import (
        UpdateProductCommand,
    )
    from app.modules.catalog.application.features.products.commands.update_product.handler import (
        UpdateProductHandler,
    )
    from app.modules.catalog.application.features.products.queries.get_product_by_id.query import (
        GetProductByIdQuery,
    )
    from app.modules.catalog.application.features.products.queries.get_product_by_id.handler import (
        GetProductByIdHandler,
    )
    from app.modules.catalog.application.features.products.queries.get_products.query import (
        GetProductsQuery,
    )
    from app.modules.catalog.application.features.products.queries.get_products.handler import (
        GetProductsHandler,
    )

    # Register handlers with their corresponding query/command types
    handler_registry.register_handler(GetProductByIdQuery, GetProductByIdHandler())
    handler_registry.register_handler(GetProductsQuery, GetProductsHandler())
    handler_registry.register_handler(CreateProductCommand, CreateProductHandler())
    handler_registry.register_handler(UpdateProductCommand, UpdateProductHandler())
    handler_registry.register_handler(DeleteProductCommand, DeleteProductHandler())

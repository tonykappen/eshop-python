"""Catalog module handler registration for mediator pattern."""

from app.core.mediator.handler_registry import HandlerRegistry


def register_catalog_handlers(handler_registry: HandlerRegistry) -> None:
    """Register catalog module handlers with the mediator."""
    # Import commands from application layer
    from app.modules.catalog.application.features.products.commands.create_product.create_product_command import (
        CreateProductCommand,
    )
    from app.modules.catalog.application.features.products.commands.create_product.create_product_handler import (
        CreateProductHandler,
    )
    from app.modules.catalog.application.features.products.commands.delete_product.delete_product_command import (
        DeleteProductCommand,
    )
    from app.modules.catalog.application.features.products.commands.delete_product.delete_product_handler import (
        DeleteProductHandler,
    )
    from app.modules.catalog.application.features.products.commands.update_product.update_product_command import (
        UpdateProductCommand,
    )
    from app.modules.catalog.application.features.products.commands.update_product.update_product_handler import (
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
    from app.modules.catalog.application.features.products.queries.get_products_by_category.query import (
        GetProductsByCategoryQuery,
    )
    from app.modules.catalog.application.features.products.queries.get_products_by_category.handler import (
        GetProductsByCategoryHandler,
    )

    # Register handlers with their corresponding query/command types
    handler_registry.register_handler(GetProductByIdQuery, GetProductByIdHandler())
    handler_registry.register_handler(GetProductsQuery, GetProductsHandler())
    handler_registry.register_handler(GetProductsByCategoryQuery, GetProductsByCategoryHandler())
    handler_registry.register_handler(CreateProductCommand, CreateProductHandler())
    handler_registry.register_handler(UpdateProductCommand, UpdateProductHandler())
    handler_registry.register_handler(DeleteProductCommand, DeleteProductHandler())












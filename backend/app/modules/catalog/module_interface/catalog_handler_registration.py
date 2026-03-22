"""Catalog module handler registration for mediator pattern."""

from app.core.mediator.handler_registry import HandlerRegistry


def register_catalog_handlers(handler_registry: HandlerRegistry) -> None:
    """Register catalog module handlers with the mediator.

    All handlers receive a UoW factory so they depend only on abstractions —
    no direct AsyncSessionLocal, SqlProductRepository, or CatalogCacheService
    construction.
    """
    from app.modules.catalog.module_interface.di.products.products_providers import (
        create_catalog_uow_factory,
    )

    uow_factory = create_catalog_uow_factory()

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
    from app.modules.catalog.application.features.products.queries.get_product_by_id.handler import (
        GetProductByIdHandler,
    )
    from app.modules.catalog.application.features.products.queries.get_product_by_id.get_product_by_id_query import (
        GetProductByIdQuery,
    )
    from app.modules.catalog.application.features.products.queries.get_products.handler import (
        GetProductsHandler,
    )
    from app.modules.catalog.application.features.products.queries.get_products.get_products_query import (
        GetProductsQuery,
    )
    from app.modules.catalog.application.features.products.queries.get_products_by_category.handler import (
        GetProductsByCategoryHandler,
    )
    from app.modules.catalog.application.features.products.queries.get_products_by_category.get_products_by_category_query import (
        GetProductsByCategoryQuery,
    )

    handler_registry.register_handler(GetProductByIdQuery, GetProductByIdHandler(uow_factory))
    handler_registry.register_handler(GetProductsQuery, GetProductsHandler(uow_factory))
    handler_registry.register_handler(
        GetProductsByCategoryQuery, GetProductsByCategoryHandler(uow_factory)
    )
    handler_registry.register_handler(CreateProductCommand, CreateProductHandler(uow_factory))
    handler_registry.register_handler(UpdateProductCommand, UpdateProductHandler(uow_factory))
    handler_registry.register_handler(DeleteProductCommand, DeleteProductHandler(uow_factory))

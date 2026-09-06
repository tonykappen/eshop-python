"""Mapping profiles for object-to-object mapping.

Generic primitives only. Domain-specific profiles live in their respective modules.
CatalogProductProfile is re-exported here for backward compatibility but its
canonical location is app.modules.catalog.application.mapping.profiles.
"""

from app.core.mapping.profiles.base_mapping_profile import BaseMappingProfile


def __getattr__(name: str):
    if name == "CatalogProductProfile":
        from app.core.mapping.profiles.catalog_product_profile import \
            CatalogProductProfile

        return CatalogProductProfile
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BaseMappingProfile",
    "CatalogProductProfile",
]

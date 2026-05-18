"""Mapping profiles for catalog module."""

from app.modules.catalog.application.mapping_profiles.category_mapping_profile import \
    CategoryMapper
from app.modules.catalog.application.mapping_profiles.product_mapping_profile import \
    ProductMapper

__all__ = ["ProductMapper", "CategoryMapper"]

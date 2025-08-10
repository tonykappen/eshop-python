"""Initial data for Catalog module - matches .NET InitialData."""

from decimal import Decimal
from uuid import UUID

from app.modules.catalog.domain.models import Product


class InitialData:
    """Initial data for Catalog module - matches .NET InitialData."""

    @staticmethod
    def get_products() -> list[Product]:
        """Get initial products - matches .NET Products property."""
        return [
            Product.create(
                product_id=UUID("5334c996-8457-4cf0-815c-ed2b77c4ff61"),
                name="IPhone X",
                category=["category1"],
                description="Long description",
                image_file="imagefile",
                price=Decimal("500"),
            ),
            Product.create(
                product_id=UUID("c67d6323-e8b1-4bdf-9a75-b0d0d2e7e914"),
                name="Samsung 10",
                category=["category1"],
                description="Long description",
                image_file="imagefile",
                price=Decimal("400"),
            ),
            Product.create(
                product_id=UUID("4f136e9f-ff8c-4c1f-9a33-d12f689bdab8"),
                name="Huawei Plus",
                category=["category2"],
                description="Long description",
                image_file="imagefile",
                price=Decimal("650"),
            ),
            Product.create(
                product_id=UUID("6ec1297b-ec0a-4aa1-be25-6726e3b51a27"),
                name="Xiaomi Mi",
                category=["category2"],
                description="Long description",
                image_file="imagefile",
                price=Decimal("450"),
            ),
        ]

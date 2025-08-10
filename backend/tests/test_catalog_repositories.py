"""Tests for catalog repositories."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.domain.entities import (
    CatalogBrand,
    CatalogCategory,
    CatalogItem,
)
from app.modules.catalog.infrastructure.orm_models import (
    CatalogBrandORM,
    CatalogCategoryORM,
    CatalogItemORM,
)
from app.modules.catalog.infrastructure.repositories import (
    CatalogBrandRepository,
    CatalogCategoryRepository,
    CatalogItemRepository,
)


class TestCatalogItemRepository:
    """Test CatalogItemRepository."""

    def test_repository_initialization(self) -> None:
        """Test repository initialization."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_get_by_id_success(self) -> None:
        """Test successful get_by_id."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        item_id = uuid4()
        mock_orm_item = MagicMock(spec=CatalogItemORM)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm_item

        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_domain_item = MagicMock(spec=CatalogItem)
            mock_mapper.from_orm.return_value = mock_domain_item

            result = await repo.get_by_id(item_id)

            assert result == mock_domain_item
            mock_session.execute.assert_called_once()
            mock_mapper.from_orm.assert_called_once_with(mock_orm_item, CatalogItem)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        """Test get_by_id when item not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        item_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id(item_id)

        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_success(self) -> None:
        """Test successful get_all."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        mock_orm_items = [
            MagicMock(spec=CatalogItemORM),
            MagicMock(spec=CatalogItemORM),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_orm_items

        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_domain_items = [
                MagicMock(spec=CatalogItem),
                MagicMock(spec=CatalogItem),
            ]
            mock_mapper.from_orm_list.return_value = mock_domain_items

            result = await repo.get_all()

            assert result == mock_domain_items
            mock_session.execute.assert_called_once()
            mock_mapper.from_orm_list.assert_called_once_with(
                mock_orm_items, CatalogItem
            )

    @pytest.mark.asyncio
    async def test_get_by_category_success(self) -> None:
        """Test successful get_by_category."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        category_id = uuid4()
        mock_orm_items = [MagicMock(spec=CatalogItemORM)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_orm_items

        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_domain_items = [MagicMock(spec=CatalogItem)]
            mock_mapper.from_orm_list.return_value = mock_domain_items

            result = await repo.get_by_category(category_id)

            assert result == mock_domain_items
            mock_session.execute.assert_called_once()
            mock_mapper.from_orm_list.assert_called_once_with(
                mock_orm_items, CatalogItem
            )

    @pytest.mark.asyncio
    async def test_add_success(self) -> None:
        """Test successful add."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        mock_domain_item = MagicMock(spec=CatalogItem)
        mock_orm_item = MagicMock(spec=CatalogItemORM)

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_mapper.to_orm.return_value = mock_orm_item
            mock_mapper.from_orm.return_value = mock_domain_item

            result = await repo.add(mock_domain_item)

            assert result == mock_domain_item
            mock_mapper.to_orm.assert_called_once_with(mock_domain_item, CatalogItemORM)
            mock_session.add.assert_called_once_with(mock_orm_item)
            mock_session.flush.assert_called_once()
            mock_mapper.from_orm.assert_called_once_with(mock_orm_item, CatalogItem)

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test successful update."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        mock_domain_item = MagicMock(spec=CatalogItem)
        mock_domain_item.id = uuid4()
        mock_orm_item = MagicMock(spec=CatalogItemORM)

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_orm_item
        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_mapper.from_orm.return_value = mock_domain_item

            result = await repo.update(mock_domain_item)

            assert result == mock_domain_item
            mock_session.execute.assert_called_once()
            mock_mapper.update_orm_from_domain.assert_called_once_with(
                mock_orm_item, mock_domain_item
            )
            # The update method calls from_orm with the result of update_orm_from_domain
            mock_mapper.from_orm.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Test successful delete."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        item_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repo.delete(item_id)

        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test delete when item not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogItemRepository(mock_session)

        item_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await repo.delete(item_id)

        assert result is False
        mock_session.execute.assert_called_once()


class TestCatalogCategoryRepository:
    """Test CatalogCategoryRepository."""

    def test_repository_initialization(self) -> None:
        """Test repository initialization."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_get_by_id_success(self) -> None:
        """Test successful get_by_id."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)

        category_id = uuid4()
        mock_orm_category = MagicMock(spec=CatalogCategoryORM)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm_category

        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_domain_category = MagicMock(spec=CatalogCategory)
            mock_mapper.from_orm.return_value = mock_domain_category

            result = await repo.get_by_id(category_id)

            assert result == mock_domain_category
            mock_session.execute.assert_called_once()
            mock_mapper.from_orm.assert_called_once_with(
                mock_orm_category, CatalogCategory
            )

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        """Test get_by_id when category not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)

        category_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id(category_id)

        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_success(self) -> None:
        """Test successful get_all."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)

        mock_orm_categories = [MagicMock(spec=CatalogCategoryORM)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_orm_categories

        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_domain_categories = [MagicMock(spec=CatalogCategory)]
            mock_mapper.from_orm_list.return_value = mock_domain_categories

            result = await repo.get_all()

            assert result == mock_domain_categories
            mock_session.execute.assert_called_once()
            mock_mapper.from_orm_list.assert_called_once_with(
                mock_orm_categories, CatalogCategory
            )

    @pytest.mark.asyncio
    async def test_add_success(self) -> None:
        """Test successful add."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)

        mock_domain_category = MagicMock(spec=CatalogCategory)
        mock_orm_category = MagicMock(spec=CatalogCategoryORM)

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_mapper.to_orm.return_value = mock_orm_category
            mock_mapper.from_orm.return_value = mock_domain_category

            result = await repo.add(mock_domain_category)

            assert result == mock_domain_category
            mock_mapper.to_orm.assert_called_once_with(
                mock_domain_category, CatalogCategoryORM
            )
            mock_session.add.assert_called_once_with(mock_orm_category)
            mock_session.flush.assert_called_once()
            mock_mapper.from_orm.assert_called_once_with(
                mock_orm_category, CatalogCategory
            )

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test successful update."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)

        mock_domain_category = MagicMock(spec=CatalogCategory)
        mock_domain_category.id = uuid4()
        mock_orm_category = MagicMock(spec=CatalogCategoryORM)

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_orm_category
        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_mapper.from_orm.return_value = mock_domain_category

            result = await repo.update(mock_domain_category)

            assert result == mock_domain_category
            mock_session.execute.assert_called_once()
            mock_mapper.update_orm_from_domain.assert_called_once_with(
                mock_orm_category, mock_domain_category
            )
            # The update method calls from_orm with the result of update_orm_from_domain
            mock_mapper.from_orm.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Test successful delete."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)

        category_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repo.delete(category_id)

        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test delete when category not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogCategoryRepository(mock_session)

        category_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await repo.delete(category_id)

        assert result is False
        mock_session.execute.assert_called_once()


class TestCatalogBrandRepository:
    """Test CatalogBrandRepository."""

    def test_repository_initialization(self) -> None:
        """Test repository initialization."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)
        assert repo.session == mock_session

    @pytest.mark.asyncio
    async def test_get_by_id_success(self) -> None:
        """Test successful get_by_id."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)

        brand_id = uuid4()
        mock_orm_brand = MagicMock(spec=CatalogBrandORM)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm_brand

        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_domain_brand = MagicMock(spec=CatalogBrand)
            mock_mapper.from_orm.return_value = mock_domain_brand

            result = await repo.get_by_id(brand_id)

            assert result == mock_domain_brand
            mock_session.execute.assert_called_once()
            mock_mapper.from_orm.assert_called_once_with(mock_orm_brand, CatalogBrand)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self) -> None:
        """Test get_by_id when brand not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)

        brand_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id(brand_id)

        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_success(self) -> None:
        """Test successful get_all."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)

        mock_orm_brands = [MagicMock(spec=CatalogBrandORM)]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_orm_brands

        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_domain_brands = [MagicMock(spec=CatalogBrand)]
            mock_mapper.from_orm_list.return_value = mock_domain_brands

            result = await repo.get_all()

            assert result == mock_domain_brands
            mock_session.execute.assert_called_once()
            mock_mapper.from_orm_list.assert_called_once_with(
                mock_orm_brands, CatalogBrand
            )

    @pytest.mark.asyncio
    async def test_add_success(self) -> None:
        """Test successful add."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)

        mock_domain_brand = MagicMock(spec=CatalogBrand)
        mock_orm_brand = MagicMock(spec=CatalogBrandORM)

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_mapper.to_orm.return_value = mock_orm_brand
            mock_mapper.from_orm.return_value = mock_domain_brand

            result = await repo.add(mock_domain_brand)

            assert result == mock_domain_brand
            mock_mapper.to_orm.assert_called_once_with(
                mock_domain_brand, CatalogBrandORM
            )
            mock_session.add.assert_called_once_with(mock_orm_brand)
            mock_session.flush.assert_called_once()
            mock_mapper.from_orm.assert_called_once_with(mock_orm_brand, CatalogBrand)

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Test successful update."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)

        mock_domain_brand = MagicMock(spec=CatalogBrand)
        mock_domain_brand.id = uuid4()
        mock_orm_brand = MagicMock(spec=CatalogBrandORM)

        mock_result = MagicMock()
        mock_result.scalar_one.return_value = mock_orm_brand
        mock_session.execute.return_value = mock_result

        with patch(
            "app.modules.catalog.infrastructure.repositories.ORMMapper"
        ) as mock_mapper:
            mock_mapper.from_orm.return_value = mock_domain_brand

            result = await repo.update(mock_domain_brand)

            assert result == mock_domain_brand
            mock_session.execute.assert_called_once()
            mock_mapper.update_orm_from_domain.assert_called_once_with(
                mock_orm_brand, mock_domain_brand
            )
            # The update method calls from_orm with the result of update_orm_from_domain
            mock_mapper.from_orm.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Test successful delete."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)

        brand_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repo.delete(brand_id)

        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found(self) -> None:
        """Test delete when brand not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = CatalogBrandRepository(mock_session)

        brand_id = uuid4()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await repo.delete(brand_id)

        assert result is False
        mock_session.execute.assert_called_once()


class TestCatalogRepositoriesIntegration:
    """Integration tests for catalog repositories."""

    @pytest.mark.asyncio
    async def test_repository_crud_operations(self) -> None:
        """Test complete CRUD operations for all repositories."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Test item repository
        item_repo = CatalogItemRepository(mock_session)
        assert item_repo.session == mock_session

        # Test category repository
        category_repo = CatalogCategoryRepository(mock_session)
        assert category_repo.session == mock_session

        # Test brand repository
        brand_repo = CatalogBrandRepository(mock_session)
        assert brand_repo.session == mock_session

    @pytest.mark.asyncio
    async def test_repository_error_handling(self) -> None:
        """Test repository error handling."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_session.execute.side_effect = Exception("Database error")

        item_repo = CatalogItemRepository(mock_session)

        with pytest.raises(Exception, match="Database error"):
            await item_repo.get_by_id(uuid4())

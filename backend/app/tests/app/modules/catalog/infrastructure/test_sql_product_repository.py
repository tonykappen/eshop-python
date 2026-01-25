"""Tests for SQL Product repository implementation."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.domain.entities.product.product import Product
from app.modules.catalog.domain.value_objects import Money
from app.modules.catalog.infrastructure.persistence.repositories.products.sql import (
    SqlProductRepository,
)
from app.modules.catalog.infrastructure.persistence.orm.product_orm import ProductORM


class TestProductRepositoryGetById:
    """Test get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self):
        """Test successful get by ID."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        product_id = uuid4()
        mock_orm = MagicMock(spec=ProductORM)
        mock_orm.id = product_id
        mock_orm.is_deleted = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm
        mock_session.execute.return_value = mock_result

        with patch.object(repo, '_orm_to_domain') as mock_mapper:
            mock_product = MagicMock(spec=Product)
            mock_mapper.return_value = mock_product
            
            result = await repo.get_by_id(product_id)
            
            assert result == mock_product
            mock_session.execute.assert_called_once()
            mock_mapper.assert_called_once_with(mock_orm)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        """Test get by ID when product not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        product_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id(product_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_excludes_deleted(self):
        """Test get by ID excludes deleted products."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        product_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Deleted products filtered out
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id(product_id)
        
        assert result is None


class TestProductRepositoryGetBySku:
    """Test get_by_sku method."""

    @pytest.mark.asyncio
    async def test_get_by_sku_success(self):
        """Test successful get by SKU."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        sku = "TEST-001"
        mock_orm = MagicMock(spec=ProductORM)
        mock_orm.sku = sku
        mock_orm.is_deleted = False
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_orm
        mock_session.execute.return_value = mock_result

        with patch.object(repo, '_orm_to_domain') as mock_mapper:
            mock_product = MagicMock(spec=Product)
            mock_mapper.return_value = mock_product
            
            result = await repo.get_by_sku(sku)
            
            assert result == mock_product
            mock_mapper.assert_called_once_with(mock_orm)

    @pytest.mark.asyncio
    async def test_get_by_sku_not_found(self):
        """Test get by SKU when product not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        sku = "NONEXISTENT"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_sku(sku)
        
        assert result is None


class TestProductRepositoryAdd:
    """Test add method."""

    @pytest.mark.asyncio
    async def test_add_product_success(self):
        """Test successful product addition."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        mock_orm = MagicMock(spec=ProductORM)
        mock_orm.id = product_id
        
        with patch.object(repo, '_domain_to_orm') as mock_domain_to_orm, \
             patch.object(repo, '_orm_to_domain') as mock_orm_to_domain:
            mock_domain_to_orm.return_value = mock_orm
            mock_orm_to_domain.return_value = product  # Return the same product after refresh
            
            result = await repo.add(product)
            
            assert result == product
            mock_session.add.assert_called_once_with(mock_orm)
            mock_session.flush.assert_called_once()
            mock_domain_to_orm.assert_called_once_with(product)
            mock_orm_to_domain.assert_called_once_with(mock_orm)


class TestProductRepositoryUpdate:
    """Test update method."""

    @pytest.mark.asyncio
    async def test_update_product_success(self):
        """Test successful product update."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        product_id = uuid4()
        price = Money(amount=Decimal("99.99"), currency="USD")
        product = Product.create(
            product_id=product_id,
            name="Test Product",
            sku="TEST-001",
            category=["Electronics"],
            description="A test product",
            price=price,
        )

        # Mock get_by_id to return the product (update calls get_by_id at the end)
        with patch.object(repo, 'get_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = product
            
            result = await repo.update(product)
            
            assert result == product
            mock_session.execute.assert_called()
            mock_session.flush.assert_called_once()
            mock_get_by_id.assert_called_once_with(product_id)


class TestProductRepositoryDelete:
    """Test delete method."""

    @pytest.mark.asyncio
    async def test_delete_product_success(self):
        """Test successful product deletion."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        product_id = uuid4()
        deleted_by = uuid4()
        
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        result = await repo.delete(product_id, deleted_by=deleted_by, deletion_reason="Test deletion")
        
        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_product_not_found(self):
        """Test delete when product not found."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        product_id = uuid4()
        
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        result = await repo.delete(product_id)
        
        assert result is False


class TestProductRepositoryGetAll:
    """Test get_all method."""

    @pytest.mark.asyncio
    async def test_get_all_products_success(self):
        """Test successful get all products."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        mock_orm1 = MagicMock(spec=ProductORM)
        mock_orm2 = MagicMock(spec=ProductORM)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_orm1, mock_orm2]
        mock_session.execute.return_value = mock_result

        with patch.object(repo, '_orm_to_domain') as mock_mapper:
            mock_product1 = MagicMock(spec=Product)
            mock_product2 = MagicMock(spec=Product)
            mock_mapper.side_effect = [mock_product1, mock_product2]
            
            result = await repo.get_all(skip=0, limit=10)
            
            assert len(result) == 2
            assert result[0] == mock_product1
            assert result[1] == mock_product2
            assert mock_mapper.call_count == 2


class TestProductRepositoryGetByCategory:
    """Test get_by_category method."""

    @pytest.mark.asyncio
    async def test_get_by_category_success(self):
        """Test successful get by category."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        category = "Electronics"
        mock_orm1 = MagicMock(spec=ProductORM)
        mock_orm2 = MagicMock(spec=ProductORM)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_orm1, mock_orm2]
        mock_session.execute.return_value = mock_result

        with patch.object(repo, '_orm_to_domain') as mock_mapper:
            mock_product1 = MagicMock(spec=Product)
            mock_product2 = MagicMock(spec=Product)
            mock_mapper.side_effect = [mock_product1, mock_product2]
            
            result = await repo.get_by_category(category)
            
            assert len(result) == 2
            assert result[0] == mock_product1
            assert result[1] == mock_product2

    @pytest.mark.asyncio
    async def test_get_by_category_with_pagination(self):
        """Test get by category with pagination."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        category = "Electronics"
        mock_orm1 = MagicMock(spec=ProductORM)
        
        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        
        # Mock products result
        mock_products_result = MagicMock()
        mock_products_result.scalars.return_value.all.return_value = [mock_orm1]
        
        mock_session.execute.side_effect = [mock_count_result, mock_products_result]

        with patch.object(repo, '_orm_to_domain') as mock_mapper:
            mock_product1 = MagicMock(spec=Product)
            mock_mapper.return_value = mock_product1
            
            products, total_count = await repo.get_by_category(category, page=1, page_size=10)
            
            assert len(products) == 1
            assert total_count == 1
            assert products[0] == mock_product1


class TestProductRepositoryExists:
    """Test exists methods."""

    @pytest.mark.asyncio
    async def test_exists_by_sku_true(self):
        """Test exists by SKU returns True."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        sku = "TEST-001"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()  # Product exists
        mock_session.execute.return_value = mock_result

        result = await repo.exists_by_sku(sku)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_by_sku_false(self):
        """Test exists by SKU returns False."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        sku = "NONEXISTENT"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repo.exists_by_sku(sku)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_by_name_true(self):
        """Test exists by name returns True."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        name = "Test Product"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = uuid4()  # Product exists
        mock_session.execute.return_value = mock_result

        result = await repo.exists_by_name(name)
        
        assert result is True


class TestProductRepositoryCount:
    """Test count method."""

    @pytest.mark.asyncio
    async def test_count_products(self):
        """Test counting products."""
        mock_session = AsyncMock(spec=AsyncSession)
        repo = SqlProductRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        result = await repo.count()
        
        assert result == 5


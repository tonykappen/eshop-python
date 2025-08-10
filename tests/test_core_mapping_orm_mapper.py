"""Tests for ORM mapper functionality."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase

from eshop.core.domain.entity import Entity
from eshop.core.mapping.orm_mapper import (
    ORMMapper,
    from_orm,
    from_orm_list,
    to_orm,
    to_orm_list,
    update_orm_from_domain,
)


class MockDeclarativeBase(DeclarativeBase):
    """Mock declarative base for testing."""


class MockORMModel(MockDeclarativeBase):
    """Mock ORM model for testing."""
    __tablename__ = "mock_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(String(500))
    created_at = Column(DateTime)
    uuid_field = Column(String(36))


class MockORMModelWithTable(MockDeclarativeBase):
    """Mock ORM model with table for testing."""
    __tablename__ = "mock_table_with_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))


class MockDomainEntity(Entity):
    """Mock domain entity for testing."""
    
    def __init__(self, id: int, name: str, description: str, created_at: datetime, uuid_field: UUID) -> None:
        super().__init__()
        self.id = id
        self.name = name
        self.description = description
        self.created_at = created_at
        self.uuid_field = uuid_field


class MockPydanticEntity(BaseModel):
    """Mock Pydantic-based domain entity for testing."""
    
    id: int
    name: str
    description: str
    created_at: datetime
    uuid_field: UUID


class MockEntityWithoutDict(Entity):
    """Mock entity without __dict__ for testing."""
    
    def __init__(self, id: int, name: str) -> None:
        super().__init__()
        self._id = id
        self._name = name
    
    @property
    def id(self) -> int:
        return self._id
    
    @property
    def name(self) -> str:
        return self._id


class TestORMMapper:
    """Test ORM mapper functionality."""

    def test_to_orm_with_none_entity(self) -> None:
        """Test converting None entity to ORM."""
        result = ORMMapper.to_orm(None, MockORMModel)
        assert result is None

    def test_to_orm_with_pydantic_entity(self) -> None:
        """Test converting Pydantic entity to ORM."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        entity = MockPydanticEntity(
            id=1,
            name="Test Product",
            description="Test Description",
            created_at=test_datetime,
            uuid_field=test_uuid,
        )
        
        orm_model = ORMMapper.to_orm(entity, MockORMModel)
        
        assert isinstance(orm_model, MockORMModel)
        assert orm_model.id == 1
        assert orm_model.name == "Test Product"
        assert orm_model.description == "Test Description"
        assert orm_model.created_at == test_datetime
        assert orm_model.uuid_field == str(test_uuid)

    def test_to_orm_with_regular_entity(self) -> None:
        """Test converting regular entity to ORM."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        entity = MockDomainEntity(
            id=1,
            name="Test Product",
            description="Test Description",
            created_at=test_datetime,
            uuid_field=test_uuid,
        )
        
        orm_model = ORMMapper.to_orm(entity, MockORMModel)
        
        assert isinstance(orm_model, MockORMModel)
        assert orm_model.id == 1
        assert orm_model.name == "Test Product"
        assert orm_model.description == "Test Description"
        assert orm_model.created_at == test_datetime
        assert orm_model.uuid_field == str(test_uuid)

    def test_to_orm_with_entity_without_dict(self) -> None:
        """Test converting entity without __dict__ to ORM."""
        entity = MockEntityWithoutDict(id=1, name="Test")
        
        with pytest.raises(ValueError, match="Cannot convert domain entity"):
            ORMMapper.to_orm(entity, MockORMModel)

    def test_to_orm_filters_fields(self) -> None:
        """Test that ORM conversion filters out non-existent fields."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        entity = MockPydanticEntity(
            id=1,
            name="Test Product",
            description="Test Description",
            created_at=test_datetime,
            uuid_field=test_uuid,
        )
        
        # Add extra field that doesn't exist in ORM model
        entity.extra_field = "extra_value"
        
        orm_model = ORMMapper.to_orm(entity, MockORMModel)
        
        assert not hasattr(orm_model, "extra_field")
        assert orm_model.id == 1
        assert orm_model.name == "Test Product"

    def test_to_orm_converts_uuid_list(self) -> None:
        """Test that UUID lists are converted properly."""
        test_uuids = [uuid4(), uuid4()]
        entity = MockPydanticEntity(
            id=1,
            name="Test",
            description="Test",
            created_at=datetime.now(),
            uuid_field=uuid4(),
        )
        entity.uuid_list = test_uuids
        
        orm_model = ORMMapper.to_orm(entity, MockORMModel)
        
        # The uuid_list should be converted to strings
        assert hasattr(orm_model, "uuid_list")
        assert orm_model.uuid_list == [str(uuid) for uuid in test_uuids]

    def test_from_orm_with_none_model(self) -> None:
        """Test converting None ORM model to entity."""
        result = ORMMapper.from_orm(None, MockPydanticEntity)
        assert result is None

    def test_from_orm_to_pydantic_entity(self) -> None:
        """Test converting ORM model to Pydantic entity."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        orm_model = MockORMModel(
            id=1,
            name="Test Product",
            description="Test Description",
            created_at=test_datetime,
            uuid_field=str(test_uuid),
        )
        
        entity = ORMMapper.from_orm(orm_model, MockPydanticEntity)
        
        assert isinstance(entity, MockPydanticEntity)
        assert entity.id == 1
        assert entity.name == "Test Product"
        assert entity.description == "Test Description"
        assert entity.created_at == test_datetime
        assert entity.uuid_field == test_uuid

    def test_from_orm_to_regular_entity(self) -> None:
        """Test converting ORM model to regular entity."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        orm_model = MockORMModel(
            id=1,
            name="Test Product",
            description="Test Description",
            created_at=test_datetime,
            uuid_field=str(test_uuid),
        )
        
        entity = ORMMapper.from_orm(orm_model, MockDomainEntity)
        
        assert isinstance(entity, MockDomainEntity)
        assert entity.id == 1
        assert entity.name == "Test Product"
        assert entity.description == "Test Description"
        assert entity.created_at == test_datetime
        assert entity.uuid_field == test_uuid

    def test_to_orm_list_empty(self) -> None:
        """Test converting empty list of entities."""
        result = ORMMapper.to_orm_list([], MockORMModel)
        assert result == []

    def test_to_orm_list_with_entities(self) -> None:
        """Test converting list of entities to ORM models."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        entities = [
            MockPydanticEntity(
                id=1,
                name="Product 1",
                description="Description 1",
                created_at=test_datetime,
                uuid_field=test_uuid,
            ),
            MockPydanticEntity(
                id=2,
                name="Product 2",
                description="Description 2",
                created_at=test_datetime,
                uuid_field=test_uuid,
            ),
        ]
        
        orm_models = ORMMapper.to_orm_list(entities, MockORMModel)
        
        assert len(orm_models) == 2
        assert all(isinstance(model, MockORMModel) for model in orm_models)
        assert orm_models[0].id == 1
        assert orm_models[1].id == 2

    def test_from_orm_list_empty(self) -> None:
        """Test converting empty list of ORM models."""
        result = ORMMapper.from_orm_list([], MockPydanticEntity)
        assert result == []

    def test_from_orm_list_with_models(self) -> None:
        """Test converting list of ORM models to entities."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        orm_models = [
            MockORMModel(
                id=1,
                name="Product 1",
                description="Description 1",
                created_at=test_datetime,
                uuid_field=str(test_uuid),
            ),
            MockORMModel(
                id=2,
                name="Product 2",
                description="Description 2",
                created_at=test_datetime,
                uuid_field=str(test_uuid),
            ),
        ]
        
        entities = ORMMapper.from_orm_list(orm_models, MockPydanticEntity)
        
        assert len(entities) == 2
        assert all(isinstance(entity, MockPydanticEntity) for entity in entities)
        assert entities[0].id == 1
        assert entities[1].id == 2

    def test_update_orm_from_domain_none_values(self) -> None:
        """Test updating ORM model with None values."""
        orm_model = MockORMModel(id=1, name="Original")
        result = ORMMapper.update_orm_from_domain(None, None)
        assert result == orm_model

    def test_update_orm_from_domain_success(self) -> None:
        """Test successfully updating ORM model from domain entity."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        orm_model = MockORMModel(
            id=1,
            name="Original Name",
            description="Original Description",
            created_at=datetime.now(),
            uuid_field=str(uuid4()),
        )
        
        entity = MockPydanticEntity(
            id=1,
            name="Updated Name",
            description="Updated Description",
            created_at=test_datetime,
            uuid_field=test_uuid,
        )
        
        updated_model = ORMMapper.update_orm_from_domain(orm_model, entity)
        
        assert updated_model is orm_model
        assert orm_model.name == "Updated Name"
        assert orm_model.description == "Updated Description"
        assert orm_model.created_at == test_datetime
        assert orm_model.uuid_field == str(test_uuid)

    def test_extract_orm_data_with_table(self) -> None:
        """Test extracting data from ORM model with table."""
        test_datetime = datetime.now()
        orm_model = MockORMModelWithTable(
            id=1,
            name="Test Name",
            email="test@example.com",
        )
        
        data = ORMMapper._extract_orm_data(orm_model)
        
        assert data["id"] == 1
        assert data["name"] == "Test Name"
        assert data["email"] == "test@example.com"

    def test_extract_orm_data_without_table(self) -> None:
        """Test extracting data from ORM model without table."""
        class MockModelWithoutTable:
            def __init__(self) -> None:
                self.id = 1
                self.name = "Test"
                self._private = "private"
        
        orm_model = MockModelWithoutTable()
        data = ORMMapper._extract_orm_data(orm_model)
        
        assert data["id"] == 1
        assert data["name"] == "Test"
        assert "_private" not in data

    def test_get_orm_model_fields_with_table(self) -> None:
        """Test getting fields from ORM model with table."""
        fields = ORMMapper._get_orm_model_fields(MockORMModelWithTable)
        
        assert "id" in fields
        assert "name" in fields
        assert "email" in fields

    def test_get_orm_model_fields_without_table(self) -> None:
        """Test getting fields from ORM model without table."""
        class MockModelWithoutTable:
            def __init__(self, id: int, name: str) -> None:
                pass
        
        fields = ORMMapper._get_orm_model_fields(MockModelWithoutTable)
        
        assert "id" in fields
        assert "name" in fields

    def test_convert_uuids_for_orm(self) -> None:
        """Test converting UUIDs for ORM storage."""
        test_uuid = uuid4()
        data = {
            "id": 1,
            "uuid_field": test_uuid,
            "uuid_list": [test_uuid, uuid4()],
            "string_field": "test",
        }
        
        converted = ORMMapper._convert_uuids_for_orm(data)
        
        assert converted["id"] == 1
        assert converted["uuid_field"] == str(test_uuid)
        assert len(converted["uuid_list"]) == 2
        assert all(isinstance(uuid_str, str) for uuid_str in converted["uuid_list"])
        assert converted["string_field"] == "test"

    def test_convert_types_for_domain(self) -> None:
        """Test converting types for domain entity."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        data = {
            "id": "1",  # String that should be converted to int
            "uuid_field": str(test_uuid),  # String that should be converted to UUID
            "created_at": test_datetime.isoformat(),  # String that should be converted to datetime
            "name": "Test",  # String that should remain string
        }
        
        converted = ORMMapper._convert_types_for_domain(data, MockPydanticEntity)
        
        assert converted["id"] == 1
        assert converted["uuid_field"] == test_uuid
        assert isinstance(converted["created_at"], datetime)
        assert converted["name"] == "Test"

    def test_convert_single_value_uuid(self) -> None:
        """Test converting single value to UUID."""
        test_uuid = uuid4()
        
        # String to UUID
        result = ORMMapper._convert_single_value(str(test_uuid), UUID)
        assert result == test_uuid
        
        # UUID to UUID
        result = ORMMapper._convert_single_value(test_uuid, UUID)
        assert result == test_uuid
        
        # None to UUID
        result = ORMMapper._convert_single_value(None, UUID)
        assert result is None

    def test_convert_single_value_datetime(self) -> None:
        """Test converting single value to datetime."""
        test_datetime = datetime.now()
        
        # String to datetime
        result = ORMMapper._convert_single_value(test_datetime.isoformat(), datetime)
        assert isinstance(result, datetime)
        
        # Datetime to datetime
        result = ORMMapper._convert_single_value(test_datetime, datetime)
        assert result == test_datetime
        
        # None to datetime
        result = ORMMapper._convert_single_value(None, datetime)
        assert result is None

    def test_convert_single_value_optional_type(self) -> None:
        """Test converting single value with optional type."""
        from typing import Optional
        
        test_uuid = uuid4()
        
        # String to Optional[UUID]
        result = ORMMapper._convert_single_value(str(test_uuid), Optional[UUID])
        assert result == test_uuid
        
        # None to Optional[UUID]
        result = ORMMapper._convert_single_value(None, Optional[UUID])
        assert result is None

    def test_convert_single_value_direct_conversion(self) -> None:
        """Test direct type conversion."""
        # String to int
        result = ORMMapper._convert_single_value("123", int)
        assert result == 123
        
        # String to float
        result = ORMMapper._convert_single_value("123.45", float)
        assert result == 123.45

    def test_convert_single_value_failed_conversion(self) -> None:
        """Test failed type conversion."""
        # Invalid string to int should return original value
        result = ORMMapper._convert_single_value("invalid", int)
        assert result == "invalid"


class TestORMMapperConvenienceFunctions:
    """Test convenience functions for ORM mapping."""

    def test_to_orm_function(self) -> None:
        """Test to_orm convenience function."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        entity = MockPydanticEntity(
            id=1,
            name="Test",
            description="Test",
            created_at=test_datetime,
            uuid_field=test_uuid,
        )
        
        orm_model = to_orm(entity, MockORMModel)
        
        assert isinstance(orm_model, MockORMModel)
        assert orm_model.id == 1

    def test_from_orm_function(self) -> None:
        """Test from_orm convenience function."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        orm_model = MockORMModel(
            id=1,
            name="Test",
            description="Test",
            created_at=test_datetime,
            uuid_field=str(test_uuid),
        )
        
        entity = from_orm(orm_model, MockPydanticEntity)
        
        assert isinstance(entity, MockPydanticEntity)
        assert entity.id == 1

    def test_to_orm_list_function(self) -> None:
        """Test to_orm_list convenience function."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        entities = [
            MockPydanticEntity(
                id=1,
                name="Test 1",
                description="Test",
                created_at=test_datetime,
                uuid_field=test_uuid,
            ),
            MockPydanticEntity(
                id=2,
                name="Test 2",
                description="Test",
                created_at=test_datetime,
                uuid_field=test_uuid,
            ),
        ]
        
        orm_models = to_orm_list(entities, MockORMModel)
        
        assert len(orm_models) == 2
        assert all(isinstance(model, MockORMModel) for model in orm_models)

    def test_from_orm_list_function(self) -> None:
        """Test from_orm_list convenience function."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        orm_models = [
            MockORMModel(
                id=1,
                name="Test 1",
                description="Test",
                created_at=test_datetime,
                uuid_field=str(test_uuid),
            ),
            MockORMModel(
                id=2,
                name="Test 2",
                description="Test",
                created_at=test_datetime,
                uuid_field=str(test_uuid),
            ),
        ]
        
        entities = from_orm_list(orm_models, MockPydanticEntity)
        
        assert len(entities) == 2
        assert all(isinstance(entity, MockPydanticEntity) for entity in entities)

    def test_update_orm_from_domain_function(self) -> None:
        """Test update_orm_from_domain convenience function."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        orm_model = MockORMModel(
            id=1,
            name="Original",
            description="Original",
            created_at=datetime.now(),
            uuid_field=str(uuid4()),
        )
        
        entity = MockPydanticEntity(
            id=1,
            name="Updated",
            description="Updated",
            created_at=test_datetime,
            uuid_field=test_uuid,
        )
        
        updated_model = update_orm_from_domain(orm_model, entity)
        
        assert updated_model is orm_model
        assert orm_model.name == "Updated"


class TestORMMapperErrorHandling:
    """Test error handling in ORM mapper."""

    def test_to_orm_conversion_error(self) -> None:
        """Test error handling during entity to ORM conversion."""
        # Create entity with invalid data that will cause conversion error
        entity = MockPydanticEntity(
            id=1,
            name="Test",
            description="Test",
            created_at=datetime.now(),
            uuid_field=uuid4(),
        )
        
        # Mock ORM model class that will raise error during instantiation
        class ErrorORMModel:
            def __init__(self, **kwargs: Any) -> None:
                raise ValueError("ORM model creation failed")
        
        with pytest.raises(ValueError, match="Failed to convert"):
            ORMMapper.to_orm(entity, ErrorORMModel)

    def test_from_orm_conversion_error(self) -> None:
        """Test error handling during ORM to entity conversion."""
        orm_model = MockORMModel(
            id=1,
            name="Test",
            description="Test",
            created_at=datetime.now(),
            uuid_field=str(uuid4()),
        )
        
        # Mock entity class that will raise error during instantiation
        class ErrorEntity:
            def __init__(self, **kwargs: Any) -> None:
                raise ValueError("Entity creation failed")
        
        with pytest.raises(ValueError, match="Failed to convert"):
            ORMMapper.from_orm(orm_model, ErrorEntity)

    def test_update_orm_conversion_error(self) -> None:
        """Test error handling during ORM update."""
        orm_model = MockORMModel(
            id=1,
            name="Original",
            description="Original",
            created_at=datetime.now(),
            uuid_field=str(uuid4()),
        )
        
        entity = MockPydanticEntity(
            id=1,
            name="Updated",
            description="Updated",
            created_at=datetime.now(),
            uuid_field=uuid4(),
        )
        
        # Mock setattr to raise error
        with patch.object(orm_model, "__setattr__", side_effect=Exception("Setattr failed")):
            with pytest.raises(ValueError, match="Failed to update"):
                ORMMapper.update_orm_from_domain(orm_model, entity)


class TestORMMapperIntegration:
    """Integration tests for ORM mapper."""

    def test_full_conversion_cycle(self) -> None:
        """Test full conversion cycle: entity -> ORM -> entity."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        original_entity = MockPydanticEntity(
            id=1,
            name="Test Product",
            description="Test Description",
            created_at=test_datetime,
            uuid_field=test_uuid,
        )
        
        # Entity to ORM
        orm_model = ORMMapper.to_orm(original_entity, MockORMModel)
        
        # ORM to Entity
        converted_entity = ORMMapper.from_orm(orm_model, MockPydanticEntity)
        
        # Verify data integrity
        assert converted_entity.id == original_entity.id
        assert converted_entity.name == original_entity.name
        assert converted_entity.description == original_entity.description
        assert converted_entity.created_at == original_entity.created_at
        assert converted_entity.uuid_field == original_entity.uuid_field

    def test_bulk_conversion_cycle(self) -> None:
        """Test bulk conversion cycle with lists."""
        test_uuid = uuid4()
        test_datetime = datetime.now()
        original_entities = [
            MockPydanticEntity(
                id=1,
                name="Product 1",
                description="Description 1",
                created_at=test_datetime,
                uuid_field=test_uuid,
            ),
            MockPydanticEntity(
                id=2,
                name="Product 2",
                description="Description 2",
                created_at=test_datetime,
                uuid_field=test_uuid,
            ),
        ]
        
        # Entities to ORM models
        orm_models = ORMMapper.to_orm_list(original_entities, MockORMModel)
        
        # ORM models to Entities
        converted_entities = ORMMapper.from_orm_list(orm_models, MockPydanticEntity)
        
        # Verify data integrity
        assert len(converted_entities) == len(original_entities)
        for original, converted in zip(original_entities, converted_entities):
            assert converted.id == original.id
            assert converted.name == original.name
            assert converted.description == original.description
            assert converted.created_at == original.created_at
            assert converted.uuid_field == original.uuid_field

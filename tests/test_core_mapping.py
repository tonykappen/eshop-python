"""Tests for the mapping module."""

import json
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import BaseModel

from eshop.core.mapping.mapper import (
    MsgspecMapper,
    from_json,
    from_redis,
    map_list_to_dtos,
    map_list_to_entities,
    map_to_dto,
    map_to_entity,
    to_json,
    to_redis,
)


@pytest.mark.no_collect
class TestDTO(BaseModel):
    """Test DTO for mapping tests."""

    id: int
    name: str
    active: bool = True


@pytest.mark.no_collect
class TestEntity:
    """Test entity for mapping tests."""

    def __init__(self, id: int, name: str, active: bool = True):
        self.id = id
        self.name = name
        self.active = active

    def model_dump(self) -> dict[str, Any]:
        """Convert to dict for mapping."""
        return {"id": self.id, "name": self.name, "active": self.active}


@pytest.mark.no_collect
class TestNestedDTO(BaseModel):
    """Test DTO with nested objects."""

    id: int
    nested: TestDTO
    items: list[TestDTO]


@pytest.mark.no_collect
class TestNestedEntity:
    """Test entity with nested objects."""

    def __init__(self, id: int, nested: TestEntity, items: list[TestEntity]):
        self.id = id
        self.nested = nested
        self.items = items

    def model_dump(self) -> dict[str, Any]:
        """Convert to dict for mapping."""
        return {
            "id": self.id,
            "nested": self.nested.model_dump(),
            "items": [item.model_dump() for item in self.items],
        }


class TestMsgspecMapper:
    """Test MsgspecMapper class."""

    def test_map_to_dto_from_pydantic_model(self) -> None:
        """Test mapping from Pydantic model to DTO."""
        entity = TestEntity(1, "test", True)

        with patch("msgspec.convert") as mock_convert:
            mock_dto = TestDTO(id=1, name="test", active=True)
            mock_convert.return_value = mock_dto

            result = MsgspecMapper.map_to_dto(entity, TestDTO)

            assert isinstance(result, TestDTO)
            assert result.id == 1
            assert result.name == "test"
            assert result.active is True

    def test_map_to_dto_from_regular_class(self) -> None:
        """Test mapping from regular class to DTO."""

        class RegularClass:
            def __init__(self) -> None:
                self.id = 2
                self.name = "regular"
                self.active = False

        entity = RegularClass()

        with patch("msgspec.convert") as mock_convert:
            mock_dto = TestDTO(id=2, name="regular", active=False)
            mock_convert.return_value = mock_dto

            result = MsgspecMapper.map_to_dto(entity, TestDTO)

            assert isinstance(result, TestDTO)
            assert result.id == 2
            assert result.name == "regular"
            assert result.active is False

    def test_map_to_dto_invalid_object_type(self) -> None:
        """Test mapping with invalid object type."""
        invalid_obj = "not a valid object"

        with pytest.raises(ValueError, match="Cannot map object of type"):
            MsgspecMapper.map_to_dto(invalid_obj, TestDTO)

    def test_map_to_dto_conversion_error(self) -> None:
        """Test mapping with conversion error."""
        entity = TestEntity(1, "test", True)

        with patch("msgspec.convert") as mock_convert:
            mock_convert.side_effect = Exception("Conversion failed")

            with pytest.raises(ValueError, match="Failed to convert to DTO"):
                MsgspecMapper.map_to_dto(entity, TestDTO)

    def test_map_to_entity_from_pydantic_model(self) -> None:
        """Test mapping from Pydantic model to entity."""
        dto = TestDTO(id=3, name="dto_test", active=True)

        with patch("msgspec.convert") as mock_convert:
            mock_entity = TestEntity(3, "dto_test", True)
            mock_convert.return_value = mock_entity

            result = MsgspecMapper.map_to_entity(dto, TestEntity)

            assert result == mock_entity
            mock_convert.assert_called_once()

    def test_map_to_entity_from_regular_class(self) -> None:
        """Test mapping from regular class to entity."""

        class RegularDTO:
            def __init__(self) -> None:
                self.id = 4
                self.name = "regular_dto"
                self.active = False

        dto = RegularDTO()

        with patch("msgspec.convert") as mock_convert:
            mock_entity = TestEntity(4, "regular_dto", False)
            mock_convert.return_value = mock_entity

            result = MsgspecMapper.map_to_entity(dto, TestEntity)

            assert result == mock_entity

    def test_map_to_entity_invalid_object_type(self) -> None:
        """Test mapping with invalid object type."""
        invalid_obj = 123

        with pytest.raises(ValueError, match="Cannot map object of type"):
            MsgspecMapper.map_to_entity(invalid_obj, TestEntity)

    def test_map_list_to_dtos(self) -> None:
        """Test mapping list of entities to DTOs."""
        entities = [
            TestEntity(1, "first"),
            TestEntity(2, "second"),
            TestEntity(3, "third"),
        ]

        with patch("msgspec.convert") as mock_convert:
            mock_dtos = [
                TestDTO(id=1, name="first"),
                TestDTO(id=2, name="second"),
                TestDTO(id=3, name="third"),
            ]
            mock_convert.side_effect = mock_dtos

            result = MsgspecMapper.map_list_to_dtos(entities, TestDTO)

            assert len(result) == 3
            assert all(isinstance(dto, TestDTO) for dto in result)
            assert result[0].id == 1
            assert result[1].id == 2
            assert result[2].id == 3

    def test_map_list_to_entities(self) -> None:
        """Test mapping list of DTOs to entities."""
        dtos = [
            TestDTO(id=1, name="first"),
            TestDTO(id=2, name="second"),
            TestDTO(id=3, name="third"),
        ]

        with patch("msgspec.convert") as mock_convert:
            mock_entities = [
                TestEntity(1, "first"),
                TestEntity(2, "second"),
                TestEntity(3, "third"),
            ]
            mock_convert.side_effect = mock_entities

            result = MsgspecMapper.map_list_to_entities(dtos, TestEntity)

            assert len(result) == 3
            assert all(isinstance(entity, TestEntity) for entity in result)

    def test_to_json(self) -> None:
        """Test JSON serialization."""
        obj = {"id": 1, "name": "test", "active": True}

        with patch("msgspec.json.encode") as mock_encode:
            mock_encode.return_value = b'{"id": 1, "name": "test", "active": true}'

            result = MsgspecMapper.to_json(obj)

            assert result == '{"id": 1, "name": "test", "active": true}'
            mock_encode.assert_called_once_with(obj)

    def test_from_json(self) -> None:
        """Test JSON deserialization."""
        json_str = '{"id": 1, "name": "test", "active": true}'

        with patch("msgspec.json.decode") as mock_decode:
            mock_dto = TestDTO(id=1, name="test", active=True)
            mock_decode.return_value = mock_dto

            result = MsgspecMapper.from_json(json_str, TestDTO)

            assert result == mock_dto
            mock_decode.assert_called_once_with(json_str, type=TestDTO)

    def test_to_redis(self) -> None:
        """Test Redis serialization."""
        obj = {"id": 1, "name": "test"}

        with patch("msgspec.msgpack.encode") as mock_encode:
            mock_encode.return_value = b"\x82\xa2id\x01\xa4name\xa4test"

            result = MsgspecMapper.to_redis(obj)

            assert result == b"\x82\xa2id\x01\xa4name\xa4test"
            mock_encode.assert_called_once_with(obj)

    def test_from_redis(self) -> None:
        """Test Redis deserialization."""
        data = b"\x82\xa2id\x01\xa4name\xa4test"

        with patch("msgspec.msgpack.decode") as mock_decode:
            mock_dto = TestDTO(id=1, name="test")
            mock_decode.return_value = mock_dto

            result = MsgspecMapper.from_redis(data, TestDTO)

            assert result == mock_dto
            mock_decode.assert_called_once_with(data, type=TestDTO)

    def test_convert_nested_object_dict(self) -> None:
        """Test nested object conversion with dict."""
        nested_dict = {"key": "value", "nested": {"inner": "data"}}
        result = MsgspecMapper._convert_nested_object(nested_dict)

        assert result == {"key": "value", "nested": {"inner": "data"}}

    def test_convert_nested_object_list(self) -> None:
        """Test nested object conversion with list."""
        nested_list = [{"id": 1}, {"id": 2}]
        result = MsgspecMapper._convert_nested_object(nested_list)

        assert result == [{"id": 1}, {"id": 2}]

    def test_convert_nested_object_pydantic_model(self) -> None:
        """Test nested object conversion with Pydantic model."""
        dto = TestDTO(id=1, name="test")
        result = MsgspecMapper._convert_nested_object(dto)

        assert result == {"id": 1, "name": "test", "active": True}

    def test_convert_nested_object_regular_class(self) -> None:
        """Test nested object conversion with regular class."""

        class RegularClass:
            def __init__(self) -> None:
                self.value = "test"

        obj = RegularClass()
        result = MsgspecMapper._convert_nested_object(obj)

        assert result == {"value": "test"}

    def test_convert_nested_object_primitive(self) -> None:
        """Test nested object conversion with primitive types."""
        assert MsgspecMapper._convert_nested_object("string") == "string"
        assert MsgspecMapper._convert_nested_object(123) == 123
        assert MsgspecMapper._convert_nested_object(True) is True
        assert MsgspecMapper._convert_nested_object(None) is None

    def test_convert_to_dto_with_nested_objects(self) -> None:
        """Test DTO conversion with nested objects."""
        nested_entity = TestEntity(2, "nested")
        entity = TestNestedEntity(1, nested_entity, [nested_entity])

        with patch("msgspec.convert") as mock_convert:
            mock_dto = TestNestedDTO(
                id=1,
                nested=TestDTO(id=2, name="nested"),
                items=[TestDTO(id=2, name="nested")],
            )
            mock_convert.return_value = mock_dto

            result = MsgspecMapper._convert_to_dto(entity.model_dump(), TestNestedDTO)

            assert result == mock_dto

    def test_convert_to_entity_with_nested_objects(self) -> None:
        """Test entity conversion with nested objects."""
        nested_dto = TestDTO(id=2, name="nested")
        dto = TestNestedDTO(id=1, nested=nested_dto, items=[nested_dto])

        with patch("msgspec.convert") as mock_convert:
            mock_entity = TestNestedEntity(
                1, TestEntity(2, "nested"), [TestEntity(2, "nested")]
            )
            mock_convert.return_value = mock_entity

            result = MsgspecMapper._convert_to_entity(
                dto.model_dump(), TestNestedEntity
            )

            assert result == mock_entity


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_map_to_dto_function(self) -> None:
        """Test map_to_dto convenience function."""
        entity = TestEntity(1, "test")

        with patch("eshop.core.mapping.mapper.MsgspecMapper.map_to_dto") as mock_mapper:
            mock_dto = TestDTO(id=1, name="test")
            mock_mapper.return_value = mock_dto

            result = map_to_dto(entity, TestDTO)

            assert result == mock_dto
            mock_mapper.assert_called_once_with(entity, TestDTO)

    def test_map_to_entity_function(self) -> None:
        """Test map_to_entity convenience function."""
        dto = TestDTO(id=1, name="test")

        with patch(
            "eshop.core.mapping.mapper.MsgspecMapper.map_to_entity"
        ) as mock_mapper:
            mock_entity = TestEntity(1, "test")
            mock_mapper.return_value = mock_entity

            result = map_to_entity(dto, TestEntity)

            assert result == mock_entity
            mock_mapper.assert_called_once_with(dto, TestEntity)

    def test_map_list_to_dtos_function(self) -> None:
        """Test map_list_to_dtos convenience function."""
        entities = [TestEntity(1, "test")]

        with patch(
            "eshop.core.mapping.mapper.MsgspecMapper.map_list_to_dtos"
        ) as mock_mapper:
            mock_dtos = [TestDTO(id=1, name="test")]
            mock_mapper.return_value = mock_dtos

            result = map_list_to_dtos(entities, TestDTO)

            assert result == mock_dtos
            mock_mapper.assert_called_once_with(entities, TestDTO)

    def test_map_list_to_entities_function(self) -> None:
        """Test map_list_to_entities convenience function."""
        dtos = [TestDTO(id=1, name="test")]

        with patch(
            "eshop.core.mapping.mapper.MsgspecMapper.map_list_to_entities"
        ) as mock_mapper:
            mock_entities = [TestEntity(1, "test")]
            mock_mapper.return_value = mock_entities

            result = map_list_to_entities(dtos, TestEntity)

            assert result == mock_entities
            mock_mapper.assert_called_once_with(dtos, TestEntity)

    def test_to_json_function(self) -> None:
        """Test to_json convenience function."""
        obj = {"test": "data"}

        with patch("eshop.core.mapping.mapper.MsgspecMapper.to_json") as mock_mapper:
            mock_mapper.return_value = '{"test": "data"}'

            result = to_json(obj)

            assert result == '{"test": "data"}'
            mock_mapper.assert_called_once_with(obj)

    def test_from_json_function(self) -> None:
        """Test from_json convenience function."""
        json_str = '{"id": 1, "name": "test"}'

        with patch("eshop.core.mapping.mapper.MsgspecMapper.from_json") as mock_mapper:
            mock_dto = TestDTO(id=1, name="test")
            mock_mapper.return_value = mock_dto

            result = from_json(json_str, TestDTO)

            assert result == mock_dto
            mock_mapper.assert_called_once_with(json_str, TestDTO)

    def test_to_redis_function(self) -> None:
        """Test to_redis convenience function."""
        obj = {"test": "data"}

        with patch("eshop.core.mapping.mapper.MsgspecMapper.to_redis") as mock_mapper:
            mock_mapper.return_value = b"test_data"

            result = to_redis(obj)

            assert result == b"test_data"
            mock_mapper.assert_called_once_with(obj)

    def test_from_redis_function(self) -> None:
        """Test from_redis convenience function."""
        data = b"test_data"

        with patch("eshop.core.mapping.mapper.MsgspecMapper.from_redis") as mock_mapper:
            mock_dto = TestDTO(id=1, name="test")
            mock_mapper.return_value = mock_dto

            result = from_redis(data, TestDTO)

            assert result == mock_dto
            mock_mapper.assert_called_once_with(data, TestDTO)


class TestMappingIntegration:
    """Integration tests for mapping functionality."""

    def test_full_mapping_cycle_pydantic(self) -> None:
        """Test complete mapping cycle with Pydantic models."""
        # Create entity
        entity = TestEntity(1, "test_entity", True)

        # Map to DTO
        with patch("msgspec.convert") as mock_convert:
            mock_dto = TestDTO(id=1, name="test_entity", active=True)
            mock_convert.return_value = mock_dto

            dto = MsgspecMapper.map_to_dto(entity, TestDTO)
            assert isinstance(dto, TestDTO)
            assert dto.id == 1
            assert dto.name == "test_entity"
            assert dto.active is True

        # Map back to entity
        with patch("msgspec.convert") as mock_convert:
            mock_convert.return_value = entity
            mapped_entity = MsgspecMapper.map_to_entity(dto, TestEntity)
            assert mapped_entity == entity

    def test_mapping_with_complex_nested_structure(self) -> None:
        """Test mapping with complex nested structures."""
        # Create nested structure
        inner_entity = TestEntity(2, "inner")
        outer_entity = TestNestedEntity(1, inner_entity, [inner_entity, inner_entity])

        # Map to DTO
        with patch("msgspec.convert") as mock_convert:
            inner_dto = TestDTO(id=2, name="inner")
            outer_dto = TestNestedDTO(
                id=1, nested=inner_dto, items=[inner_dto, inner_dto]
            )
            mock_convert.return_value = outer_dto

            result = MsgspecMapper.map_to_dto(outer_entity, TestNestedDTO)
            assert result == outer_dto

    def test_mapping_error_handling(self) -> None:
        """Test error handling in mapping operations."""
        # Test invalid object type
        with pytest.raises(ValueError, match="Cannot map object of type"):
            MsgspecMapper.map_to_dto(123, TestDTO)

        # Test conversion error
        entity = TestEntity(1, "test")
        with patch("msgspec.convert") as mock_convert:
            mock_convert.side_effect = Exception("Test error")

            with pytest.raises(ValueError, match="Failed to convert to DTO"):
                MsgspecMapper.map_to_dto(entity, TestDTO)

    def test_json_serialization_cycle(self) -> None:
        """Test JSON serialization and deserialization cycle."""
        original_obj = {"id": 1, "name": "test", "nested": {"value": "data"}}

        # Serialize to JSON
        with patch("msgspec.json.encode") as mock_encode:
            mock_encode.return_value = json.dumps(original_obj).encode()
            json_str = MsgspecMapper.to_json(original_obj)

        # Deserialize from JSON
        with patch("msgspec.json.decode") as mock_decode:
            mock_decode.return_value = original_obj
            result = MsgspecMapper.from_json(json_str, dict)

            assert result == original_obj

    def test_redis_serialization_cycle(self) -> None:
        """Test Redis serialization and deserialization cycle."""
        original_obj = {"id": 1, "name": "test", "active": True}

        # Serialize to Redis format
        with patch("msgspec.msgpack.encode") as mock_encode:
            mock_encode.return_value = b"serialized_data"
            redis_data = MsgspecMapper.to_redis(original_obj)

        # Deserialize from Redis format
        with patch("msgspec.msgpack.decode") as mock_decode:
            mock_decode.return_value = original_obj
            result = MsgspecMapper.from_redis(redis_data, dict)

            assert result == original_obj

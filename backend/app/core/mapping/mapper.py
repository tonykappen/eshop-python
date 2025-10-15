"""Object mapping utilities using msgspec for high-performance serialization and validation."""

from typing import Any, TypeVar

import msgspec

T = TypeVar("T")


class MsgspecMapper:
    """High-performance object mapper using msgspec for serialization and validation."""

    @staticmethod
    def map_to_dto(entity: Any, dto_class: type[T]) -> T:
        """Map an entity to a DTO using msgspec."""
        if hasattr(entity, "model_dump"):
            # Pydantic model
            data = entity.model_dump()
        elif hasattr(entity, "__dict__"):
            # Regular class
            data = entity.__dict__.copy()
        else:
            raise ValueError(f"Cannot map object of type {type(entity)}")

        # Convert to msgspec struct for validation and serialization
        return MsgspecMapper._convert_to_dto(data, dto_class)

    @staticmethod
    def map_to_entity(dto: Any, entity_class: type[T]) -> T:
        """Map a DTO to an entity using msgspec."""
        if hasattr(dto, "model_dump"):
            # Pydantic model
            data = dto.model_dump()
        elif hasattr(dto, "__dict__"):
            # Regular class
            data = dto.__dict__.copy()
        else:
            raise ValueError(f"Cannot map object of type {type(dto)}")

        return MsgspecMapper._convert_to_entity(data, entity_class)

    @staticmethod
    def map_list_to_dtos(entities: list[Any], dto_class: type[T]) -> list[T]:
        """Map a list of entities to DTOs."""
        return [MsgspecMapper.map_to_dto(entity, dto_class) for entity in entities]

    @staticmethod
    def map_list_to_entities(dtos: list[Any], entity_class: type[T]) -> list[T]:
        """Map a list of DTOs to entities."""
        return [MsgspecMapper.map_to_entity(dto, entity_class) for dto in dtos]

    @staticmethod
    def to_json(obj: Any) -> str:
        """Serialize object to JSON string using msgspec."""
        return msgspec.json.encode(obj).decode("utf-8")

    @staticmethod
    def from_json(json_str: str, target_class: type[T]) -> T:
        """Deserialize JSON string to object using msgspec."""
        return msgspec.json.decode(json_str, type=target_class)

    @staticmethod
    def to_redis(obj: Any) -> bytes:
        """Serialize object to bytes for Redis storage."""
        return msgspec.msgpack.encode(obj)

    @staticmethod
    def from_redis(data: bytes, target_class: type[T]) -> T:
        """Deserialize bytes from Redis to object."""
        return msgspec.msgpack.decode(data, type=target_class)

    @staticmethod
    def _convert_to_dto(data: dict[str, Any], dto_class: type[T]) -> T:
        """Convert data to DTO with nested object handling."""
        converted_data = {}

        for field_name, field_value in data.items():
            if isinstance(field_value, list):
                # Handle list of objects
                converted_data[field_name] = [
                    MsgspecMapper._convert_nested_object(item) for item in field_value
                ]
            elif isinstance(field_value, dict):
                # Handle nested object
                converted_data[field_name] = MsgspecMapper._convert_nested_object(
                    field_value
                )
            else:
                converted_data[field_name] = field_value

        # Use msgspec for validation and conversion
        try:
            return msgspec.convert(converted_data, type=dto_class)
        except Exception as e:
            raise ValueError(
                f"Failed to convert to DTO {dto_class.__name__}: {e}"
            ) from e

    @staticmethod
    def _convert_to_entity(data: dict[str, Any], entity_class: type[T]) -> T:
        """Convert data to entity with nested object handling."""
        converted_data = {}

        for field_name, field_value in data.items():
            if isinstance(field_value, list):
                # Handle list of objects
                converted_data[field_name] = [
                    MsgspecMapper._convert_nested_object(item) for item in field_value
                ]
            elif isinstance(field_value, dict):
                # Handle nested object
                converted_data[field_name] = MsgspecMapper._convert_nested_object(
                    field_value
                )
            else:
                converted_data[field_name] = field_value

        # Use msgspec for validation and conversion
        try:
            return msgspec.convert(converted_data, type=entity_class)
        except Exception as e:
            raise ValueError(
                f"Failed to convert to entity {entity_class.__name__}: {e}"
            ) from e

    @staticmethod
    def _convert_nested_object(obj: Any) -> Any:
        """Convert nested objects recursively."""
        if isinstance(obj, dict):
            return {k: MsgspecMapper._convert_nested_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [MsgspecMapper._convert_nested_object(item) for item in obj]
        elif hasattr(obj, "model_dump"):
            # Pydantic model
            return obj.model_dump()
        elif hasattr(obj, "__dict__"):
            # Regular class
            return obj.__dict__.copy()
        else:
            return obj


# Convenience functions
def map_to_dto(entity: Any, dto_class: type[T]) -> T:
    """Map an entity to a DTO."""
    return MsgspecMapper.map_to_dto(entity, dto_class)


def map_to_entity(dto: Any, entity_class: type[T]) -> T:
    """Map a DTO to an entity."""
    return MsgspecMapper.map_to_entity(dto, entity_class)


def map_list_to_dtos(entities: list[Any], dto_class: type[T]) -> list[T]:
    """Map a list of entities to DTOs."""
    return MsgspecMapper.map_list_to_dtos(entities, dto_class)


def map_list_to_entities(dtos: list[Any], entity_class: type[T]) -> list[T]:
    """Map a list of DTOs to entities."""
    return MsgspecMapper.map_list_to_entities(dtos, entity_class)


def to_json(obj: Any) -> str:
    """Serialize object to JSON string."""
    return MsgspecMapper.to_json(obj)


def from_json(json_str: str, target_class: type[T]) -> T:
    """Deserialize JSON string to object."""
    return MsgspecMapper.from_json(json_str, target_class)


def to_redis(obj: Any) -> bytes:
    """Serialize object to bytes for Redis storage."""
    return MsgspecMapper.to_redis(obj)


def from_redis(data: bytes, target_class: type[T]) -> T:
    """Deserialize bytes from Redis to object."""
    return MsgspecMapper.from_redis(data, target_class)

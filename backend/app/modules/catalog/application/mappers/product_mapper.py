"""Product mapper - facade over core.mapping.object_mapper for product-related mappings."""

from typing import Any, TypeVar

from app.core.mapping.mapper import (
    MsgspecMapper,
    map_list_to_dtos,
    map_list_to_entities,
    map_to_dto,
    map_to_entity,
)

T = TypeVar("T")


class ProductMapper:
    """
    Simple facade over core.mapping.object_mapper for product-related flows.
    
    This provides a catalog-specific interface to the core mapping engine,
    making it easier to use mapping in product handlers and services.
    """

    @staticmethod
    def map_to_dto(entity: Any, dto_class: type[T]) -> T:
        """
        Map a product entity to a DTO using the core mapper.
        
        Args:
            entity: Product entity or domain model
            dto_class: Target DTO class
            
        Returns:
            Mapped DTO instance
        """
        return map_to_dto(entity, dto_class)

    @staticmethod
    def map_to_entity(dto: Any, entity_class: type[T]) -> T:
        """
        Map a product DTO to an entity using the core mapper.
        
        Args:
            dto: Product DTO
            entity_class: Target entity class
            
        Returns:
            Mapped entity instance
        """
        return map_to_entity(dto, entity_class)

    @staticmethod
    def map_list_to_dtos(entities: list[Any], dto_class: type[T]) -> list[T]:
        """
        Map a list of product entities to DTOs using the core mapper.
        
        Args:
            entities: List of product entities
            dto_class: Target DTO class
            
        Returns:
            List of mapped DTO instances
        """
        return map_list_to_dtos(entities, dto_class)

    @staticmethod
    def map_list_to_entities(dtos: list[Any], entity_class: type[T]) -> list[T]:
        """
        Map a list of product DTOs to entities using the core mapper.
        
        Args:
            dtos: List of product DTOs
            entity_class: Target entity class
            
        Returns:
            List of mapped entity instances
        """
        return map_list_to_entities(dtos, entity_class)

    @staticmethod
    def to_json(obj: Any) -> str:
        """
        Serialize a product object to JSON string.
        
        Args:
            obj: Product object to serialize
            
        Returns:
            JSON string representation
        """
        return MsgspecMapper.to_json(obj)

    @staticmethod
    def from_json(json_str: str, target_class: type[T]) -> T:
        """
        Deserialize a JSON string to a product object.
        
        Args:
            json_str: JSON string to deserialize
            target_class: Target class type
            
        Returns:
            Deserialized object instance
        """
        return MsgspecMapper.from_json(json_str, target_class)

    @staticmethod
    def to_redis(obj: Any) -> bytes:
        """
        Serialize a product object to bytes for Redis storage.
        
        Args:
            obj: Product object to serialize
            
        Returns:
            Bytes representation
        """
        return MsgspecMapper.to_redis(obj)

    @staticmethod
    def from_redis(data: bytes, target_class: type[T]) -> T:
        """
        Deserialize bytes from Redis to a product object.
        
        Args:
            data: Bytes data from Redis
            target_class: Target class type
            
        Returns:
            Deserialized object instance
        """
        return MsgspecMapper.from_redis(data, target_class)












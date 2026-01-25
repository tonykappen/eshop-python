"""Base JSON converter ABC for custom JSON formats."""

from abc import ABC, abstractmethod
from typing import Any


class BaseJsonConverter(ABC):
    """Abstract base class for custom JSON converters."""

    @abstractmethod
    def serialize(self, obj: Any) -> str:
        """
        Serialize an object to JSON string.

        Args:
            obj: Object to serialize

        Returns:
            JSON string representation
        """
        pass

    @abstractmethod
    def deserialize(self, json_str: str, target_type: type[Any]) -> Any:
        """
        Deserialize a JSON string to an object.

        Args:
            json_str: JSON string to deserialize
            target_type: Target type for deserialization

        Returns:
            Deserialized object
        """
        pass

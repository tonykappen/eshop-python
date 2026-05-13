"""Base class for mapping profiles."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")
SourceType = TypeVar("SourceType")
DestinationType = TypeVar("DestinationType")


class BaseMappingProfile(ABC):
    """
    Base class for mapping profiles.

    Mapping profiles define explicit rules for converting between different object types
    (e.g., Domain entities ↔ DTOs ↔ ORM models). This follows the AutoMapper pattern
    from .NET, providing a centralized, testable way to manage object mappings.

    Subclasses should implement specific mapping methods for their domain entities.
    """

    @abstractmethod
    def configure(self) -> None:
        """
        Configure mapping rules for this profile.

        This method is called during profile initialization to set up
        mapping configurations. Override this to define custom mappings.
        """
        pass

    def map(
        self, source: SourceType, destination_type: type[DestinationType]
    ) -> DestinationType:
        """
        Map source object to destination type.

        Args:
            source: Source object to map from
            destination_type: Target type to map to

        Returns:
            Mapped destination object

        Raises:
            NotImplementedError: If mapping not configured for these types
        """
        # Default implementation - subclasses should override
        raise NotImplementedError(
            f"Mapping from {type(source).__name__} to {destination_type.__name__} not configured"
        )

    def map_list(
        self, sources: list[SourceType], destination_type: type[DestinationType]
    ) -> list[DestinationType]:
        """
        Map a list of source objects to destination type.

        Args:
            sources: List of source objects
            destination_type: Target type to map to

        Returns:
            List of mapped destination objects
        """
        return [self.map(source, destination_type) for source in sources]

    def can_map(self, source_type: type, destination_type: type) -> bool:
        """
        Check if this profile can map from source to destination type.

        Args:
            source_type: Source type
            destination_type: Destination type

        Returns:
            True if mapping is supported, False otherwise
        """
        # Default implementation - subclasses should override
        return False

    def _extract_data(self, obj: Any) -> dict[str, Any]:
        """
        Extract data from an object for mapping.

        Args:
            obj: Object to extract data from

        Returns:
            Dictionary of object data
        """
        if hasattr(obj, "model_dump"):
            # Pydantic model
            return obj.model_dump(exclude={"domain_events"})
        elif hasattr(obj, "items"):
            # Entity with items() method
            return dict(obj.items())
        elif hasattr(obj, "__dict__"):
            # Regular class
            return {
                k: v
                for k, v in obj.__dict__.items()
                if not k.startswith("_") and k != "domain_events"
            }
        else:
            raise ValueError(f"Cannot extract data from object of type {type(obj)}")

    def _create_instance(self, data: dict[str, Any], target_type: type[T]) -> T:
        """
        Create an instance of target type from data dictionary.

        Args:
            data: Data dictionary
            target_type: Target type to create

        Returns:
            Instance of target type
        """
        from pydantic import BaseModel

        if issubclass(target_type, BaseModel):
            # Pydantic model
            return target_type(**data)
        else:
            # Regular class
            return target_type(**data)

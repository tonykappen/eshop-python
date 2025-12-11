"""ID provider service for generating unique identifiers."""

from abc import ABC, abstractmethod
from uuid import UUID


class IIdProvider(ABC):
    """Interface for ID provider service."""

    @abstractmethod
    def generate_id(self) -> UUID:
        """
        Generate a new unique ID.
        
        Returns:
            New unique UUID
        """
        pass


class IdProvider(IIdProvider):
    """Default ID provider implementation."""

    def generate_id(self) -> UUID:
        """
        Generate a new unique ID using UUID4.
        
        Returns:
            New unique UUID
        """
        import uuid
        return uuid.uuid4()


class DeterministicIdProvider(IIdProvider):
    """Deterministic ID provider for testing purposes."""

    def __init__(self, seed: int = 0):
        """
        Initialize with a seed for deterministic generation.
        
        Args:
            seed: Seed for deterministic generation
        """
        self.seed = seed
        self.counter = 0

    def generate_id(self) -> UUID:
        """
        Generate a deterministic ID based on seed and counter.
        
        Returns:
            Deterministic UUID
        """
        import uuid
        
        # Create a deterministic UUID based on seed and counter
        namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        name = f"{self.seed}-{self.counter}"
        self.counter += 1
        
        return uuid.uuid5(namespace, name)



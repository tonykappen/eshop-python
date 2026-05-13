"""Clock service for time operations."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime


class IClock(ABC):
    """Interface for clock service."""

    @abstractmethod
    def now(self) -> datetime:
        """
        Get current UTC time.

        Returns:
            Current UTC datetime
        """
        pass

    @abstractmethod
    def now_iso(self) -> str:
        """
        Get current UTC time as ISO string.

        Returns:
            Current UTC datetime as ISO string
        """
        pass


class Clock(IClock):
    """Default clock implementation using system time."""

    def now(self) -> datetime:
        """
        Get current UTC time.

        Returns:
            Current UTC datetime
        """
        return datetime.now(UTC)

    def now_iso(self) -> str:
        """
        Get current UTC time as ISO string.

        Returns:
            Current UTC datetime as ISO string
        """
        return self.now().isoformat()


class FixedClock(IClock):
    """Fixed clock implementation for testing purposes."""

    def __init__(self, fixed_time: datetime | None = None):
        """
        Initialize with a fixed time.

        Args:
            fixed_time: Fixed time to return (defaults to current time)
        """
        self.fixed_time = fixed_time or datetime.now(UTC)

    def now(self) -> datetime:
        """
        Get the fixed time.

        Returns:
            Fixed datetime
        """
        return self.fixed_time

    def now_iso(self) -> str:
        """
        Get the fixed time as ISO string.

        Returns:
            Fixed datetime as ISO string
        """
        return self.fixed_time.isoformat()

    def set_time(self, new_time: datetime) -> None:
        """
        Set a new fixed time.

        Args:
            new_time: New fixed time
        """
        self.fixed_time = new_time

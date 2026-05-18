"""Tests for clock service."""

from datetime import UTC, datetime

import pytest
from app.core.time.clock import Clock, FixedClock, IClock


class TestIClock:
    """Test IClock interface."""

    def test_iclock_is_abstract(self) -> None:
        """Test that IClock is an abstract base class."""
        with pytest.raises(TypeError):
            IClock()  # Should raise TypeError for abstract class


class TestClock:
    """Test Clock implementation."""

    def test_clock_now_returns_datetime(self) -> None:
        """Test that now() returns a datetime object."""
        clock = Clock()
        now = clock.now()

        assert isinstance(now, datetime)
        assert now.tzinfo == UTC

    def test_clock_now_iso_returns_string(self) -> None:
        """Test that now_iso() returns an ISO format string."""
        clock = Clock()
        iso_string = clock.now_iso()

        assert isinstance(iso_string, str)
        # Should be valid ISO format
        parsed = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        assert isinstance(parsed, datetime)

    def test_clock_now_iso_matches_now(self) -> None:
        """Test that now_iso() matches the ISO format of now()."""
        clock = Clock()
        now = clock.now()
        iso_string = clock.now_iso()

        # Parse the ISO string and compare
        parsed = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        # Allow small time difference (less than 1 second)
        time_diff = abs((now - parsed).total_seconds())
        assert time_diff < 1.0


class TestFixedClock:
    """Test FixedClock implementation."""

    def test_fixed_clock_with_explicit_time(self) -> None:
        """Test FixedClock with explicit time."""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        clock = FixedClock(fixed_time)

        assert clock.now() == fixed_time
        assert clock.now_iso() == fixed_time.isoformat()

    def test_fixed_clock_with_default_time(self) -> None:
        """Test FixedClock with default time (current time)."""
        clock = FixedClock()
        now = clock.now()

        assert isinstance(now, datetime)
        assert now.tzinfo == UTC
        # Should be recent (within last minute)
        time_diff = abs((datetime.now(UTC) - now).total_seconds())
        assert time_diff < 60.0

    def test_fixed_clock_set_time(self) -> None:
        """Test setting a new fixed time."""
        initial_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        clock = FixedClock(initial_time)

        assert clock.now() == initial_time

        new_time = datetime(2024, 2, 1, 15, 30, 0, tzinfo=UTC)
        clock.set_time(new_time)

        assert clock.now() == new_time
        assert clock.now_iso() == new_time.isoformat()

    def test_fixed_clock_consistency(self) -> None:
        """Test that FixedClock returns the same time consistently."""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        clock = FixedClock(fixed_time)

        # Call multiple times
        assert clock.now() == fixed_time
        assert clock.now() == fixed_time
        assert clock.now() == fixed_time

        assert clock.now_iso() == fixed_time.isoformat()
        assert clock.now_iso() == fixed_time.isoformat()

    def test_fixed_clock_iso_format(self) -> None:
        """Test that FixedClock ISO format is correct."""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        clock = FixedClock(fixed_time)

        iso_string = clock.now_iso()
        # Should be valid ISO format
        parsed = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        assert parsed == fixed_time

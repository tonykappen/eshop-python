"""Tests for core domain entity."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest

from app.core.domain.entity import Aggregate, DomainEvent, Entity, ValueObject


class TestDomainEvent:
    """Test domain event functionality."""

    def test_domain_event_creation(self):
        """Test domain event creation."""
        event = DomainEvent()

        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_on, str)
        assert event.event_type == ""

    def test_domain_event_id_uniqueness(self):
        """Test that domain events have unique IDs."""
        event1 = DomainEvent()
        event2 = DomainEvent()

        assert event1.event_id != event2.event_id

    def test_domain_event_custom_values(self):
        """Test domain event with custom values."""
        custom_id = uuid4()
        custom_type = "test_event"

        event = DomainEvent(event_id=custom_id, event_type=custom_type)

        assert event.event_id == custom_id
        assert event.event_type == custom_type

    def test_domain_event_equality(self):
        """Test domain event equality."""
        event1 = DomainEvent()
        event2 = DomainEvent()

        # Different events should not be equal
        assert event1 != event2

        # Same event should be equal to itself
        assert event1 == event1

    def test_domain_event_serialization(self):
        """Test domain event serialization."""
        event = DomainEvent()

        # Should be able to convert to dict
        event_dict = event.model_dump()
        assert "event_id" in event_dict
        assert "occurred_on" in event_dict
        assert "event_type" in event_dict
        # The event_id should be a UUID in the dict (Pydantic preserves UUID type)
        assert isinstance(event_dict["event_id"], UUID)

    def test_domain_event_from_dict(self):
        """Test domain event creation from dictionary."""
        original_event = DomainEvent()
        event_dict = original_event.model_dump()

        # Create new event from dict
        new_event = DomainEvent(**event_dict)

        assert new_event.event_id == original_event.event_id
        assert new_event.event_type == original_event.event_type

    def test_domain_event_repr(self):
        """Test domain event string representation."""
        event = DomainEvent()
        repr_str = repr(event)

        assert "DomainEvent" in repr_str
        assert str(event.event_id) in repr_str

    def test_domain_event_model_copy(self):
        """Test domain event copying."""
        event = DomainEvent()
        event_copy = event.model_copy()

        # Should be equal but different objects
        assert event == event_copy
        assert event is not event_copy


class TestEntity:
    """Test entity functionality."""

    def test_entity_creation(self):
        """Test entity creation."""
        entity = Entity()

        assert isinstance(entity.id, UUID)
        assert entity.domain_events == []
        assert entity.created_at is None
        assert entity.created_by is None
        assert entity.last_modified is None
        assert entity.last_modified_by is None

    def test_entity_id_uniqueness(self):
        """Test that entities have unique IDs."""
        entity1 = Entity()
        entity2 = Entity()

        assert entity1.id != entity2.id

    def test_entity_add_domain_event(self):
        """Test adding domain events to entity."""
        entity = Entity()
        event = DomainEvent()

        entity.add_domain_event(event)

        assert len(entity.domain_events) == 1
        assert entity.domain_events[0] == event

    def test_entity_add_multiple_domain_events(self):
        """Test adding multiple domain events to entity."""
        entity = Entity()
        event1 = DomainEvent()
        event2 = DomainEvent()

        entity.add_domain_event(event1)
        entity.add_domain_event(event2)

        assert len(entity.domain_events) == 2
        assert entity.domain_events[0] == event1
        assert entity.domain_events[1] == event2

    def test_entity_clear_domain_events(self):
        """Test clearing domain events from entity."""
        entity = Entity()
        event1 = DomainEvent()
        event2 = DomainEvent()

        entity.add_domain_event(event1)
        entity.add_domain_event(event2)

        assert len(entity.domain_events) == 2

        entity.clear_domain_events()

        assert len(entity.domain_events) == 0

    def test_entity_domain_events_copy(self):
        """Test getting domain events copy from entity."""
        entity = Entity()
        event1 = DomainEvent()
        event2 = DomainEvent()

        entity.add_domain_event(event1)
        entity.add_domain_event(event2)

        events_copy = entity.domain_events_copy

        assert len(events_copy) == 2
        assert event1 in events_copy
        assert event2 in events_copy
        assert events_copy is not entity.domain_events  # Should be a copy

    def test_entity_equality(self):
        """Test entity equality."""
        entity1 = Entity()
        entity2 = Entity()

        # Different entities should not be equal
        assert entity1 != entity2

        # Same entity should be equal to itself
        assert entity1 == entity1

    def test_entity_equality_with_same_id(self):
        """Test entity equality with same ID."""
        # Create entities with same ID
        same_id = uuid4()
        entity1 = Entity(id=same_id)
        entity2 = Entity(id=same_id)

        # Entities with same ID should be equal
        assert entity1 == entity2

    def test_entity_hash(self):
        """Test entity hashability."""
        entity = Entity()

        # Should be hashable
        hash_value = hash(entity)
        assert isinstance(hash_value, int)

    def test_entity_repr(self):
        """Test entity string representation."""
        entity = Entity()
        repr_str = repr(entity)

        assert "Entity" in repr_str
        assert str(entity.id) in repr_str

    def test_entity_model_dump(self):
        """Test entity serialization to dictionary."""
        entity = Entity()
        event = DomainEvent()
        entity.add_domain_event(event)

        entity_dict = entity.model_dump()

        assert "id" in entity_dict
        assert "created_at" in entity_dict
        assert "created_by" in entity_dict
        assert "last_modified" in entity_dict
        assert "last_modified_by" in entity_dict
        # domain_events should be excluded
        assert "domain_events" not in entity_dict

    def test_entity_model_copy(self):
        """Test entity copying."""
        entity = Entity()
        event = DomainEvent()
        entity.add_domain_event(event)

        copied_entity = entity.model_copy()

        # Should be equal but different objects
        assert entity == copied_entity
        assert entity is not copied_entity
        assert len(copied_entity.domain_events) == 1

    def test_entity_domain_events_immutability(self):
        """Test that domain events list is not shared between entities."""
        entity1 = Entity()
        entity2 = Entity()

        event = DomainEvent()
        entity1.add_domain_event(event)

        # Entity2 should not have the event
        assert len(entity2.domain_events) == 0

    def test_entity_domain_events_order(self):
        """Test that domain events maintain order."""
        entity = Entity()
        event1 = DomainEvent()
        event2 = DomainEvent()
        event3 = DomainEvent()

        entity.add_domain_event(event1)
        entity.add_domain_event(event2)
        entity.add_domain_event(event3)

        events = entity.domain_events
        assert events[0] == event1
        assert events[1] == event2
        assert events[2] == event3

    def test_entity_clear_empty_events(self):
        """Test clearing domain events when none exist."""
        entity = Entity()

        # Should not raise any error
        entity.clear_domain_events()

        assert len(entity.domain_events) == 0

    def test_entity_add_none_event(self):
        """Test adding None as domain event."""
        entity = Entity()

        # Should not raise error, but should add None
        entity.add_domain_event(None)

        assert len(entity.domain_events) == 1
        assert entity.domain_events[0] is None

    def test_entity_add_invalid_event(self):
        """Test adding invalid domain event."""
        entity = Entity()
        invalid_event = "not a domain event"

        # Should not raise error, but should add invalid event
        entity.add_domain_event(invalid_event)

        assert len(entity.domain_events) == 1
        assert entity.domain_events[0] == invalid_event

    def test_entity_serialization_with_complex_events(self):
        """Test entity serialization with complex domain events."""
        entity = Entity()

        # Add multiple events
        for _ in range(5):
            entity.add_domain_event(DomainEvent())

        entity_dict = entity.model_dump()

        assert "id" in entity_dict
        # domain_events should be excluded from serialization
        assert "domain_events" not in entity_dict

    def test_entity_copy_with_events(self):
        """Test entity copying with domain events."""
        entity = Entity()
        events = [DomainEvent() for _ in range(3)]

        for event in events:
            entity.add_domain_event(event)

        copied_entity = entity.model_copy()

        # Should have same events
        assert len(copied_entity.domain_events) == 3
        assert copied_entity.domain_events == entity.domain_events

    def test_entity_equality_with_different_events(self):
        """Test entity equality with different domain events."""
        entity1 = Entity()
        entity2 = Entity()

        # Set same ID
        same_id = uuid4()
        entity1.id = same_id
        entity2.id = same_id

        # Add different events
        entity1.add_domain_event(DomainEvent())
        entity2.add_domain_event(DomainEvent())

        # Should still be equal (equality based on ID only)
        assert entity1 == entity2

    def test_entity_with_custom_fields(self):
        """Test entity with custom field values."""
        custom_id = uuid4()
        custom_created_at = datetime.now()
        custom_created_by = "test_user"

        entity = Entity(
            id=custom_id, created_at=custom_created_at, created_by=custom_created_by
        )

        assert entity.id == custom_id
        assert entity.created_at == custom_created_at
        assert entity.created_by == custom_created_by


class TestAggregate:
    """Test aggregate functionality."""

    def test_aggregate_creation(self):
        """Test aggregate creation."""
        aggregate = Aggregate()

        assert isinstance(aggregate.id, UUID)
        assert aggregate.version == 1
        assert aggregate.domain_events == []

    def test_aggregate_increment_version(self):
        """Test aggregate version increment."""
        aggregate = Aggregate()
        initial_version = aggregate.version

        aggregate.increment_version()

        assert aggregate.version == initial_version + 1

    def test_aggregate_multiple_version_increments(self):
        """Test multiple version increments."""
        aggregate = Aggregate()

        aggregate.increment_version()
        aggregate.increment_version()
        aggregate.increment_version()

        assert aggregate.version == 4

    def test_aggregate_inherits_entity_functionality(self):
        """Test that aggregate inherits entity functionality."""
        aggregate = Aggregate()
        event = DomainEvent()

        aggregate.add_domain_event(event)

        assert len(aggregate.domain_events) == 1
        assert aggregate.domain_events[0] == event

    def test_aggregate_equality(self):
        """Test aggregate equality."""
        aggregate1 = Aggregate()
        aggregate2 = Aggregate()

        # Different aggregates should not be equal
        assert aggregate1 != aggregate2

        # Same aggregate should be equal to itself
        assert aggregate1 == aggregate1

    def test_aggregate_with_custom_version(self):
        """Test aggregate with custom version."""
        custom_version = 5
        aggregate = Aggregate(version=custom_version)

        assert aggregate.version == custom_version


class TestValueObject:
    """Test value object functionality."""

    def test_value_object_creation(self):
        """Test value object creation."""

        class TestValueObject(ValueObject):
            name: str
            value: int

        vo = TestValueObject(name="test", value=42)

        assert vo.name == "test"
        assert vo.value == 42

    def test_value_object_equality(self):
        """Test value object equality."""

        class TestValueObject(ValueObject):
            name: str
            value: int

        vo1 = TestValueObject(name="test", value=42)
        vo2 = TestValueObject(name="test", value=42)
        vo3 = TestValueObject(name="different", value=42)

        # Same values should be equal
        assert vo1 == vo2

        # Different values should not be equal
        assert vo1 != vo3

    def test_value_object_hash(self):
        """Test value object hashability."""

        class TestValueObject(ValueObject):
            name: str
            value: int

        vo = TestValueObject(name="test", value=42)

        # Should be hashable
        hash_value = hash(vo)
        assert isinstance(hash_value, int)

    def test_value_object_immutability(self):
        """Test value object immutability."""

        class TestValueObject(ValueObject):
            name: str
            value: int

        vo = TestValueObject(name="test", value=42)

        # Should be immutable (frozen) - should raise ValidationError
        with pytest.raises((ValueError, TypeError)):  # ValidationError or TypeError
            vo.name = "changed"

    def test_value_object_model_dump(self):
        """Test value object serialization."""

        class TestValueObject(ValueObject):
            name: str
            value: int

        vo = TestValueObject(name="test", value=42)
        vo_dict = vo.model_dump()

        assert vo_dict["name"] == "test"
        assert vo_dict["value"] == 42

    def test_value_object_model_copy(self):
        """Test value object copying."""

        class TestValueObject(ValueObject):
            name: str
            value: int

        vo = TestValueObject(name="test", value=42)
        vo_copy = vo.model_copy()

        # Should be equal but different objects
        assert vo == vo_copy
        assert vo is not vo_copy

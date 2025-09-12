"""Comprehensive tests for domain entity classes."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.core.domain.entity import Aggregate, DomainEvent, Entity, ValueObject


class TestDomainEvent:
    """Test cases for DomainEvent class."""

    def test_domain_event_creation(self):
        """Test domain event creation."""
        event = DomainEvent(event_type="TestEvent")
        assert event.event_type == "TestEvent"
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_on, str)

    def test_domain_event_with_custom_id(self):
        """Test domain event creation with custom ID."""
        event_id = uuid4()
        event = DomainEvent(event_id=event_id, event_type="TestEvent")
        assert event.event_id == event_id
        assert event.event_type == "TestEvent"

    def test_domain_event_equality(self):
        """Test domain event equality."""
        event_id = uuid4()
        event1 = DomainEvent(event_id=event_id, event_type="TestEvent")
        event2 = DomainEvent(event_id=event_id, event_type="TestEvent")
        # Note: DomainEvent doesn't implement __eq__, so they won't be equal
        assert event1.event_id == event2.event_id
        assert event1.event_type == event2.event_type

    def test_domain_event_hash(self):
        """Test domain event hashing."""
        event = DomainEvent(event_type="TestEvent")
        # DomainEvent doesn't implement __hash__, so it's not hashable
        with pytest.raises(TypeError):
            hash(event)

    def test_domain_event_with_arbitrary_types(self):
        """Test domain event with arbitrary types."""

        class CustomData:
            def __init__(self, value):
                self.value = value

        custom_data = CustomData("test")
        event = DomainEvent(event_type="TestEvent")

        # DomainEvent doesn't allow arbitrary attributes by default
        with pytest.raises(ValueError):
            event.custom_data = custom_data

    def test_domain_event_serialization(self):
        """Test domain event serialization."""
        event = DomainEvent(event_type="TestEvent")
        data = event.model_dump()
        assert data["event_type"] == "TestEvent"
        assert "event_id" in data
        assert "occurred_on" in data

    def test_domain_event_deserialization(self):
        """Test domain event deserialization."""
        event_id = uuid4()
        data = {
            "event_id": str(event_id),
            "event_type": "TestEvent",
            "occurred_on": "123456789",
        }
        event = DomainEvent.model_validate(data)
        assert event.event_id == event_id
        assert event.event_type == "TestEvent"
        assert event.occurred_on == "123456789"


class TestEntity:
    """Test cases for Entity class."""

    def test_entity_creation(self):
        """Test entity creation."""
        entity = Entity()
        assert isinstance(entity.id, UUID)
        assert entity.created_at is None
        assert entity.created_by is None
        assert entity.last_modified is None
        assert entity.last_modified_by is None
        assert entity.domain_events == []

    def test_entity_with_custom_id(self):
        """Test entity creation with custom ID."""
        entity_id = uuid4()
        entity = Entity(id=entity_id)
        assert entity.id == entity_id

    def test_entity_with_timestamps(self):
        """Test entity creation with timestamps."""
        now = datetime.now()
        entity = Entity(
            created_at=now,
            created_by="test_user",
            last_modified=now,
            last_modified_by="test_user",
        )
        assert entity.created_at == now
        assert entity.created_by == "test_user"
        assert entity.last_modified == now
        assert entity.last_modified_by == "test_user"

    def test_entity_add_domain_event(self):
        """Test adding domain events to entity."""
        entity = Entity()
        event = DomainEvent(event_type="TestEvent")

        entity.add_domain_event(event)
        assert len(entity.domain_events) == 1
        assert entity.domain_events[0] == event

    def test_entity_clear_domain_events(self):
        """Test clearing domain events from entity."""
        entity = Entity()
        event1 = DomainEvent(event_type="TestEvent1")
        event2 = DomainEvent(event_type="TestEvent2")

        entity.add_domain_event(event1)
        entity.add_domain_event(event2)
        assert len(entity.domain_events) == 2

        entity.clear_domain_events()
        assert len(entity.domain_events) == 0

    def test_entity_domain_events_copy(self):
        """Test getting domain events copy."""
        entity = Entity()
        event = DomainEvent(event_type="TestEvent")
        entity.add_domain_event(event)

        events_copy = entity.domain_events_copy
        assert len(events_copy) == 1
        assert events_copy[0] == event

        # Modify the copy shouldn't affect original
        events_copy.append(DomainEvent(event_type="AnotherEvent"))
        assert len(entity.domain_events) == 1

    def test_entity_equality(self):
        """Test entity equality."""
        entity_id = uuid4()
        entity1 = Entity(id=entity_id)
        entity2 = Entity(id=entity_id)
        entity3 = Entity()

        assert entity1 == entity2
        assert entity1 != entity3

    def test_entity_hash(self):
        """Test entity hashing."""
        entity = Entity()
        assert isinstance(hash(entity), int)
        assert hash(entity) == hash(entity.id)

    def test_entity_with_custom_attributes(self):
        """Test entity with custom attributes."""
        entity = Entity()

        # Entity doesn't allow arbitrary attributes by default
        with pytest.raises(ValueError):
            entity.custom_field = "test_value"

    def test_entity_domain_events_exclusion(self):
        """Test that domain events are excluded from serialization."""
        entity = Entity()
        event = DomainEvent(event_type="TestEvent")
        entity.add_domain_event(event)

        data = entity.model_dump()
        assert "domain_events" not in data

    def test_entity_serialization(self):
        """Test entity serialization."""
        entity = Entity()
        data = entity.model_dump()
        assert "id" in data
        assert "created_at" in data
        assert "created_by" in data
        assert "last_modified" in data
        assert "last_modified_by" in data

    def test_entity_deserialization(self):
        """Test entity deserialization."""
        entity_id = uuid4()
        now = datetime.now()
        data = {
            "id": str(entity_id),
            "created_at": now.isoformat(),
            "created_by": "test_user",
            "last_modified": now.isoformat(),
            "last_modified_by": "test_user",
        }
        entity = Entity.model_validate(data)
        assert entity.id == entity_id
        assert entity.created_by == "test_user"


class TestAggregate:
    """Test cases for Aggregate class."""

    def test_aggregate_creation(self):
        """Test aggregate creation."""
        aggregate = Aggregate()
        assert isinstance(aggregate.id, UUID)
        assert aggregate.version == 1

    def test_aggregate_increment_version(self):
        """Test aggregate version increment."""
        aggregate = Aggregate()
        assert aggregate.version == 1

        aggregate.increment_version()
        assert aggregate.version == 2

        aggregate.increment_version()
        assert aggregate.version == 3

    def test_aggregate_inheritance(self):
        """Test that aggregate inherits from entity."""
        aggregate = Aggregate()
        assert isinstance(aggregate, Entity)
        assert hasattr(aggregate, "add_domain_event")
        assert hasattr(aggregate, "clear_domain_events")
        assert hasattr(aggregate, "domain_events_copy")

    def test_aggregate_with_custom_version(self):
        """Test aggregate creation with custom version."""
        aggregate = Aggregate(version=5)
        assert aggregate.version == 5

    def test_aggregate_serialization(self):
        """Test aggregate serialization."""
        aggregate = Aggregate(version=3)
        data = aggregate.model_dump()
        assert data["version"] == 3
        assert "id" in data


class TestValueObject:
    """Test cases for ValueObject class."""

    def test_value_object_creation(self):
        """Test value object creation."""

        class TestValueObject(ValueObject):
            some_field: str

        vo = TestValueObject(some_field="test")
        assert vo.some_field == "test"

    def test_value_object_equality(self):
        """Test value object equality."""

        class TestValueObject(ValueObject):
            some_field: str

        vo1 = TestValueObject(some_field="test")
        vo2 = TestValueObject(some_field="test")
        vo3 = TestValueObject(some_field="different")

        assert vo1 == vo2
        assert vo1 != vo3

    def test_value_object_hash(self):
        """Test value object hashing."""

        class TestValueObject(ValueObject):
            some_field: str

        vo = TestValueObject(some_field="test")
        assert isinstance(hash(vo), int)

    def test_value_object_immutability(self):
        """Test value object immutability."""

        class TestValueObject(ValueObject):
            some_field: str

        vo = TestValueObject(some_field="test")

        # ValueObject is frozen, so attributes can't be modified
        with pytest.raises(ValidationError):
            vo.some_field = "new_value"

    def test_value_object_serialization(self):
        """Test value object serialization."""

        class TestValueObject(ValueObject):
            some_field: str

        vo = TestValueObject(some_field="test")
        data = vo.model_dump()
        assert data["some_field"] == "test"

    def test_value_object_deserialization(self):
        """Test value object deserialization."""

        class TestValueObject(ValueObject):
            some_field: str

        data = {"some_field": "test"}
        vo = TestValueObject.model_validate(data)
        assert vo.some_field == "test"

    def test_value_object_with_multiple_fields(self):
        """Test value object with multiple fields."""

        class TestValueObject(ValueObject):
            field1: str
            field2: int
            field3: bool

        vo = TestValueObject(field1="test", field2=42, field3=True)
        assert vo.field1 == "test"
        assert vo.field2 == 42
        assert vo.field3 is True

    def test_value_object_hash_consistency(self):
        """Test that value object hash is consistent."""

        class TestValueObject(ValueObject):
            some_field: str

        vo1 = TestValueObject(some_field="test")
        vo2 = TestValueObject(some_field="test")

        assert hash(vo1) == hash(vo2)
        assert hash(vo1) == hash(vo1)  # Should be consistent across calls

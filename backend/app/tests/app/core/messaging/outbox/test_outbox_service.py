"""Tests for outbox service registration."""

from app.core.messaging.outbox.outbox_service import (
    get_registered_outbox_orm,
    register_outbox_orm,
)


class FakeOutboxORM:
    __name__ = "FakeOutboxORM"


def test_register_and_get_outbox_orm() -> None:
    register_outbox_orm(FakeOutboxORM)
    assert get_registered_outbox_orm() is FakeOutboxORM


def test_get_outbox_orm_class_falls_back_to_catalog() -> None:
    from app.core.messaging.outbox.outbox_service import OutboxService
    from unittest.mock import AsyncMock

    service = OutboxService(AsyncMock())
    orm_class = service._get_outbox_orm_class()
    assert orm_class is not None

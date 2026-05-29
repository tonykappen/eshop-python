"""Tests for CLEF log dispatcher helpers."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from app.core.logging.clef_dispatcher import (
    CLEFLogDispatcher,
    _categorize_event_stream,
    _resolve_log_directory,
)


class TestClefDispatcherHelpers:
    def test_resolve_log_directory_relative(self) -> None:
        path = _resolve_log_directory("logs")
        assert path.is_absolute()
        assert path.name == "logs"

    def test_resolve_log_directory_absolute(self, tmp_path: Path) -> None:
        assert _resolve_log_directory(str(tmp_path)) == tmp_path

    def test_categorize_access_stream(self) -> None:
        assert _categorize_event_stream({"message_name": "begin_request"}) == "access"
        assert _categorize_event_stream({"@m": "response_sent"}) == "access"

    def test_categorize_events_stream(self) -> None:
        assert (
            _categorize_event_stream({"message_name": "db_query", "db_statement": "SELECT 1"})
            == "events"
        )
        assert _categorize_event_stream({"message_name": "cache_get_hit"}) == "events"

    def test_categorize_app_stream(self) -> None:
        assert _categorize_event_stream({"message_name": "handler_executed"}) == "app"


@pytest.mark.asyncio
async def test_dispatcher_enqueue_and_stop() -> None:
    dispatcher = CLEFLogDispatcher(
        seq_url=None,
        log_directory="logs/test-clef",
        batch_size=1,
    )
    await dispatcher.start()
    await dispatcher.enqueue({"@m": "test_event", "message_name": "handler_executed"})
    await dispatcher.stop()

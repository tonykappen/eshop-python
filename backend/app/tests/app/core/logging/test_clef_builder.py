"""Tests for CLEF event builder."""

from unittest.mock import patch

import pytest
from app.core.logging.clef_builder import (
    build_clef_event,
    get_host_metadata,
    get_service_metadata,
)
from app.core.logging.trace_context import clear_trace_context, set_trace_context


class TestClefBuilder:
    def test_get_service_metadata_defaults(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            meta = get_service_metadata()
            assert meta["service"] == "eshop-api"
            assert meta["version"] == "1.0.0"
            assert meta["env"] == "dev"

    def test_get_service_metadata_from_env(self) -> None:
        env = {
            "SERVICE_NAME": "catalog-api",
            "SERVICE_VERSION": "2.0.0",
            "ENVIRONMENT": "prod",
        }
        with patch.dict("os.environ", env, clear=True):
            meta = get_service_metadata()
            assert meta == {
                "service": "catalog-api",
                "version": "2.0.0",
                "env": "prod",
            }

    def test_get_host_metadata(self) -> None:
        meta = get_host_metadata()
        assert "host" in meta
        assert isinstance(meta["pid"], int)
        assert meta["thread"] == "MainThread"

    def test_build_clef_event_required_fields(self) -> None:
        clear_trace_context()

        event = build_clef_event(
            event_name="test_event",
            level="info",
            logger="test.logger",
            module="test_module",
            function="test_fn",
            line=42,
        )

        assert event["@l"] == "INFO"
        assert event["@m"] == "test_event"
        assert event["logger"] == "test.logger"
        assert event["line"] == 42
        assert event["trace_id"] == "0" * 32
        assert event["span_id"] == "0" * 16
        assert "request_id" in event
        assert event["policy"]["rate_limited"] is False

    def test_build_clef_event_with_trace_context(self) -> None:
        set_trace_context("abc123" * 4 + "abcd", "span1234567890ab", "req-123")

        event = build_clef_event(
            event_name="http_request",
            level="warning",
            logger="app.http",
            module="middleware",
            function="dispatch",
            line=10,
            method="GET",
            path="/api/v1/products",
            status_code=200,
            user_id="user-1",
            roles=["admin"],
        )

        assert event["trace_id"] == "abc123" * 4 + "abcd"
        assert event["span_id"] == "span1234567890ab"
        assert event["request_id"] == "req-123"
        assert event["method"] == "GET"
        assert event["status_code"] == 200
        assert event["user_id"] == "user-1"
        assert event["roles"] == ["admin"]

    def test_build_clef_event_custom_field_override(self) -> None:
        event = build_clef_event(
            event_name="custom",
            level="error",
            logger="app",
            module="mod",
            function="fn",
            line=1,
            custom_metric=99,
        )
        assert event["custom_metric"] == 99

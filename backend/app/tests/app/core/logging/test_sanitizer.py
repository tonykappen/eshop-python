"""Tests for logging sanitizer utilities."""

import json

from app.core.logging.sanitizer import (
    get_safe_headers,
    sanitize_headers,
    sanitize_json_body,
)


class TestSanitizer:
    def test_sanitize_headers_redacts_authorization(self) -> None:
        headers = {
            "Authorization": "Bearer secret-token",
            "Content-Type": "application/json",
        }
        result = sanitize_headers(headers)
        assert "REDACTED" in result["Authorization"]
        assert result["Content-Type"] == "application/json"

    def test_sanitize_headers_empty(self) -> None:
        assert sanitize_headers({}) == {}
        assert sanitize_headers(None) == {}

    def test_sanitize_json_body_dict(self) -> None:
        body = {"username": "alice", "password": "secret123", "nested": {"token": "abc"}}
        result = sanitize_json_body(body)
        assert result["username"] == "alice"
        assert "REDACTED" in result["password"]
        assert "REDACTED" in result["nested"]["token"]

    def test_sanitize_json_body_string(self) -> None:
        body = json.dumps({"access_token": "xyz", "name": "test"})
        result = sanitize_json_body(body)
        assert "REDACTED" in result["access_token"]
        assert result["name"] == "test"

    def test_sanitize_json_body_bytes(self) -> None:
        body = b'{"api_key": "key123"}'
        result = sanitize_json_body(body)
        assert "REDACTED" in result["api_key"]

    def test_sanitize_json_body_binary(self) -> None:
        result = sanitize_json_body(b"\xff\xfe\xfd")
        assert "binary data" in result

    def test_sanitize_json_body_truncation(self) -> None:
        long_body = "x" * 6000
        result = sanitize_json_body(long_body, max_size=100)
        assert "truncated" in result

    def test_get_safe_headers_whitelist(self) -> None:
        headers = {
            "Authorization": "Bearer x",
            "Content-Type": "application/json",
            "User-Agent": "test-agent",
        }
        result = get_safe_headers(headers, include_all=False)
        assert "Authorization" not in result
        assert result["Content-Type"] == "application/json"
        assert result["User-Agent"] == "test-agent"

    def test_get_safe_headers_include_all(self) -> None:
        headers = {"Authorization": "Bearer x", "Accept": "application/json"}
        result = get_safe_headers(headers, include_all=True)
        assert "REDACTED" in result["Authorization"]
        assert result["Accept"] == "application/json"

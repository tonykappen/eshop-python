"""Safe logging utilities for request headers and payloads with automatic redaction."""

import json
from typing import Any

# Headers that should always be redacted
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "x-api-key",
    "x-client-secret",
    "x-auth-token",
    "x-bearer-token",
    "x-access-token",
    "x-refresh-token",
    "proxy-authorization",
    "www-authenticate",
    "set-cookie",
    "x-csrf-token",
    "x-session-id",
    "x-secret",
    "api-key",
    "apikey",
}

# JSON keys that should be redacted in request/response bodies
SENSITIVE_BODY_KEYS = {
    "password",
    "secret",
    "token",
    "key",
    "authorization",
    "cookie",
    "client_secret",
    "bearer_token",
    "api_key",
    "private_key",
    "access_token",
    "refresh_token",
    "csrf_token",
    "session_id",
    "credit_card",
    "card_number",
    "cvv",
    "ssn",
    "social_security_number",
    "pin",
    "pii",
    "personal_data",
}


def sanitize_headers(headers: dict[str, str] | Any) -> dict[str, str]:
    """
    Sanitize HTTP headers by redacting sensitive information.

    Args:
        headers: Dictionary of HTTP headers

    Returns:
        Sanitized headers dictionary with sensitive values redacted
    """
    if not headers:
        return {}

    sanitized = {}

    for key, value in headers.items():
        key_lower = key.lower()

        # Check if this header should be redacted
        if any(sensitive in key_lower for sensitive in SENSITIVE_HEADERS):
            if isinstance(value, str) and len(value) > 0:
                # Show length but not content
                sanitized[key] = f"<REDACTED:{len(value)} chars>"
            else:
                sanitized[key] = "<REDACTED>"
        else:
            # Safe to include
            sanitized[key] = value

    return sanitized


def sanitize_json_body(
    body: str | bytes | dict | Any, max_size: int = 5000
) -> dict[str, Any] | str | None:
    """
    Sanitize JSON request/response body by redacting sensitive fields.

    Args:
        body: Request/response body (string, bytes, or dict)
        max_size: Maximum size of body to log (in characters)

    Returns:
        Sanitized body as dict or string, or None if body is too large/binary
    """
    if body is None:
        return None

    # Convert bytes to string
    if isinstance(body, bytes):
        try:
            body_str = body.decode("utf-8")
        except UnicodeDecodeError:
            # Binary data - don't log
            return f"<binary data: {len(body)} bytes>"
    elif isinstance(body, dict):
        # Already a dict, sanitize it
        return _sanitize_dict(body)
    elif isinstance(body, str):
        body_str = body
    else:
        # Unknown type
        return str(body)[:max_size]

    # Limit size
    if len(body_str) > max_size:
        body_str = body_str[:max_size] + "... <truncated>"

    # Try to parse as JSON
    try:
        body_dict = json.loads(body_str)
        if isinstance(body_dict, dict):
            return _sanitize_dict(body_dict)
        else:
            # Not a dict, return as string
            return body_str
    except (json.JSONDecodeError, ValueError):
        # Not JSON, return as string (already limited in size)
        return body_str


def _sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively sanitize a dictionary by redacting sensitive keys."""
    sanitized: dict[str, Any] = {}

    for key, value in data.items():
        key_lower = str(key).lower()

        # Check if this key should be redacted
        if any(sensitive in key_lower for sensitive in SENSITIVE_BODY_KEYS):
            if isinstance(value, str) and len(value) > 0:
                sanitized[key] = f"<REDACTED:{len(value)} chars>"
            elif isinstance(value, (int, float)):
                sanitized[key] = "<REDACTED>"
            else:
                sanitized[key] = "<REDACTED>"
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = _sanitize_dict(value)
        elif isinstance(value, list):
            # Sanitize list items
            sanitized[key] = [
                _sanitize_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Safe to include
            sanitized[key] = value

    return sanitized


def get_safe_headers(
    headers: dict[str, str] | Any, include_all: bool = False
) -> dict[str, str]:
    """
    Get safe headers for logging.

    Args:
        headers: Dictionary of HTTP headers
        include_all: If True, include all headers (with redaction).
                     If False, only include safe/common headers.

    Returns:
        Dictionary of safe headers
    """
    if not headers:
        return {}

    # Common safe headers to always include
    safe_headers_whitelist = {
        "content-type",
        "content-length",
        "user-agent",
        "accept",
        "accept-encoding",
        "accept-language",
        "referer",
        "origin",
        "host",
        "x-forwarded-for",
        "x-real-ip",
        "x-requested-with",
        "traceparent",
        "tracestate",
    }

    if include_all:
        # Include all headers but redact sensitive ones
        return sanitize_headers(headers)
    else:
        # Only include whitelisted safe headers
        sanitized = {}
        for key, value in headers.items():
            key_lower = key.lower()
            if key_lower in safe_headers_whitelist:
                sanitized[key] = value

        return sanitized

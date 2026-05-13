"""Tests for request context module."""

import pytest

from app.core.context.request_context import (
    clear_trace_context,
    get_auth_subject,
    get_baggage,
    get_client_ip,
    get_controller,
    get_http_version,
    get_kc_user_id,
    get_kc_user_name,
    get_method,
    get_operation_id,
    get_path,
    get_path_params,
    get_query,
    get_referer,
    get_request_id,
    get_request_size,
    get_roles,
    get_route,
    get_scheme,
    get_session_id,
    get_session_id_prefix,
    get_span_id,
    get_tenant_id,
    get_token_id,
    get_trace_context,
    get_trace_id,
    get_traceparent_raw,
    get_tracestate,
    get_user_agent,
    get_user_id,
    get_parent_span_id,
    set_http_request_context,
    set_identity_context,
    set_operation_context,
    set_trace_context,
)


class TestTraceContext:
    """Test trace context functions."""

    def test_set_and_get_trace_context(self) -> None:
        """Test setting and getting trace context."""
        clear_trace_context()
        
        set_trace_context("trace-123", "span-456", "request-789")
        
        assert get_trace_id() == "trace-123"
        assert get_span_id() == "span-456"
        assert get_request_id() == "request-789"
        
        clear_trace_context()
        assert get_trace_id() is None
        assert get_span_id() is None
        assert get_request_id() is None

    def test_get_trace_context_dict(self) -> None:
        """Test getting trace context as dictionary."""
        clear_trace_context()
        
        set_trace_context("trace-123", "span-456", "request-789")
        set_http_request_context(parent_span_id="parent-123", traceparent_raw="00-123", tracestate="state=value")
        
        context = get_trace_context()
        
        assert context["trace_id"] == "trace-123"
        assert context["span_id"] == "span-456"
        assert context["request_id"] == "request-789"
        assert context["parent_span_id"] == "parent-123"
        assert context["traceparent_raw"] == "00-123"
        assert context["tracestate"] == "state=value"
        
        clear_trace_context()

    def test_clear_trace_context(self) -> None:
        """Test clearing trace context."""
        set_trace_context("trace-123", "span-456", "request-789")
        clear_trace_context()
        
        assert get_trace_id() is None
        assert get_span_id() is None
        assert get_request_id() is None


class TestIdentityContext:
    """Test identity context functions."""

    def test_set_and_get_identity_context(self) -> None:
        """Test setting and getting identity context."""
        clear_trace_context()
        
        set_identity_context(
            kc_user_id="kc-123",
            kc_user_name="john.doe",
            user_id="user-456",
            auth_subject="subject-789",
            roles=["admin", "user"],
            token_id="token-abc",
            session_id="session-xyz",
            tenant_id="tenant-123",
        )
        
        assert get_kc_user_id() == "kc-123"
        assert get_kc_user_name() == "john.doe"
        assert get_user_id() == "user-456"
        assert get_auth_subject() == "subject-789"
        assert get_roles() == ["admin", "user"]
        assert get_token_id() == "token-abc"
        assert get_session_id() == "session-xyz"
        assert get_tenant_id() == "tenant-123"
        
        clear_trace_context()

    def test_set_identity_context_partial(self) -> None:
        """Test setting identity context with partial values."""
        clear_trace_context()
        
        set_identity_context(kc_user_id="kc-123", roles=["admin"])
        
        assert get_kc_user_id() == "kc-123"
        assert get_roles() == ["admin"]
        assert get_user_id() is None
        assert get_kc_user_name() is None
        
        clear_trace_context()

    def test_get_roles_default_empty(self) -> None:
        """Test that get_roles returns empty list when not set."""
        clear_trace_context()
        
        assert get_roles() == []
        
        clear_trace_context()


class TestOperationContext:
    """Test operation context functions."""

    def test_set_and_get_operation_context(self) -> None:
        """Test setting and getting operation context."""
        clear_trace_context()
        
        set_operation_context(operation_id="op-123", controller="ProductController")
        
        assert get_operation_id() == "op-123"
        assert get_controller() == "ProductController"
        
        clear_trace_context()

    def test_set_operation_context_partial(self) -> None:
        """Test setting operation context with partial values."""
        clear_trace_context()
        
        set_operation_context(operation_id="op-123")
        
        assert get_operation_id() == "op-123"
        assert get_controller() is None
        
        clear_trace_context()


class TestHttpRequestContext:
    """Test HTTP request context functions."""

    def test_set_and_get_http_request_context_full(self) -> None:
        """Test setting and getting full HTTP request context."""
        clear_trace_context()
        
        set_http_request_context(
            method="GET",
            path="/api/products",
            client_ip="192.168.1.1",
            user_agent="Mozilla/5.0",
            scheme="https",
            http_version="HTTP/1.1",
            referer="https://example.com",
            route="/api/products",
            path_params={"id": "123"},
            query="page=1&limit=10",
            request_size=1024,
            parent_span_id="parent-123",
            traceparent_raw="00-123",
            tracestate="state=value",
            session_id_prefix="sess-",
        )
        
        assert get_method() == "GET"
        assert get_path() == "/api/products"
        assert get_client_ip() == "192.168.1.1"
        assert get_user_agent() == "Mozilla/5.0"
        assert get_scheme() == "https"
        assert get_http_version() == "HTTP/1.1"
        assert get_referer() == "https://example.com"
        assert get_route() == "/api/products"
        assert get_path_params() == {"id": "123"}
        assert get_query() == "page=1&limit=10"
        assert get_request_size() == 1024
        assert get_parent_span_id() == "parent-123"
        assert get_traceparent_raw() == "00-123"
        assert get_tracestate() == "state=value"
        assert get_session_id_prefix() == "sess-"
        
        clear_trace_context()

    def test_set_http_request_context_partial(self) -> None:
        """Test setting HTTP request context with partial values."""
        clear_trace_context()
        
        set_http_request_context(method="POST", path="/api/products")
        
        assert get_method() == "POST"
        assert get_path() == "/api/products"
        assert get_client_ip() is None
        assert get_user_agent() is None
        
        clear_trace_context()

    def test_get_path_params(self) -> None:
        """Test getting path params."""
        clear_trace_context()
        
        path_params = {"id": "123", "category": "electronics"}
        set_http_request_context(path_params=path_params)
        
        assert get_path_params() == path_params
        
        clear_trace_context()


class TestBaggage:
    """Test baggage functions."""

    def test_get_baggage_default_empty(self) -> None:
        """Test that get_baggage returns empty dict by default."""
        clear_trace_context()
        
        baggage = get_baggage()
        assert baggage == {}
        
        clear_trace_context()


class TestContextIsolation:
    """Test that context is properly isolated."""

    def test_context_isolation(self) -> None:
        """Test that context values don't leak between tests."""
        clear_trace_context()
        
        # Set some values
        set_trace_context("trace-1", "span-1", "request-1")
        set_identity_context(user_id="user-1")
        
        # Clear and verify
        clear_trace_context()
        
        assert get_trace_id() is None
        assert get_user_id() is None
        assert get_roles() == []  # Should be empty list, not None
        
        clear_trace_context()

"""Tests for W3C trace utilities."""

from app.core.logging.w3c_trace import (
    extract_or_generate_trace_context,
    format_traceparent,
    generate_span_id,
    generate_trace_id,
    generate_traceparent,
    parse_traceparent,
)


class TestW3CTrace:
    def test_parse_valid_traceparent(self) -> None:
        header = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        ctx = parse_traceparent(header)
        assert ctx is not None
        assert ctx.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert len(ctx.span_id) == 16

    def test_parse_invalid_traceparent(self) -> None:
        assert parse_traceparent("invalid") is None
        assert parse_traceparent(None) is None

    def test_generate_ids(self) -> None:
        trace_id = generate_trace_id()
        span_id = generate_span_id()
        assert len(trace_id) == 32
        assert len(span_id) == 16

    def test_generate_and_format_traceparent(self) -> None:
        header = generate_traceparent()
        ctx = parse_traceparent(header)
        assert ctx is not None
        assert format_traceparent(ctx).startswith("00-")

    def test_extract_or_generate_without_header(self) -> None:
        ctx = extract_or_generate_trace_context(None, None)
        assert len(ctx.trace_id) == 32

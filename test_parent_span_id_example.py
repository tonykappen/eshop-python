#!/usr/bin/env python3
"""
Test script to demonstrate parent_span_id being populated.

This script shows:
1. How parent_span_id is extracted from traceparent header
2. How it flows through the system
3. A practical example you can run
"""

from app.core.logging.w3c_trace import (extract_or_generate_trace_context,
                                        format_traceparent, parse_traceparent)


def test_parent_span_id_extraction():
    """Test that parent_span_id is extracted from traceparent header."""
    print("=" * 80)
    print("TEST 1: Extract parent_span_id from traceparent header")
    print("=" * 80)

    # Example traceparent header from a client
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    print(f"\nInput traceparent header: {traceparent}")
    print("\nBreakdown:")
    print("  version: 00")
    print("  trace_id: 4bf92f3577b34da6a3ce929d0e0e4736")
    print("  parent_span_id: 00f067aa0ba902b7  ← This will be extracted!")
    print("  trace_flags: 01")

    # Parse the traceparent
    trace_ctx = parse_traceparent(traceparent)

    if trace_ctx:
        print("\n✅ Parsed successfully!")
        print(f"  trace_id: {trace_ctx.trace_id}")
        print(f"  span_id: {trace_ctx.span_id} (new span for this service)")
        print(f"  parent_span_id: {trace_ctx.parent_span_id} ← POPULATED!")
        print(f"  trace_flags: {trace_ctx.trace_flags}")
        assert trace_ctx.parent_span_id == "00f067aa0ba902b7"
        print("\n✅ parent_span_id is correctly populated!")
    else:
        print("\n❌ Failed to parse traceparent")
        return False

    return True


def test_no_traceparent_header():
    """Test that parent_span_id is None when no traceparent header."""
    print("\n" + "=" * 80)
    print("TEST 2: No traceparent header (root span)")
    print("=" * 80)

    traceparent = None
    print(f"\nInput traceparent header: {traceparent}")

    # Generate new trace context
    trace_ctx = extract_or_generate_trace_context(traceparent)

    print("\n✅ Generated new trace context!")
    print(f"  trace_id: {trace_ctx.trace_id}")
    print(f"  span_id: {trace_ctx.span_id}")
    print(
        f"  parent_span_id: {trace_ctx.parent_span_id} ← None (correct for root span)"
    )
    print(f"  trace_flags: {trace_ctx.trace_flags}")

    assert trace_ctx.parent_span_id is None
    print("\n✅ parent_span_id is None (correct for root span)")

    return True


def test_trace_propagation():
    """Test trace propagation across requests."""
    print("\n" + "=" * 80)
    print("TEST 3: Trace propagation (parent-child relationship)")
    print("=" * 80)

    # Request 1: Root span (no parent)
    print("\n📥 Request 1: Root span (no traceparent header)")
    trace_ctx_1 = extract_or_generate_trace_context(None)
    print(f"  trace_id: {trace_ctx_1.trace_id}")
    print(f"  span_id: {trace_ctx_1.span_id}")
    print(f"  parent_span_id: {trace_ctx_1.parent_span_id}")

    # Format traceparent for next request
    traceparent_1 = format_traceparent(trace_ctx_1)
    print(f"  traceparent header: {traceparent_1}")

    # Request 2: Child span (with parent from Request 1)
    print("\n📥 Request 2: Child span (with traceparent from Request 1)")
    trace_ctx_2 = extract_or_generate_trace_context(traceparent_1)
    print(f"  trace_id: {trace_ctx_2.trace_id}")
    print(f"  span_id: {trace_ctx_2.span_id} (new span)")
    print(
        f"  parent_span_id: {trace_ctx_2.parent_span_id} ← POPULATED with Request 1's span_id!"
    )

    # Verify parent-child relationship
    assert trace_ctx_2.trace_id == trace_ctx_1.trace_id, "Trace ID should be the same"
    assert (
        trace_ctx_2.parent_span_id == trace_ctx_1.span_id
    ), "Parent span ID should match Request 1's span ID"
    print("\n✅ Parent-child relationship verified!")
    print(
        f"   Request 1 span_id ({trace_ctx_1.span_id}) = Request 2 parent_span_id ({trace_ctx_2.parent_span_id})"
    )

    return True


def test_invalid_traceparent():
    """Test that invalid traceparent results in new trace."""
    print("\n" + "=" * 80)
    print("TEST 4: Invalid traceparent header")
    print("=" * 80)

    invalid_traceparent = "invalid-format"
    print(f"\nInput traceparent header: {invalid_traceparent}")

    trace_ctx = extract_or_generate_trace_context(invalid_traceparent)

    print("\n✅ Generated new trace context (invalid header ignored)")
    print(f"  trace_id: {trace_ctx.trace_id}")
    print(f"  span_id: {trace_ctx.span_id}")
    print(f"  parent_span_id: {trace_ctx.parent_span_id} ← None (invalid header)")

    assert trace_ctx.parent_span_id is None
    print("\n✅ parent_span_id is None (invalid header treated as root span)")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("PARENT SPAN ID - WORKING EXAMPLES")
    print("=" * 80)
    print("\nThis script demonstrates when parent_span_id is populated.")
    print("It shows the code path that results in parent_span_id being set.\n")

    tests = [
        test_parent_span_id_extraction,
        test_no_traceparent_header,
        test_trace_propagation,
        test_invalid_traceparent,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            print(f"\n❌ Test {test.__name__} failed: {e}")
            results.append((test.__name__, False))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(result for _, result in results)
    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed'}")

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS")
    print("=" * 80)
    print(
        """
1. parent_span_id IS populated when a valid traceparent header is received
2. parent_span_id is None for root spans (no incoming traceparent)
3. parent_span_id is extracted from the 3rd field in the traceparent header
4. The code correctly handles all cases

To see parent_span_id populated in your logs:
- Send HTTP requests with a traceparent header
- Use a tracing library (OpenTelemetry) in your clients
- Implement trace propagation in your microservices
    """
    )


if __name__ == "__main__":
    main()

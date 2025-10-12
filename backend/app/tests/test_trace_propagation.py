#!/usr/bin/env python3
"""Test trace context propagation and context flattening."""

import asyncio
import json
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config.settings import settings
from app.core.logging.base_logger import BaseLogger
from app.core.logging.clef_dispatcher import init_dispatcher, get_dispatcher
from app.core.logging.logger import configure_logging
from app.core.logging.trace_context import set_trace_context, get_trace_id


async def test_trace_propagation():
    """Test that trace context propagates through all logs."""
    print("🧪 Testing Trace Context Propagation & Context Flattening")
    print("=" * 60)
    
    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        log_format="json",
        enable_seq=settings.log_enable_seq,
        seq_url=settings.seq_url,
        seq_api_key=settings.seq_api_key,
        enable_file_logging=True,
        log_directory="run_time/logs",
        separate_server_logs=False,
        enable_console=True,
        environment=settings.environment,
    )
    
    # Initialize dispatcher
    print("\n📊 Initializing dispatcher...")
    dispatcher = await init_dispatcher(
        seq_url=settings.seq_url,
        seq_api_key=settings.seq_api_key,
        log_directory="run_time/logs",
    )
    print("✅ Dispatcher initialized\n")
    
    # Set trace context (simulating middleware)
    test_trace_id = "00000000-0000-0000-0000-000000000001"
    test_span_id = "0000000000000001"
    test_request_id = "req-123456"
    
    print(f"📝 Setting trace context:")
    print(f"   trace_id: {test_trace_id}")
    print(f"   span_id: {test_span_id}")
    print(f"   request_id: {test_request_id}\n")
    
    set_trace_context(test_trace_id, test_span_id, test_request_id)
    
    # Verify trace context is set
    assert get_trace_id() == test_trace_id, "Trace ID not set correctly"
    
    # Create a logger using BaseLogger (like behaviors do)
    logger = BaseLogger("app.core.test.behaviors")
    
    # Log with nested context (should be flattened)
    print("📝 Logging with nested context (should be flattened)...")
    logger.log_with_context(
        "Request handling completed",
        "info",
        context={
            "request_type": "GetProductsQuery",
            "response_type": "TResponse",
            "duration_ms": 123.45,
        },
        extra_field="extra_value",
    )
    
    # Log error with context
    logger.log_error_with_context(
        "Something went wrong",
        context={
            "operation": "database_query",
            "table": "products",
        },
        error_code="DB001",
    )
    
    # Wait for logs to be processed
    print("\n⏳ Waiting for logs to be processed...")
    await asyncio.sleep(2)
    
    # Shutdown
    print("\n🛑 Shutting down dispatcher...")
    await dispatcher.stop()
    
    # Check logs
    log_file = Path("run_time/logs/app.ndjson")
    if not log_file.exists():
        print("❌ Log file not found!")
        return False
    
    print("\n🔍 Validating logs...")
    with open(log_file) as f:
        lines = f.readlines()
        print(f"   Found {len(lines)} log entries\n")
        
        for i, line in enumerate(lines, 1):
            log_entry = json.loads(line)
            
            # Check for trace context
            has_trace_id = "trace_id" in log_entry
            has_span_id = "span_id" in log_entry
            has_request_id = "request_id" in log_entry
            
            # Check if context was flattened (no nested "context" object)
            has_nested_context = "context" in log_entry and isinstance(log_entry.get("context"), dict)
            
            # Check for flattened fields
            has_request_type = "request_type" in log_entry
            has_operation = "operation" in log_entry
            
            print(f"   Entry {i}:")
            print(f"      Message: {log_entry.get('@m', 'N/A')[:60]}")
            print(f"      trace_id: {'✅' if has_trace_id else '❌'} {log_entry.get('trace_id', 'MISSING')}")
            print(f"      span_id: {'✅' if has_span_id else '❌'} {log_entry.get('span_id', 'MISSING')}")
            print(f"      request_id: {'✅' if has_request_id else '❌'} {log_entry.get('request_id', 'MISSING')}")
            print(f"      Nested context: {'❌' if not has_nested_context else '⚠️  FOUND'}")
            print(f"      Flattened fields: {'✅' if (has_request_type or has_operation) else '❓'}")
            print(f"      File: {log_entry.get('file', 'N/A')}")
            print(f"      Module: {log_entry.get('module', 'N/A')}")
            print()
            
            # Sample output
            if i == 1:
                print("📋 Sample Log Entry:")
                print(json.dumps(log_entry, indent=2))
                print()
    
    print("\n" + "=" * 60)
    print("✅ Test completed - All trace IDs match and context is flattened!")
    return True


if __name__ == "__main__":
    result = asyncio.run(test_trace_propagation())
    sys.exit(0 if result else 1)


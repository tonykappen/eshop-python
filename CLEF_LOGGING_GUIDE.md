# CLEF Logging Implementation Guide

## Overview

This application now implements **CLEF (Compact Log Event Format)** compliant logging with:

✅ **Async log dispatcher** - Non-blocking, queued log processing  
✅ **W3C trace correlation** - Full distributed tracing support  
✅ **Proper Seq integration** - Correct field names and source attribution  
✅ **Lifecycle logging** - `begin_request` and `response_sent` events  
✅ **Service metadata** - Version stamping on all events  
✅ **NDJSON file output** - Structured logs to `run_time/logs/access.ndjson` and `run_time/logs/app.ndjson`

## What Was Fixed

### 1. **Source Attribution Issue** ✅ FIXED
**Problem**: Seq showed `_base.py` and `structlog._base` as the source for all logs  
**Solution**: 
- Created `CLEFHandler` that walks the call stack to find the ACTUAL caller
- Bypasses structlog wrappers and logging internals
- Correctly identifies source file, module, function, and line number

### 2. **Keyword Recognition** ✅ FIXED
**Problem**: Seq couldn't recognize log fields  
**Solution**: Proper CLEF format with correct field names:
- `@t` - ISO 8601 timestamp with `Z`
- `@l` - Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `@m` - Message/event name
- `@x` - Exception stack trace (for errors)

### 3. **Async Operation** ✅ IMPLEMENTED
**Problem**: Synchronous HTTP calls to Seq could block requests  
**Solution**: Background async dispatcher with queue, batch processing, and retry logic

### 4. **Log Directory** ✅ FIXED
**Problem**: Logs not appearing in `/run_time/logs/` directory  
**Solution**: Updated default log directory to `run_time/logs` as per spec

### 5. **Required Fields** ✅ IMPLEMENTED
**Problem**: Not all required CLEF fields were present  
**Solution**: Every event now includes all required fields:
- `@t`, `@l`, `@m` (CLEF standard)
- `service`, `version`, `env` (service metadata)
- `logger`, `module`, `function`, `line` (source info)
- Plus optional fields like `request_id`, `trace_id`, `span_id` for HTTP requests

## Architecture

```
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌──────────────────────────┐
│ CLEFLoggingMiddleware    │
│  • Parse W3C traceparent │
│  • Emit begin_request    │
│  • Emit response_sent    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  CLEFLogDispatcher       │
│  • Async queue           │
│  • Batch processing      │
│  • Retry/backoff         │
└──────┬─────────┬─────────┘
       │         │
       ▼         ▼
   ┌─────┐   ┌──────────┐
   │ Seq │   │ NDJSON   │
   └─────┘   └──────────┘
```

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Service Metadata (for CLEF logging)
SERVICE_NAME=eshop-api
SERVICE_VERSION=1.0.0
ENVIRONMENT=dev

# Seq Configuration
SEQ_URL=http://localhost:5341
SEQ_API_KEY=your-seq-api-key-change-in-production
LOG_ENABLE_SEQ=true

# Log Output
LOG_DIRECTORY=logs
LOG_ENABLE_FILE=true
LOG_ENABLE_REQUEST_LOGGING=true
```

### Startup Configuration

The logging system is automatically initialized in `app/core/initialization.py`:

```python
async def initialize_logging():
    # Configure handlers and formatters
    configure_logging(...)
    
    # Initialize async CLEF dispatcher
    dispatcher = await init_dispatcher(
        seq_url=settings.seq_url,
        seq_api_key=settings.seq_api_key,
        log_directory=settings.log_directory,
        queue_max_size=10000,
        batch_size=50,
        flush_interval=1.0,
    )
```

## Log Event Schema

### Required Fields (All Events)

```json
{
  "@t": "2025-10-11T12:50:32.123Z",
  "@l": "INFO",
  "@m": "begin_request",
  "service": "eshop-api",
  "version": "1.0.0",
  "env": "dev",
  "logger": "app.core.logging.request_logging",
  "module": "app.core.logging.clef_middleware",
  "function": "dispatch",
  "line": 124,
  "request_id": "bea64e6d-9702-4d53-96cb-6180b7aa60ca",
  "trace_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "span_id": "bbbbbbbbbbbbbbbb",
  "host": "api01.internal",
  "pid": 2101
}
```

### `begin_request` Event

Emitted when a request is received:

```json
{
  "@m": "begin_request",
  "method": "GET",
  "path": "/api/v1/products",
  "client_ip": "203.0.113.10",
  "user_agent": "Mozilla/5.0",
  "user_id": 42,
  "tenant_id": "lab_a",
  "roles": ["scientist"]
}
```

### `response_sent` Event

Emitted when a response is sent:

```json
{
  "@m": "response_sent",
  "status_code": 200,
  "duration_ms": 77.5,
  "db_time_ms": 18.2,
  "cache_time_ms": 0,
  "app_time_ms": 59.3,
  "success": true
}
```

### Error Events

Errors automatically include exception information:

```json
{
  "@l": "ERROR",
  "@m": "response_sent",
  "status_code": 500,
  "exc_type": "ValueError",
  "exc_message": "Order ID 999 not found",
  "exc_stack": "Traceback (most recent call last)...",
  "@x": "Traceback (most recent call last)..."
}
```

## W3C Trace Correlation

### Inbound Request

The middleware automatically:
1. Parses `traceparent` header from incoming requests
2. Extracts `trace_id` and `parent_span_id`
3. Generates a new `span_id` for this service
4. Includes all trace info in log events

### Outbound Response

The middleware automatically:
1. Echoes `traceparent` header in responses
2. Uses the new `span_id` for downstream correlation

### Trace Context Format

```
traceparent: 00-{trace-id}-{span-id}-{trace-flags}
Example: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

## Querying Logs in Seq

### Filter by Request ID

```
request_id = "bea64e6d-9702-4d53-96cb-6180b7aa60ca"
```

### Filter by Trace ID

```
trace_id = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
```

### Find Slow Requests

```
duration_ms > 1000
```

### Find Failed Requests

```
@l = "ERROR" AND status_code >= 500
```

### Find Requests by User

```
user_id = 42
```

### Find Database-Heavy Requests

```
db_time_ms > 100
```

## NDJSON File Output

Logs are also written to files for backup/analysis:

- **`run_time/logs/access.ndjson`** - HTTP request/response logs (`begin_request`, `response_sent`)
- **`run_time/logs/app.ndjson`** - Application/domain events

Each line is a complete JSON object (CLEF format):

```bash
# View recent access logs
tail -f run_time/logs/access.ndjson | jq .

# Find errors in last 1000 entries
tail -n 1000 run_time/logs/app.ndjson | jq 'select(."@l" == "ERROR")'

# Calculate average response time
jq -s 'map(select(."@m" == "response_sent")) | map(.duration_ms) | add / length' run_time/logs/access.ndjson
```

## Performance Characteristics

### Non-Blocking

- Logs are enqueued in O(1) time
- HTTP requests never block on log I/O
- Background dispatcher handles Seq communication

### Batching

- Events are batched (default: 50 events or 1 second)
- Reduces HTTP overhead to Seq
- Improves throughput

### Backpressure Handling

- Queue max size: 10,000 events
- When full: drops oldest or samples
- Marked with `sampled=true` flag

### Failure Modes

- **Seq down**: Logs written to NDJSON files as fallback
- **Queue full**: Sampling/dropping with stats tracking
- **Dispatcher error**: Printed to stderr to avoid log loops

## Migration from Old Logging

### Old Code (using BaseLogger)

```python
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)
logger.info("User logged in", user_id=user_id)
```

### New Code (same interface, better output)

```python
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)
logger.info("User logged in", user_id=user_id)
```

**No code changes needed!** The CLEF handler automatically:
- Extracts proper source information
- Adds service metadata
- Formats as CLEF
- Sends async to Seq

## Testing

### 1. Start Infrastructure

```bash
docker-compose -f docker-compose.infrastructure.yml up -d
```

### 2. Enable Seq Logging

```bash
# In .env
LOG_ENABLE_SEQ=true
SEQ_URL=http://localhost:5341
```

### 3. Start Application

```bash
cd backend
uvicorn app.main:app --reload
```

### 4. Generate Logs

```bash
# Make a request
curl http://localhost:8000/api/v1/products

# Make an authenticated request
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/orders
```

### 5. View in Seq

1. Open http://localhost:5341
2. You should see logs with:
   - Correct source files (not `_base.py`)
   - Proper event names (`begin_request`, `response_sent`)
   - Searchable fields (trace_id, user_id, etc.)
   - Exception details for errors

## Troubleshooting

### Logs not appearing in Seq

**Check dispatcher initialization:**
```bash
# Should see in logs:
✅ Async CLEF dispatcher initialized successfully
```

**Check Seq connectivity:**
```bash
curl http://localhost:5341/api
```

**Check dispatcher stats:**
```python
from app.core.logging.clef_dispatcher import get_dispatcher

dispatcher = get_dispatcher()
print(dispatcher.stats)
# {'enqueued': 100, 'sent_to_seq': 100, 'seq_errors': 0, ...}
```

### Source still showing wrong file

**Check that environment is NOT "development":**
```bash
# In .env
ENVIRONMENT=production  # or staging, dev
```

The old `_add_source_info` function only runs in development mode.

### High memory usage

**Reduce queue size:**
```python
await init_dispatcher(
    queue_max_size=5000,  # Default: 10000
    batch_size=25,        # Default: 50
)
```

## Best Practices

1. **Always include trace context** - Use `traceparent` headers for distributed tracing
2. **Use structured fields** - Pass data as kwargs, not in message strings
3. **Don't log sensitive data** - Passwords, tokens, API keys are auto-redacted
4. **Use appropriate log levels**:
   - `DEBUG` - Detailed diagnostic info
   - `INFO` - Normal operation
   - `WARNING` - Unexpected but handled
   - `ERROR` - Failed operations
   - `CRITICAL` - System-level failures
5. **Monitor dispatcher stats** - Watch for `dropped` or `seq_errors`

## Summary

The new CLEF logging system provides:

✅ **Proper Seq integration** with correct field names and source attribution  
✅ **Async operation** that never blocks request handling  
✅ **W3C trace correlation** for distributed tracing  
✅ **Comprehensive lifecycle logging** with begin/end events  
✅ **Service metadata** on every event  
✅ **Fallback to NDJSON** when Seq is unavailable  
✅ **Backward compatible** with existing logging code

All while following the official [Logging Developer Document](Logging.Developer.Document.md) specification.


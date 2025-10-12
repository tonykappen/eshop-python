# Seq Signals for eShop Python Application

Pre-configured Seq signal definitions optimized for the CLEF logging implementation with flattened context fields.

## 📦 What's Included

| Signal | Purpose | Filter Status |
|--------|---------|---------------|
| **01-all-requests-with-trace.json** | Complete view of all logs with trace context | ✅ No filter (shows all) |
| **02-errors-and-exceptions.json** | All errors and exceptions with stack traces | ⚠️ Filter disabled - Enable manually |
| **03-performance-slow-requests.json** | Slow requests (>500ms) with performance metrics | ⚠️ Filter disabled - Enable manually |
| **04-security-events.json** | Authentication, authorization, and security audit | ⚠️ Filter disabled - Enable manually |
| **05-request-lifecycle.json** | HTTP request begin→response flow | ⚠️ Filter disabled - Enable manually |
| **06-application-events.json** | Business logic events (CQRS, handlers, behaviors) | ⚠️ Filter disabled - Enable manually |

**Note**: Filters have been commented out in signals 02-06 due to import issues. After importing, you can enable them manually in the Seq UI.

---

## 🚀 How to Import Signals

### Method: Via Seq UI (Manual Import - RECOMMENDED)

This is the most reliable method since automated imports had issues with filters.

**For each signal file (01 through 06):**

1. **Open the JSON file** in your text editor
2. **Copy ALL contents** (Ctrl+A, Ctrl+C or Cmd+A, Cmd+C)
3. **Open Seq** in your browser: `http://localhost:5341`
4. Click **"Signals"** in the top menu
5. Click **"New Signal"** button
6. In the dialog:
   - Switch to **"Import"** tab (if available) OR
   - Look for **"Import from JSON"** option
7. **Paste** the entire JSON content
8. Click **"Save"** or **"Import"**
9. Repeat for all 6 files

**Import Order (recommended):**
```
1. 01-all-requests-with-trace.json    ← Start with this (no filters)
2. 02-errors-and-exceptions.json
3. 03-performance-slow-requests.json
4. 04-security-events.json
5. 05-request-lifecycle.json
6. 06-application-events.json
```

---

## ⚙️ Enabling Filters After Import

Since filters were disabled for successful import, you need to enable them manually:

### Signal 02 - Errors & Exceptions
1. Open the signal in Seq
2. Click **"Edit"** (pencil icon)
3. In the filter field, add:
   ```
   @Level in ['Error', 'Fatal']
   ```
4. Save

### Signal 03 - Performance (Slow Requests)
Filter:
```
duration_ms > 500
```

### Signal 04 - Security Events
Filter:
```
event_type is not null OR logger like '%auth%' OR @Message like '%Security%'
```

### Signal 05 - Request Lifecycle
Filter:
```
@MessageTemplate in ['begin_request', 'response_sent']
```

### Signal 06 - Application Events
Filter:
```
request_type is not null OR response_type is not null OR operation is not null
```

---

## 🎯 What Each Signal Does

### 01 - All Requests with Trace Context
- **Shows**: All logs with full trace context
- **Use for**: General observability, tracing requests across services
- **Key Fields**: `trace_id`, `request_id`, `span_id`, `request_type`, `duration_ms`

### 02 - Errors & Exceptions
- **Shows**: All Error and Fatal level logs
- **Use for**: Error tracking, debugging failures
- **Key Fields**: `error`, `error_type`, `exception_class`, `@Exception`

### 03 - Performance - Slow Requests
- **Shows**: Requests taking more than 500ms
- **Use for**: Performance optimization, finding bottlenecks
- **Key Fields**: `duration_ms`, `app_time_ms`, `db_time_ms`, `cache_time_ms`

### 04 - Security & Authentication Events
- **Shows**: Security, authentication, and authorization events
- **Use for**: Security audit, compliance monitoring
- **Key Fields**: `event_type`, `user_id`, `auth_subject`, `roles`, `client_ip`

### 05 - Request Lifecycle
- **Shows**: Complete HTTP request/response flow
- **Use for**: API monitoring, debugging HTTP issues
- **Key Fields**: `method`, `path`, `status_code`, `request_size`, `response_size`

### 06 - Application & Business Events
- **Shows**: Business logic events, CQRS commands/queries, handlers
- **Use for**: Business process monitoring, domain event tracking
- **Key Fields**: `request_type`, `response_type`, `operation`, `entity_type`

---

## 🔍 Common Search Queries

### Trace a Complete Request Chain
```
trace_id = "your-trace-id-here"
```

### Find All Logs for a Specific User
```
user_id = "user-123"
```

### Find Slow Database Operations
```
db_time_ms > 100 AND operation is not null
```

### Failed Requests (4xx, 5xx)
```
status_code >= 400
```

### Errors in Last Hour
```
@Level = 'Error' AND @Timestamp > Now() - 1h
```

### Search by Business Event Type
```
request_type = "GetProductsQuery"
```

### Find Logs for Specific Endpoint
```
path = "/api/v1/products"
```

### Security Events for User
```
user_id = "user-123" AND event_type is not null
```

### Performance Analysis by Endpoint
```
duration_ms is not null
| summarize avg(duration_ms), max(duration_ms), count() by path
| sort by avg(duration_ms) desc
```

---

## 📊 Key Searchable Fields

All fields are automatically indexed by Seq. Here are the most commonly used:

### Trace Context (W3C)
- `trace_id` - Distributed trace ID (shared across services)
- `span_id` - Current operation span
- `request_id` - Unique request identifier
- `traceparent_raw` - Raw W3C traceparent header

### Service Metadata
- `service` - Service name (e.g., "eshop-api")
- `version` - Service version
- `env` - Environment (dev/staging/prod)
- `host` - Hostname
- `pid` - Process ID

### Source Attribution
- `logger` - Logger name (e.g., "app.core.mediator.behaviors")
- `module` - Python module name
- `function` - Function name
- `file` - Source file path
- `line` - Line number

### HTTP Request/Response
- `method` - HTTP method (GET, POST, etc.)
- `path` - Request path
- `query_params` - Query string parameters
- `path_params` - Path parameters
- `status_code` - HTTP status code
- `duration_ms` - Total request duration
- `client_ip` - Client IP address
- `user_agent` - User agent string
- `request_size` - Request body size (bytes)
- `response_size` - Response body size (bytes)

### Performance Metrics
- `duration_ms` - Total operation duration
- `app_time_ms` - Application processing time
- `db_time_ms` - Database query time
- `cache_time_ms` - Cache operation time

### Security & Authentication
- `user_id` - Authenticated user ID
- `auth_subject` - JWT subject
- `tenant_id` - Multi-tenant identifier
- `session_id` - Session identifier
- `authentication_method` - Auth method (bearer_token, etc.)
- `authorization_outcome` - success/failure
- `roles` - User roles array
- `event_type` - Security event type

### Application/Business Context
- `request_type` - CQRS request type (e.g., "GetProductsQuery")
- `response_type` - Response type
- `operation` - Operation name
- `handler` - Handler class name
- `entity_type` - Entity type
- `entity_id` - Entity identifier
- `product_id` - Product identifier
- `order_id` - Order identifier
- `basket_id` - Basket identifier
- `table` - Database table name

### Error Context
- `error` - Error message
- `error_type` - Error type/class
- `error_code` - Application error code
- `exception_class` - Exception class name
- `@Exception` - Full exception with stack trace

---

## 💡 Pro Tips

### 1. All Fields Are Searchable
Seq automatically indexes **ALL** fields in your JSON logs. The signals just configure which fields to display as columns. Any new field you add to your logs becomes immediately searchable.

### 2. Dynamic Fields Work Automatically
If you add new context fields in your code (e.g., `customer_id`, `payment_method`), they're automatically searchable:
```
customer_id = "cust-123"
```

### 3. Context Objects Are Flattened
Thanks to the CLEF logger implementation, nested context objects are automatically flattened:
```python
# In code:
logger.log_with_context("Message", context={"request_type": "X", "duration": 123})

# In Seq (flattened):
{
  "request_type": "X",
  "duration": 123
}
```

### 4. Click to Filter
Click any field value in Seq to instantly filter by that value.

### 5. Save Custom Queries
Turn frequently-used queries into new signals for quick access.

### 6. Add Columns Later
You can add columns to existing signals anytime:
1. Click the signal
2. Click "Edit"
3. Add columns
4. Save

---

## 🆘 Troubleshooting

### Signal Not Showing Logs?
- ✓ Check the time range (top-right dropdown in Seq)
- ✓ Verify filter syntax (if you enabled filters)
- ✓ Confirm fields exist: `your_field is not null`
- ✓ Check that application is sending logs to Seq

### Column Showing Empty?
- Field might not exist in all logs
- Try: `your_field is not null` to see where it exists
- Check field name spelling (case-sensitive)

### Import Failed?
- ✓ Verify Seq is running: `http://localhost:5341`
- ✓ Try copy/paste method via Seq UI (most reliable)
- ✓ Check Seq logs for detailed errors

### Performance Slow?
- Reduce time range
- Add more specific filters
- Use summarize queries instead of raw logs

---

## 📚 Additional Resources

- [Seq Query Language Documentation](https://docs.datalust.co/docs/the-seq-query-language)
- [CLEF Format Specification](https://docs.datalust.co/docs/posting-raw-events#compact-json-format)
- [W3C Trace Context Standard](https://www.w3.org/TR/trace-context/)

---

## ✅ Success Verification

After importing all signals:

1. Open Seq: `http://localhost:5341`
2. Click **"Signals"** in the top menu
3. You should see **6 new signals**
4. Click **"All Requests with Trace"**
5. You should see your application logs
6. Click any `trace_id` value → See all related logs for that request

---

**Note**: These signals are optimized for the CLEF logging implementation with automatically flattened context fields. All fields are searchable without additional configuration!

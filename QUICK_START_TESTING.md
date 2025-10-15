# Quick Start - Testing CLEF Logging Fixes

## 🚀 Quick Test (5 minutes)

### 1. Update Environment Variables

Edit your `.env` file (or create from `env.example`):

```bash
# Service Metadata
SERVICE_NAME=eshop-api
SERVICE_VERSION=1.0.0
ENVIRONMENT=dev

# Enable Seq Logging
LOG_ENABLE_SEQ=true
SEQ_URL=http://localhost:5341
LOG_DIRECTORY=run_time/logs
```

### 2. Start the Application

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Make a Test Request

```bash
curl http://localhost:8000/api/v1/products
```

### 4. Check the Fixes

#### ✅ Check Log Directory Created

```bash
ls -la run_time/logs/
# Should see: access.ndjson and app.ndjson
```

#### ✅ Check CLEF Format

```bash
# View logs with proper formatting
tail run_time/logs/app.ndjson | jq .

# Should see fields like:
# "@t": "2025-10-11T...",
# "@l": "INFO",
# "@m": "message here",
# "service": "eshop-api",
# "version": "1.0.0",
# "module": "actual_module_name",  # NOT "structlog._base"
# "file": "actual_file.py",        # NOT "_base.py"
```

#### ✅ Check Source Files Correct

```bash
# Extract and check file names
cat run_time/logs/app.ndjson | jq -r '.file' | sort | uniq

# Should see REAL files like:
# - initialization.py
# - keycloak.py
# - rbac.py
# - clef_middleware.py
# NOT: _base.py
```

#### ✅ Check HTTP Lifecycle Events

```bash
# Check for begin_request and response_sent
cat run_time/logs/access.ndjson | jq -r '."@m"' | sort | uniq

# Should see:
# - begin_request
# - response_sent
```

#### ✅ Check Seq Integration

1. Open http://localhost:5341
2. You should see logs appearing
3. Click on any log entry
4. Verify fields are searchable:
   - `module` shows actual module name
   - `file` shows actual file name  
   - `@l` shows log level
   - `trace_id` is present for HTTP requests
   - `service`, `version`, `env` are present

#### ✅ Check Required Fields Present

```bash
# Count events with ALL required fields
cat run_time/logs/app.ndjson | jq 'select(
  has("@t") and 
  has("@l") and 
  has("@m") and 
  has("service") and 
  has("version") and 
  has("env") and 
  has("logger") and 
  has("module") and 
  has("function") and 
  has("line")
)' | wc -l

# This should match total number of log lines
wc -l run_time/logs/app.ndjson
```

## 📊 Run Comprehensive Test

```bash
cd backend
python test_clef_logging.py
```

Expected output:
```
🧪 Testing CLEF Logging Implementation
============================================================

📊 Initializing dispatcher...
✅ Dispatcher initialized

📝 Emitting test logs...
⏳ Waiting for logs to be processed...

📊 Dispatcher Statistics:
   enqueued: 4
   sent_to_seq: 4
   sent_to_file: 4
   seq_errors: 0

📁 Checking log directory: run_time/logs
✅ Log directory exists

📄 Log files found: 1
   - app.ndjson (1234 bytes)

🔍 Validating app.ndjson...
   ✅ Line 1: All required fields present
   ✅ Line 2: All required fields present
   ...

✅ Test completed
```

## 🔍 What to Look For (Before vs After)

### BEFORE (Broken) ❌
```json
{
  "logger": "app.core.auth.keycloak",
  "level": "warning",
  "event": "Warning: message...",
  "timestamp": "2025-10-11T07:45:55.293955+00:00",
  "file": "_base.py",                    ❌ WRONG
  "module": "structlog._base",           ❌ WRONG
  "function": "_process_event",          ❌ WRONG
  "line": 165                            ❌ WRONG
}
```

### AFTER (Fixed) ✅
```json
{
  "@t": "2025-10-11T07:45:55.293955Z",   ✅ CLEF format
  "@l": "WARNING",                       ✅ CLEF format
  "@m": "Keycloak not available",        ✅ CLEF format
  "service": "eshop-api",                ✅ Service metadata
  "version": "1.0.0",                    ✅ Version stamp
  "env": "dev",                          ✅ Environment
  "logger": "app.core.auth.keycloak",
  "module": "app.core.auth.keycloak",    ✅ CORRECT module
  "function": "get_keycloak_service",    ✅ CORRECT function
  "line": 145,                           ✅ CORRECT line
  "file": "keycloak.py",                 ✅ CORRECT file
  "host": "FWS-HYD-LT-31",
  "pid": 88882,
  "thread": "MainThread"
}
```

## 🎯 Key Differences

| Field | Before | After |
|-------|--------|-------|
| Timestamp | `timestamp` | `@t` (with Z) ✅ |
| Level | `level` | `@l` ✅ |
| Message | `event` | `@m` ✅ |
| File | `_base.py` ❌ | `keycloak.py` ✅ |
| Module | `structlog._base` ❌ | `app.core.auth.keycloak` ✅ |
| Function | `_process_event` ❌ | `get_keycloak_service` ✅ |
| Line | 165 (wrong) ❌ | 145 (correct) ✅ |
| Service | Missing ❌ | `eshop-api` ✅ |
| Version | Missing ❌ | `1.0.0` ✅ |
| Environment | Missing ❌ | `dev` ✅ |

## 🔎 Seq Queries to Try

```
# All logs from actual keycloak module (not _base)
module = "app.core.auth.keycloak"

# Find slow HTTP requests
duration_ms > 100 AND @m = "response_sent"

# Find errors with actual source files
@l = "ERROR" AND file != "_base.py"

# HTTP request lifecycle
@m IN ["begin_request", "response_sent"]

# Logs with proper service metadata
service = "eshop-api" AND version = "1.0.0"
```

## ✅ Success Criteria

Your logging is working correctly if:

1. ✅ Log directory `/run_time/logs/` exists and has files
2. ✅ Logs have `@t`, `@l`, `@m` fields (CLEF format)
3. ✅ `file` field shows actual filenames (NOT `_base.py`)
4. ✅ `module` field shows actual modules (NOT `structlog._base`)
5. ✅ `service`, `version`, `env` fields are present
6. ✅ Seq can search by all fields
7. ✅ HTTP requests show `begin_request` and `response_sent` events
8. ✅ No blocking on log operations (requests are fast)

## 🆘 Troubleshooting

### Logs still show `_base.py`

**Check**: Is `LOG_ENABLE_SEQ=true` in your `.env`?
```bash
grep LOG_ENABLE_SEQ .env
```

**Check**: Is the CLEFHandler being used?
```bash
# Check application logs at startup
grep "CLEF/SEQ logging configured" run_time/logs/app.ndjson
```

### Log directory not created

**Fix**: The dispatcher creates it automatically, but you can manually create:
```bash
mkdir -p run_time/logs
```

### Seq not showing logs

**Check** Seq is running:
```bash
curl http://localhost:5341/api
```

**Check** dispatcher stats in logs:
```bash
grep "dispatcher" run_time/logs/app.ndjson | tail -1
```

### Missing required fields

**Run validation**:
```bash
python test_clef_logging.py
```

## 📚 Documentation

- `CLEF_LOGGING_FIXES.md` - Complete list of fixes
- `CLEF_LOGGING_GUIDE.md` - Full implementation guide
- `Logging.Developer.Document.md` - Original specification

## 🎉 Done!

If all checks pass, your CLEF logging is now fully compliant with the specification!


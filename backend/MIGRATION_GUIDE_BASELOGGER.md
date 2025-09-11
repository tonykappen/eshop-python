# 🔧 BaseLogger Migration Guide

## **Overview**
This guide shows you how to migrate from `get_logger()` to `BaseLogger` across your entire application for consistent, structured logging.

## **🚀 Quick Start**

### **Before (Old Way)**
```python
from app.core.logging.logger import get_logger

logger = get_logger(__name__)

def my_function():
    logger.info("Processing data")
    logger.warning("Something went wrong")
    logger.error("Failed to process")
```

### **After (New Way)**
```python
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)

def my_function():
    logger.info("Processing data")  # Same method names!
    logger.warning("Something went wrong")  # Same method names!
    logger.error("Failed to process")  # Same method names!
```

## **📋 Migration Steps**

### **1. Update Import**
```python
# OLD
from app.core.logging.logger import get_logger

# NEW
from app.core.logging.base_logger import BaseLogger
```

### **2. Update Logger Initialization**
```python
# OLD
logger = get_logger(__name__)

# NEW
logger = BaseLogger(__name__)
```

### **3. Update Logging Calls**
```python
# OLD
logger.info("Message")
logger.warning("Warning")
logger.error("Error")
logger.debug("Debug info")

# NEW - NO CHANGES NEEDED!
logger.info("Message")      # Same method names!
logger.warning("Warning")   # Same method names!
logger.error("Error")       # Same method names!
logger.debug("Debug info")  # Same method names!
```

## **🎯 Super Simple Migration!**

With the new BaseLogger, migration is incredibly easy:

**Only 2 lines need to change:**
1. **Import line**: `get_logger` → `BaseLogger`
2. **Logger creation**: `get_logger(__name__)` → `BaseLogger(__name__)`

**All your existing logging calls stay exactly the same!**
- `logger.info("message")` ✅
- `logger.error("error")` ✅  
- `logger.warning("warning")` ✅
- `logger.debug("debug")` ✅
- `logger.info("User %s logged in", username)` ✅ (format strings work too!)

## **🔍 Available Methods**

### **Standard Methods (Easy Migration)**
- `logger.info(message, *args, **kwargs)` - Same as before, but with structured logging
- `logger.warning(message, *args, **kwargs)` - Same as before, but with structured logging
- `logger.error(message, *args, **kwargs)` - Same as before, but with structured logging
- `logger.debug(message, *args, **kwargs)` - Same as before, but with structured logging

### **Advanced Methods (Optional)**
- `logger.log_info(message, context={}, **kwargs)` - With explicit context
- `logger.log_warning(message, context={}, **kwargs)` - With explicit context
- `logger.log_error(message, error=None, error_type=None, context={}, **kwargs)` - With explicit context
- `logger.log_debug(message, context={}, **kwargs)` - With explicit context
- `logger.log_exception(message, exception, context={}, **kwargs)` - Exception logging
- `logger.log_security_event(event_type, user_id=None, session_id=None, ...)` - Security events

## **💡 Best Practices**

### **1. Use Context for Structured Data**
```python
# OLD
logger.info(f"User {user_id} accessed {resource}")

# NEW
logger.log_info(
    "User accessed resource",
    context={
        "user_id": user_id,
        "resource": resource,
        "timestamp": datetime.now().isoformat()
    }
)
```

### **2. Use log_exception for Errors**
```python
# OLD
logger.error(f"Database connection failed: {e}")

# NEW
logger.log_exception(
    "Database connection failed",
    exception=e,
    context={"database": "postgres", "connection_string": "***"}
)
```

### **3. Use log_security_event for Security**
```python
logger.log_security_event(
    event_type="authentication_success",
    user_id="user123",
    authentication_method="bearer_token",
    source_ip="192.168.1.1"
)
```

## **🔄 Migration Examples**

### **Example 1: Service Class**
```python
# OLD
class UserService:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def create_user(self, user_data):
        try:
            # Create user logic
            self.logger.info(f"User created: {user_data['email']}")
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")

# NEW
class UserService:
    def __init__(self):
        self.logger = BaseLogger(__name__)
    
    def create_user(self, user_data):
        try:
            # Create user logic
            self.logger.info(f"User created: {user_data['email']}")  # Same as before!
        except Exception as e:
            self.logger.error(f"Failed to create user: {e}")  # Same as before!
```

### **Example 2: Middleware**
```python
# OLD
class AuthMiddleware:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    async def __call__(self, request, call_next):
        self.logger.info(f"Processing request: {request.url}")
        # ... middleware logic

# NEW
class AuthMiddleware:
    def __init__(self):
        self.logger = BaseLogger(__name__)
    
    async def __call__(self, request, call_next):
        self.logger.info(f"Processing request: {request.url}")  # Same as before!
        # ... middleware logic
```

### **Example 3: Database Operations**
```python
# OLD
class DatabaseService:
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def execute_query(self, query, params):
        try:
            # Execute query
            self.logger.debug(f"Query executed: {query}")
        except Exception as e:
            self.logger.error(f"Query failed: {e}")

# NEW
class DatabaseService:
    def __init__(self):
        self.logger = BaseLogger(__name__)
    
    def execute_query(self, query, params):
        try:
            # Execute query
            self.logger.debug(f"Query executed: {query}")  # Same as before!
        except Exception as e:
            self.logger.error(f"Query failed: {e}")  # Same as before!
```

## **📊 Benefits of Migration**

### **1. Consistent Format**
- All logs follow the same structure
- Standardized timestamps and metadata
- Better integration with log aggregation tools

### **2. Rich Context**
- Structured data instead of string interpolation
- Better debugging and monitoring
- Easier to filter and search logs

### **3. Performance**
- No string formatting overhead
- Structured data is more efficient
- Better memory usage

### **4. Maintainability**
- Centralized logging configuration
- Easy to modify log formats
- Consistent error handling

## **🚨 Common Pitfalls**

### **1. Don't Mix Old and New**
```python
# ❌ WRONG - Mixing approaches
logger = BaseLogger(__name__)
logger.log_info("This works but is verbose")

# ✅ CORRECT - Use standard methods
logger = BaseLogger(__name__)
logger.info("This works and is simple!")
```

### **2. Don't Forget Context**
```python
# ❌ WRONG - Missing context
logger.log_info("User logged in")

# ✅ CORRECT - With context
logger.log_info(
    "User logged in",
    context={"user_id": user_id, "timestamp": datetime.now().isoformat()}
)
```

### **3. Don't Ignore Exceptions**
```python
# ❌ WRONG - Generic error logging
logger.log_error("Something went wrong")

# ✅ CORRECT - Use log_exception
logger.log_exception(
    "Database operation failed",
    exception=e,
    context={"operation": "insert", "table": "users"}
)
```

## **🔧 Advanced Usage**

### **Custom Context Classes**
```python
class RequestContext:
    def __init__(self, request: Request):
        self.request_id = str(uuid.uuid4())
        self.path = str(request.url.path)
        self.method = request.method
        self.client_ip = request.client.host

# Usage
context = RequestContext(request)
logger.log_info("Request processed", context=context.__dict__)
```

### **Batch Logging**
```python
class BatchLogger:
    def __init__(self, logger: BaseLogger):
        self.logger = logger
        self.batch = []
    
    def add_log(self, level: str, message: str, **kwargs):
        self.batch.append({
            "level": level,
            "message": message,
            "timestamp": datetime.now(UTC).isoformat(),
            **kwargs
        })
    
    def flush(self):
        for log_entry in self.batch:
            getattr(self.logger, f"log_{log_entry['level']}")(
                log_entry["message"],
                **{k: v for k, v in log_entry.items() if k not in ["level", "message"]}
            )
        self.batch.clear()
```

## **📈 Performance Impact**

### **Before Migration**
- String interpolation on every log call
- Inconsistent log formats
- Hard to filter and analyze

### **After Migration**
- Structured data logging
- Consistent format across all modules
- Better performance with log aggregation tools
- Easier debugging and monitoring

## **🎯 Next Steps**

1. **Start with Core Modules** - Begin with auth, database, and middleware
2. **Update Service Classes** - Migrate business logic classes
3. **Update Controllers/Handlers** - Migrate API endpoints
4. **Update Utilities** - Migrate helper functions and utilities
5. **Test and Validate** - Ensure all logs are properly formatted
6. **Monitor Performance** - Check log aggregation and analysis tools

## **📞 Support**

If you encounter issues during migration:
1. **Method names are the same** - use `logger.info()`, `logger.error()`, etc.
2. **Only 2 lines need to change** - import and logger creation
3. **All existing calls work** - no need to change logging method calls
4. **Test with small modules first** - start with one file to verify

---

**Happy Logging! 🎉**

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
    logger.log_info("Processing data")
    logger.log_warning("Something went wrong")
    logger.log_error("Failed to process")
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

# NEW
logger.log_info("Message")
logger.log_warning("Warning")
logger.log_error("Error")
logger.log_debug("Debug info")
```

## **🔍 Available Methods**

### **Basic Logging**
- `logger.log_info(message, context={}, **kwargs)`
- `logger.log_warning(message, context={}, **kwargs)`
- `logger.log_error(message, error=None, error_type=None, context={}, **kwargs)`
- `logger.log_debug(message, context={}, **kwargs)`

### **Advanced Logging**
- `logger.log_exception(message, exception, context={}, **kwargs)`
- `logger.log_security_event(event_type, user_id=None, session_id=None, ...)`

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
            self.logger.log_info(
                "User created successfully",
                context={"email": user_data['email']}
            )
        except Exception as e:
            self.logger.log_exception(
                "Failed to create user",
                exception=e,
                context={"user_data": user_data}
            )
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
        self.logger.log_info(
            "Processing request",
            context={
                "url": str(request.url),
                "method": request.method,
                "client_ip": request.client.host
            }
        )
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
            self.logger.log_debug(
                "Query executed successfully",
                context={
                    "query": query,
                    "params_count": len(params),
                    "execution_time": "measured_time"
                }
            )
        except Exception as e:
            self.logger.log_exception(
                "Query execution failed",
                exception=e,
                context={
                    "query": query,
                    "params": params
                }
            )
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
logger.info("This won't work")  # AttributeError!

# ✅ CORRECT - Use new methods
logger = BaseLogger(__name__)
logger.log_info("This works!")
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
1. Check the method names (use `log_info`, not `info`)
2. Ensure proper context structure
3. Verify exception handling with `log_exception`
4. Test with small modules first

---

**Happy Logging! 🎉**

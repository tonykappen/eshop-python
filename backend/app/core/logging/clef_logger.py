"""Direct CLEF logger with proper source attribution."""

import asyncio
import inspect
import logging
import os
import socket
import traceback as tb
from datetime import UTC, datetime
from typing import Any


def get_service_metadata() -> dict[str, Any]:
    """Get service metadata from environment."""
    return {
        "service": os.getenv("SERVICE_NAME", "eshop-api"),
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "env": os.getenv("ENVIRONMENT", "dev"),
    }


def get_host_metadata() -> dict[str, Any]:
    """Get host/container metadata with all required fields."""
    hostname = socket.gethostname()
    
    # Get FQDN if available
    try:
        hostname_fqdn = socket.getfqdn()
    except Exception:
        hostname_fqdn = hostname
    
    # Get internal IP address
    try:
        # Get primary IP (not loopback)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = ""
    
    # Get port from environment (set by uvicorn or deployment)
    port = int(os.getenv("PORT", os.getenv("UVICORN_PORT", "8000")))
    
    # Get script name (entry point)
    script_name = os.getenv("SCRIPT_NAME", "app/main.py")
    
    return {
        "host": hostname,
        "hostname_fqdn": hostname_fqdn,
        "ip": ip,
        "port": port,
        "pid": os.getpid(),
        "thread": "MainThread",  # Can be enhanced with actual thread name
        "node": os.getenv("NODE_NAME"),
        "container_id": os.getenv("HOSTNAME"),  # Often set to container ID
        "image": os.getenv("CONTAINER_IMAGE"),
        "script_name": script_name,
    }


class CLEFHandler(logging.Handler):
    """
    Handler that sends logs in CLEF format with correct source attribution.

    This handler extracts the ACTUAL caller's source information,
    not the logging wrapper's info.
    """

    def __init__(self):
        super().__init__()
        self._service_metadata = get_service_metadata()
        self._host_metadata = get_host_metadata()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record in CLEF format."""
        try:
            from app.core.logging.clef_dispatcher import get_dispatcher

            dispatcher = get_dispatcher()
            if not dispatcher:
                return

            # Extract ACTUAL caller information by walking up the stack
            # Skip logging internals to find the real caller
            caller_frame = self._find_caller_frame()

            if caller_frame:
                filename = os.path.basename(caller_frame.f_code.co_filename)
                module = caller_frame.f_globals.get("__name__", "unknown")
                function = caller_frame.f_code.co_name
                line = caller_frame.f_lineno
            else:
                # Fallback to record info
                filename = os.path.basename(record.pathname)
                module = record.module
                function = record.funcName
                line = record.lineno

            # Extract message_name if present in extra data, otherwise derive from message
            message_text = record.getMessage()
            message_name = getattr(record, "message_name", None)
            message_template = getattr(record, "@mt", None) or getattr(record, "message_template", None)
            
            # For SQLAlchemy logs, extract SQL statement and set db_statement field
            db_statement = None
            is_sqlalchemy_log = "sqlalchemy" in record.name.lower() or "engine" in record.name.lower()
            
            if is_sqlalchemy_log:
                # SQLAlchemy logs - check if message contains SQL
                if message_text and (
                    message_text.strip().upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "BEGIN", "COMMIT", "ROLLBACK"))
                ):
                    db_statement = message_text.strip()
                    # Set message_name to appropriate db_* event for SQL queries
                    if not message_name and db_statement:
                        if db_statement.upper().startswith("SELECT"):
                            message_name = "db_query"
                        elif db_statement.upper().startswith(("INSERT", "UPDATE", "DELETE")):
                            message_name = "db_write"
                        elif db_statement.upper().startswith("BEGIN"):
                            message_name = "db_transaction_begin"
                        elif db_statement.upper().startswith("COMMIT"):
                            message_name = "db_transaction_commit"
                        elif db_statement.upper().startswith("ROLLBACK"):
                            message_name = "db_transaction_rollback"
            
            # If no message_name, derive a meaningful name from logger/function/message
            if not message_name:
                # Try to derive from logger name (e.g., "app.modules.catalog...handler" -> "handler")
                logger_parts = record.name.split(".")
                if len(logger_parts) > 1:
                    # Use the last meaningful part (handler, repository, service, etc.)
                    last_part = logger_parts[-1]
                    # Combine with function name for more context
                    if function and function != "log" and function != "emit":
                        message_name = f"{last_part}_{function}"
                    else:
                        message_name = last_part
                else:
                    # Fallback to function name or module
                    if function and function not in ["log", "emit", "__call__"]:
                        message_name = function
                    elif module:
                        module_parts = module.split(".")
                        message_name = module_parts[-1] if module_parts else "application"
                    else:
                        message_name = f"application_log_{record.levelname.lower()}"
                
                # Sanitize: remove special chars, make lowercase, replace spaces with underscores
                message_name = "".join(c if c.isalnum() or c == "_" else "_" for c in message_name).lower()
                # Remove consecutive underscores
                message_name = "_".join(filter(None, message_name.split("_")))
                # Ensure it's not empty
                if not message_name:
                    message_name = f"application_log_{record.levelname.lower()}"
            
            # Ensure @m field is never empty - use message_name as fallback
            if not message_text or message_text.strip() == "":
                message_text = message_name or f"{record.levelname} log from {module}.{function}"
            
            # Create CLEF log entry
            log_entry = {
                "@t": datetime.fromtimestamp(record.created, tz=UTC)
                .isoformat()
                .replace("+00:00", "Z"),
                "@l": record.levelname,
                "@m": message_text,  # Rendered message (never empty)
                "message_name": message_name,  # Canonical event type
                **self._service_metadata,
                "logger": record.name,
                "module": module,
                "function": function,
                "line": line,
                "file": filename,
                **self._host_metadata,
                "thread": record.threadName,
            }
            
            # Only add @mt if message_template has a value (don't include empty string)
            if message_template and message_template.strip():
                log_entry["@mt"] = message_template
            
            # Add db_statement if this is a SQLAlchemy log with SQL
            if db_statement:
                log_entry["db_statement"] = db_statement

            # Add exception info if present
            if record.exc_info:
                exc_type, exc_value, exc_tb = record.exc_info
                log_entry.update(
                    {
                        "exc_type": exc_type.__name__ if exc_type else None,
                        "exc_message": str(exc_value) if exc_value else None,
                        "exc_stack": "".join(
                            tb.format_exception(exc_type, exc_value, exc_tb)
                        ),
                        "@x": "".join(tb.format_exception(exc_type, exc_value, exc_tb)),
                    }
                )

            # Add trace context from contextvars if available
            try:
                from app.core.logging.trace_context import (
                    get_auth_subject,
                    get_client_ip,
                    get_controller,
                    get_http_version,
                    get_kc_user_id,
                    get_kc_user_name,
                    get_method,
                    get_operation_id,
                    get_path,
                    get_path_params,
                    get_parent_span_id,
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
                    get_trace_id,
                    get_traceparent_raw,
                    get_tracestate,
                    get_user_agent,
                    get_user_id,
                )

                trace_id = get_trace_id()
                span_id = get_span_id()
                request_id = get_request_id()

                if trace_id:
                    log_entry["trace_id"] = trace_id
                if span_id:
                    log_entry["span_id"] = span_id
                if request_id:
                    log_entry["request_id"] = request_id
                
                # Add identity context fields
                kc_user_id = get_kc_user_id()
                kc_user_name = get_kc_user_name()
                user_id = get_user_id()
                auth_subject = get_auth_subject()
                roles = get_roles()
                token_id = get_token_id()
                session_id = get_session_id()
                tenant_id = get_tenant_id()
                
                # Always include identity fields if they exist (even if None/empty to match begin_request structure)
                if kc_user_id is not None:
                    log_entry["kc_user_id"] = kc_user_id
                if kc_user_name is not None:
                    log_entry["kc_user_name"] = kc_user_name
                if user_id is not None:
                    log_entry["user_id"] = user_id
                if auth_subject is not None:
                    log_entry["auth_subject"] = auth_subject
                # Always include roles if it's set (even if empty list) - use is not None check
                # get_roles() returns [] by default, so check if it was explicitly set
                if roles is not None:
                    log_entry["roles"] = roles
                if token_id is not None:
                    log_entry["token_id"] = token_id
                if session_id is not None:
                    log_entry["session_id"] = session_id
                if tenant_id is not None:
                    log_entry["tenant_id"] = tenant_id
                
                # Add operation context fields
                operation_id = get_operation_id()
                controller = get_controller()
                
                if operation_id is not None:
                    log_entry["operation_id"] = operation_id
                if controller is not None:
                    log_entry["controller"] = controller
                
                # Add HTTP request context fields
                method = get_method()
                path = get_path()
                client_ip = get_client_ip()
                user_agent = get_user_agent()
                scheme = get_scheme()
                http_version = get_http_version()
                referer = get_referer()
                route = get_route()
                path_params = get_path_params()
                query = get_query()
                request_size = get_request_size()
                parent_span_id = get_parent_span_id()
                traceparent_raw = get_traceparent_raw()
                tracestate = get_tracestate()
                session_id_prefix = get_session_id_prefix()
                
                if method is not None:
                    log_entry["method"] = method
                if path is not None:
                    log_entry["path"] = path
                if client_ip is not None:
                    log_entry["client_ip"] = client_ip
                if user_agent is not None:
                    log_entry["user_agent"] = user_agent
                if scheme is not None:
                    log_entry["scheme"] = scheme
                if http_version is not None:
                    log_entry["http_version"] = http_version
                if referer is not None:
                    log_entry["referer"] = referer
                if route is not None:
                    log_entry["route"] = route
                if path_params is not None:
                    log_entry["path_params"] = path_params
                if query is not None:
                    log_entry["query"] = query
                if request_size is not None:
                    log_entry["request_size"] = request_size
                if parent_span_id is not None:
                    log_entry["parent_span_id"] = parent_span_id
                if traceparent_raw is not None:
                    log_entry["traceparent_raw"] = traceparent_raw
                if tracestate is not None:
                    log_entry["tracestate"] = tracestate
                if session_id_prefix is not None:
                    log_entry["session_id_prefix"] = session_id_prefix
            except Exception:
                pass

            # Add extra fields from record.__dict__ and FLATTEN nested objects
            for key, value in record.__dict__.items():
                if key not in {
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                } and not key.startswith("_"):
                    # Flatten nested dicts (like "context") for Seq searchability
                    if isinstance(value, dict) and key == "context":
                        # Flatten context object
                        for ctx_key, ctx_value in value.items():
                            log_entry[ctx_key] = ctx_value
                    else:
                        log_entry[key] = value

            # Enqueue async
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(dispatcher.enqueue(log_entry))
            except RuntimeError:
                # No event loop, skip
                pass

        except Exception as e:
            # Fallback to console if dispatcher fails
            print(f"Failed to send log to dispatcher: {e}", flush=True)

    def _find_caller_frame(self):
        """Find the actual caller frame by walking up the stack."""
        # Skip these modules/files when finding the caller
        skip_modules = {
            "logging",
            "structlog",
            "app.core.logging.base_logger",
            "app.core.logging.logger",
            "app.core.logging.clef_logger",
            "_base",
        }

        skip_files = {
            "base_logger.py",
            "logger.py",
            "clef_logger.py",
            "_base.py",
            "logging/__init__.py",
        }

        # Get current frame
        current_frame = inspect.currentframe()

        try:
            # Walk up the stack
            frame = current_frame
            for _ in range(15):  # Limit depth
                if frame is None:
                    break

                frame = frame.f_back
                if frame is None:
                    break

                # Get module name
                module_name = frame.f_globals.get("__name__", "")
                filename = frame.f_code.co_filename
                basename = os.path.basename(filename)

                # Skip internal logging frames
                if any(skip in module_name for skip in skip_modules):
                    continue

                if basename in skip_files:
                    continue

                # Found the actual caller!
                return frame

            return None
        finally:
            # Clean up frame references
            del current_frame


def get_clef_logger(name: str) -> logging.Logger:
    """
    Get a logger configured for CLEF output.

    This bypasses structlog and uses Python's standard logging
    with our custom CLEF handler.
    """
    logger = logging.getLogger(name)
    return logger

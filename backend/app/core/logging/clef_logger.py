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
    """Get host/container metadata."""
    return {
        "host": socket.gethostname(),
        "pid": os.getpid(),
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

            # Create CLEF log entry
            log_entry = {
                "@t": datetime.fromtimestamp(record.created, tz=UTC)
                .isoformat()
                .replace("+00:00", "Z"),
                "@l": record.levelname,
                "@m": record.getMessage(),
                **self._service_metadata,
                "logger": record.name,
                "module": module,
                "function": function,
                "line": line,
                "file": filename,
                **self._host_metadata,
                "thread": record.threadName,
            }

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
                    get_request_id,
                    get_span_id,
                    get_trace_id,
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

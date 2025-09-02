"""Structured logging configuration with SEQ support and auto-logging capabilities."""

import asyncio
import logging
import sys
import inspect
from pathlib import Path
from typing import Any, Optional
from datetime import datetime

import structlog
from structlog.stdlib import LoggerFactory

# Try to import httpx for SEQ HTTP transport
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    enable_seq: bool = False,
    seq_url: str | None = None,
    seq_api_key: str | None = None,
    enable_file_logging: bool = True,
    log_directory: str = "logs",
    separate_server_logs: bool = True,
    enable_console: bool = True,
    environment: str = "development",
) -> None:
    """Configure structured logging with optional SEQ support and auto-logging."""

    # Create logs directory if it doesn't exist
    if enable_file_logging:
        log_path = Path(log_directory)
        log_path.mkdir(exist_ok=True)

    # Configure structlog processors
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add source information in development mode
    if environment == "development":
        processors.append(_add_source_info)
    
    # Add final renderer
    processors.append(
        structlog.processors.JSONRenderer()
        if log_format == "json"
        else structlog.dev.ConsoleRenderer()
    )

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure handlers
    handlers: list[logging.Handler] = []

    # Console handler (enabled by default)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(console_handler)

    # File handlers if enabled
    if enable_file_logging:
        # Application logs
        app_handler = logging.FileHandler(f"{log_directory}/app.log")
        app_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        # Error logs
        error_handler = logging.FileHandler(f"{log_directory}/error.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        handlers.extend([app_handler, error_handler])

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
    )

    # Configure Uvicorn server logs separately if enabled
    if separate_server_logs and enable_file_logging:
        # Create separate handlers for uvicorn
        uvicorn_access_handler = logging.FileHandler(
            f"{log_directory}/uvicorn_access.log"
        )
        uvicorn_access_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        uvicorn_error_handler = logging.FileHandler(
            f"{log_directory}/uvicorn_error.log"
        )
        uvicorn_error_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        # Configure uvicorn loggers
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_error_logger = logging.getLogger("uvicorn.error")

        # Add handlers to uvicorn loggers
        uvicorn_access_logger.addHandler(uvicorn_access_handler)
        uvicorn_error_logger.addHandler(uvicorn_error_handler)

        # Prevent propagation to avoid duplicate console logs
        uvicorn_access_logger.propagate = False

    # Configure SEQ logging if enabled and available
    if enable_seq and HTTPX_AVAILABLE and seq_url:
        try:
            # Create a custom handler for Seq HTTP transport
            class SeqHTTPHandler(logging.Handler):
                """Custom handler for sending logs to Seq via HTTP."""

                def __init__(self, seq_url: str, api_key: str | None = None):
                    super().__init__()
                    self.seq_url = seq_url.rstrip("/")
                    self.api_key = api_key
                    self.client = httpx.AsyncClient(timeout=5.0)

                def emit(self, record: logging.LogRecord) -> None:
                    """Emit a log record to Seq."""
                    try:
                        # Create log entry for Seq
                        log_entry = {
                            "@mt": record.getMessage(),
                            "@l": record.levelname,
                            "@t": record.created,
                            "@x": record.exc_info[2] if record.exc_info else None,
                        }

                        # Add extra fields from record
                        if hasattr(record, "structlog"):
                            log_entry.update(record.structlog)

                        # Add standard fields
                        log_entry.update({
                            "logger": record.name,
                            "level": record.levelname,
                            "timestamp": record.created,
                        })

                        # Send to Seq asynchronously
                        asyncio.create_task(self._send_to_seq(log_entry))

                    except Exception as e:
                        # Fallback to console if Seq fails
                        print(f"Failed to send log to Seq: {e}")

                async def _send_to_seq(self, log_entry: dict) -> None:
                    """Send log entry to Seq."""
                    try:
                        headers = {"Content-Type": "application/json"}
                        if self.api_key:
                            headers["X-Seq-ApiKey"] = self.api_key

                        await self.client.post(
                            f"{self.seq_url}/api/events/raw",
                            json=[log_entry],
                            headers=headers,
                        )
                    except Exception as e:
                        # Silently fail to avoid log loops
                        pass

            # Add Seq handler to root logger
            seq_handler = SeqHTTPHandler(seq_url, seq_api_key)
            seq_handler.setLevel(getattr(logging, log_level.upper()))
            logging.getLogger().addHandler(seq_handler)

            get_logger(__name__).info(f"✅ SEQ logging configured successfully at {seq_url}")
        except Exception as e:
            # Fallback to console logging if SEQ configuration fails
            get_logger(__name__).warning(f"Failed to configure SEQ logging: {e}")
    elif enable_seq and not HTTPX_AVAILABLE:
        get_logger(__name__).warning(
            "SEQ logging requested but httpx package not available"
        )


def _add_source_info(logger: Any, method_name: str, event_dict: dict) -> dict:
    """Add source information (file, module, line) to log entries in development mode."""
    try:
        # Get the caller's frame
        frame = inspect.currentframe()
        if frame:
            # Go up the call stack to find the actual caller
            for _ in range(10):  # Limit stack depth
                frame = frame.f_back
                if frame and frame.f_code.co_name != '_add_source_info':
                    break
            
            if frame:
                event_dict.update({
                    "file": frame.f_code.co_filename.split("/")[-1],  # Just filename, not full path
                    "module": frame.f_globals.get("__name__", "unknown"),
                    "function": frame.f_code.co_name,
                    "line": frame.f_lineno,
                })
    except Exception:
        # Silently fail if we can't get source info
        pass
    
    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)  # type: ignore


class LoggerMixin:
    """Mixin to add logging capabilities to classes."""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get a logger for this class."""
        return get_logger(self.__class__.__name__)


# Enhanced async logging with security event tracking
async def log_security_event(
    logger: structlog.stdlib.BoundLogger,
    event_type: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    authentication_method: Optional[str] = None,
    authorization_outcome: Optional[str] = None,
    source_ip: Optional[str] = None,
    user_agent: Optional[str] = None,
    status_code: Optional[int] = None,
    **kwargs: Any
) -> None:
    """Log a security event with comprehensive information."""
    
    # Sanitize sensitive data
    sanitized_kwargs = _sanitize_log_data(kwargs)
    
    log_entry = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "session_id": session_id[:6] if session_id else None,  # First 6 characters only
        "authentication_method": authentication_method,
        "authorization_outcome": authorization_outcome,
        "source_ip": source_ip,
        "user_agent": user_agent,
        "status_code": status_code,
        **sanitized_kwargs
    }
    
    # Remove None values
    log_entry = {k: v for k, v in log_entry.items() if v is not None}
    
    logger.info(f"Security Event: {event_type}", **log_entry)


def _sanitize_log_data(data: dict) -> dict:
    """Remove sensitive information from log data."""
    sensitive_keys = [
        'password', 'secret', 'token', 'key', 'authorization', 'cookie',
        'client_secret', 'bearer_token', 'api_key', 'private_key'
    ]
    
    sanitized = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str) and len(value) > 0:
                sanitized[key] = f"<REDACTED:{len(value)}>"
            else:
                sanitized[key] = "<REDACTED>"
        else:
            sanitized[key] = value
    
    return sanitized


# Convenience function for async logging
async def log_async(
    logger: structlog.stdlib.BoundLogger, level: str, message: str, **kwargs: Any
) -> None:
    """Log a message asynchronously."""
    log_func = getattr(logger, level.lower())
    log_func(message, **kwargs)
    # Small delay to prevent blocking
    await asyncio.sleep(0)


# Auto-logging context manager for functions
class AutoLogContext:
    """Context manager for automatic function logging."""

    def __init__(self, logger: structlog.stdlib.BoundLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time: float | None = None

    async def __aenter__(self) -> "AutoLogContext":
        import time

        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation}")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        import time

        execution_time = time.time() - self.start_time if self.start_time else 0

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}", execution_time=execution_time
            )
        else:
            self.logger.error(
                f"Failed {self.operation}: {exc_val}",
                execution_time=execution_time,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
            )

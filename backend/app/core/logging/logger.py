"""Structured logging configuration with CLEF/SEQ support and async dispatcher."""

import asyncio

# Try to import httpx for SEQ HTTP transport
import importlib.util
import inspect
import logging
import logging.handlers
from datetime import date, datetime
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

from app.core.logging.base_logger import LogFormatters

HTTPX_AVAILABLE = importlib.util.find_spec("httpx") is not None


def _resolve_log_directory(log_directory: str) -> Path:
    """Resolve log directory path relative to backend directory.

    Args:
        log_directory: Relative or absolute log directory path

    Returns:
        Resolved absolute Path to log directory
    """
    log_path = Path(log_directory)

    # If already absolute, return as is
    if log_path.is_absolute():
        return log_path

    # Get the backend directory (parent of app directory)
    # __file__ is in backend/app/core/logging/logger.py
    # So we go: logger.py -> logging/ -> core/ -> app/ -> backend/
    backend_dir = Path(__file__).parent.parent.parent.parent

    # Resolve relative to backend directory
    resolved_path = backend_dir / log_path

    return resolved_path


class DailyRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Custom file handler that rotates logs daily.

    Today's logs go to base_filename (e.g., app.log).
    Previous days' logs are renamed to base_filename_YYYY-MM-DD (e.g., app_2024-01-15.log).
    """

    def __init__(self, filename: str, log_directory: str, **kwargs):
        """Initialize daily rotating file handler.

        Args:
            filename: Base filename (e.g., 'app.log')
            log_directory: Directory where logs are stored (relative or absolute)
            **kwargs: Additional arguments for TimedRotatingFileHandler
        """
        # Resolve log directory relative to backend directory
        resolved_log_dir = _resolve_log_directory(log_directory)

        # Ensure directory exists
        resolved_log_dir.mkdir(parents=True, exist_ok=True)

        # Create full file path
        file_path = resolved_log_dir / filename

        # Initialize with daily rotation at midnight
        # Set delay=False to ensure files are created immediately, not lazily
        super().__init__(
            filename=str(file_path),
            when="midnight",
            interval=1,
            backupCount=0,  # We handle backup naming manually
            delay=False,  # Create file immediately, not on first write
            **kwargs,
        )

        self.base_filename = filename
        self.log_directory = resolved_log_dir
        self.current_date = date.today()

        # Check if existing file is from a previous day and rotate it
        self._check_and_rotate_existing_file()

        # Rotate on initialization if needed (for date change detection)
        self._rotate_if_needed()

        # Ensure file stream is open if delay is False
        # This ensures the file is created immediately, not on first write
        if not self.delay and self.stream is None:
            try:
                self.stream = self._open()
                # Verify file was created
                if Path(self.baseFilename).exists():
                    import sys

                    print(
                        f"[Logging] Created log file: {self.baseFilename}",
                        file=sys.stderr,
                    )
            except Exception as e:
                import sys

                print(
                    f"[Logging] WARNING: Failed to open log file {self.baseFilename}: {e}",
                    file=sys.stderr,
                )
                raise

    def _check_and_rotate_existing_file(self) -> None:
        """Check if existing log file is from a previous day and rotate it."""
        current_path = Path(self.baseFilename)
        if current_path.exists() and current_path.stat().st_size > 0:
            try:
                # Get file modification date
                file_mtime = date.fromtimestamp(current_path.stat().st_mtime)

                # If file is from a previous day, rename it
                if file_mtime < self.current_date:
                    base_name = current_path.stem  # e.g., 'app' from 'app.log'
                    extension = current_path.suffix  # e.g., '.log'
                    dated_filename = (
                        f"{base_name}_{file_mtime.strftime('%Y-%m-%d')}{extension}"
                    )
                    dated_path = self.log_directory / dated_filename
                    current_path.rename(dated_path)
            except Exception as e:
                # If rotation fails, log to stderr to avoid recursion
                import sys

                print(
                    f"Failed to rotate existing file {self.baseFilename}: {e}",
                    file=sys.stderr,
                )

    def _rotate_if_needed(self) -> None:
        """Check if rotation is needed and rotate if necessary."""
        current_date = date.today()

        # If date changed, rotate the old file
        if self.current_date != current_date and self.baseFilename:
            self._do_rollover()

        self.current_date = current_date

    def _do_rollover(self) -> None:
        """Perform the actual rollover (rename current file to dated name)."""
        if self.stream:
            self.stream.close()
            self.stream = None

        # Get yesterday's date for the filename
        yesterday = self.current_date
        base_name = Path(self.baseFilename).stem  # e.g., 'app' from 'app.log'
        extension = Path(self.baseFilename).suffix  # e.g., '.log'

        # Create dated filename: app_2024-01-15.log
        dated_filename = f"{base_name}_{yesterday.strftime('%Y-%m-%d')}{extension}"
        dated_path = self.log_directory / dated_filename

        # Rename current file to dated name if it exists
        current_path = Path(self.baseFilename)
        if current_path.exists() and current_path.stat().st_size > 0:
            current_path.rename(dated_path)

        # Update current date
        self.current_date = date.today()

        # Reopen the base file for today
        if not self.delay:
            self.stream = self._open()

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record, rotating if necessary."""
        # Check if we need to rotate before emitting
        if date.today() != self.current_date:
            self._rotate_if_needed()

        super().emit(record)


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    enable_seq: bool = False,
    seq_url: str | None = None,
    _seq_api_key: str | None = None,
    enable_file_logging: bool = True,
    log_directory: str = "run_time/logs",
    separate_server_logs: bool = True,
    enable_console: bool = True,
    environment: str = "development",
) -> None:
    """Configure structured logging with optional SEQ support and auto-logging."""

    # Resolve and create logs directory if it doesn't exist
    if enable_file_logging:
        resolved_log_dir = _resolve_log_directory(log_directory)
        try:
            resolved_log_dir.mkdir(parents=True, exist_ok=True)
            # Verify directory was created
            if not resolved_log_dir.exists():
                raise OSError(f"Failed to create log directory: {resolved_log_dir}")
            # Use resolved path for handlers
            log_directory = str(resolved_log_dir)
            # Debug output (can be removed in production)
            import sys

            print(
                f"[Logging] Log directory resolved to: {resolved_log_dir.resolve()}",
                file=sys.stderr,
            )
        except Exception as e:
            import sys

            print(
                f"[Logging] ERROR: Failed to create log directory {resolved_log_dir}: {e}",
                file=sys.stderr,
            )
            raise

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
        console_handler.setFormatter(LogFormatters.get_console_formatter())
        handlers.append(console_handler)

    # File handlers if enabled
    if enable_file_logging:
        # Application logs with daily rotation
        app_handler = DailyRotatingFileHandler(
            filename="app.log", log_directory=log_directory
        )
        app_handler.setFormatter(LogFormatters.get_standard_formatter())

        # Error logs with daily rotation
        error_handler = DailyRotatingFileHandler(
            filename="error.log", log_directory=log_directory
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(LogFormatters.get_standard_formatter())

        handlers.extend([app_handler, error_handler])

    # Configure standard library logging
    logging.basicConfig(
        format=LogFormatters.CONSOLE,
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
    )

    # Silence noisy third-party loggers
    # Prevent httpx and httpcore from flooding logs with connection details
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
    logging.getLogger("httpcore.http11").setLevel(logging.WARNING)

    # Configure Uvicorn server logs separately if enabled
    if separate_server_logs and enable_file_logging:
        # Create separate handlers for uvicorn with daily rotation
        uvicorn_access_handler = DailyRotatingFileHandler(
            filename="uvicorn_access.log", log_directory=log_directory
        )
        uvicorn_access_handler.setFormatter(LogFormatters.get_uvicorn_formatter())

        uvicorn_error_handler = DailyRotatingFileHandler(
            filename="uvicorn_error.log", log_directory=log_directory
        )
        uvicorn_error_handler.setFormatter(LogFormatters.get_uvicorn_formatter())

        # Configure uvicorn loggers
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_error_logger = logging.getLogger("uvicorn.error")

        # Add handlers to uvicorn loggers
        uvicorn_access_logger.addHandler(uvicorn_access_handler)
        uvicorn_error_logger.addHandler(uvicorn_error_handler)

        # Prevent propagation to avoid duplicate console logs
        uvicorn_access_logger.propagate = False

    # Configure SEQ logging with async CLEF dispatcher if enabled and available
    if enable_seq and HTTPX_AVAILABLE and seq_url:
        try:
            # Import the CLEF handler
            from app.core.logging.clef_logger import CLEFHandler

            # Note: The dispatcher will be initialized during app startup
            # This is just configuration
            # Add CLEF handler to root logger
            clef_handler = CLEFHandler()
            clef_handler.setLevel(getattr(logging, log_level.upper()))

            # Add filter to exclude HTTP request logs from httpx
            def filter_http_logs(record):
                # Exclude HTTP request logs from httpx
                if hasattr(record, "name") and "httpx" in record.name:
                    return False
                # Exclude HTTP request logs in the message
                if (
                    hasattr(record, "getMessage")
                    and "HTTP Request:" in record.getMessage()
                ):
                    return False
                return True

            clef_handler.addFilter(filter_http_logs)
            logging.getLogger().addHandler(clef_handler)

            get_logger(__name__).info(
                f"[OK] CLEF/SEQ logging configured successfully at {seq_url}"
            )
        except Exception as e:
            # Fallback to console logging if SEQ configuration fails
            get_logger(__name__).warning(f"Failed to configure CLEF/SEQ logging: {e}")
    elif enable_seq and not HTTPX_AVAILABLE:
        get_logger(__name__).warning(
            "SEQ logging requested but httpx package not available"
        )


def _add_source_info(_logger: Any, _method_name: str, event_dict: dict) -> dict:
    """Add source information (file, module, line) to log entries in development mode."""
    try:
        # Get the caller's frame
        frame = inspect.currentframe()
        if frame:
            # Go up the call stack to find the actual caller
            for _ in range(10):  # Limit stack depth
                frame = frame.f_back
                if frame and frame.f_code.co_name != "_add_source_info":
                    break

            if frame:
                event_dict.update(
                    {
                        "file": frame.f_code.co_filename.split("/")[
                            -1
                        ],  # Just filename, not full path
                        "module": frame.f_globals.get("__name__", "unknown"),
                        "function": frame.f_code.co_name,
                        "line": frame.f_lineno,
                    }
                )
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
    user_id: str | None = None,
    session_id: str | None = None,
    authentication_method: str | None = None,
    authorization_outcome: str | None = None,
    source_ip: str | None = None,
    user_agent: str | None = None,
    status_code: int | None = None,
    **kwargs: Any,
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
        **sanitized_kwargs,
    }

    # Remove None values
    log_entry = {k: v for k, v in log_entry.items() if v is not None}

    logger.info(f"Security Event: {event_type}", **log_entry)


def _sanitize_log_data(data: dict) -> dict:
    """Remove sensitive information from log data."""
    sensitive_keys = [
        "password",
        "secret",
        "token",
        "key",
        "authorization",
        "cookie",
        "client_secret",
        "bearer_token",
        "api_key",
        "private_key",
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

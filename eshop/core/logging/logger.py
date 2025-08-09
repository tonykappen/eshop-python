"""Structured logging configuration with SEQ support and auto-logging capabilities."""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory

# Try to import seqlog for SEQ logging support
try:
    import seqlog

    SEQ_AVAILABLE = True
except ImportError:
    SEQ_AVAILABLE = False


def configure_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    enable_seq: bool = False,
    seq_url: str | None = None,
    seq_api_key: str | None = None,
    enable_file_logging: bool = True,
    log_directory: str = "logs",
    separate_server_logs: bool = True,
) -> None:
    """Configure structured logging with optional SEQ support and auto-logging."""

    # Create logs directory if it doesn't exist
    if enable_file_logging:
        log_path = Path(log_directory)
        log_path.mkdir(exist_ok=True)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            (
                structlog.processors.JSONRenderer()
                if log_format == "json"
                else structlog.dev.ConsoleRenderer()
            ),
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure handlers
    handlers = []

    # Console handler
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
        uvicorn_access_handler = logging.FileHandler(f"{log_directory}/uvicorn_access.log")
        uvicorn_access_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        uvicorn_error_handler = logging.FileHandler(f"{log_directory}/uvicorn_error.log")
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
    if enable_seq and SEQ_AVAILABLE and seq_url:
        try:
            seqlog.configure_from_dict(
                {
                    "version": 1,
                    "disable_existing_loggers": False,
                    "formatters": {
                        "seq": {
                            "()": seqlog.StructuredLogFormatter,
                            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                        }
                    },
                    "handlers": {
                        "seq": {
                            "class": "seqlog.structured_logging.StructuredLogHandler",
                            "formatter": "seq",
                            "url": seq_url,
                            "api_key": seq_api_key or "",
                            "batch_size": 100,
                            "auto_flush_timeout": 1.0,
                        }
                    },
                    "loggers": {
                        "": {
                            "handlers": ["seq"],
                            "level": log_level.upper(),
                            "propagate": False,
                        }
                    },
                }
            )
        except Exception as e:
            # Fallback to console logging if SEQ configuration fails
            get_logger(__name__).warning(f"Failed to configure SEQ logging: {e}")
    elif enable_seq and not SEQ_AVAILABLE:
        get_logger(__name__).warning(
            "SEQ logging requested but seqlog package not available"
        )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)  # type: ignore


class LoggerMixin:
    """Mixin to add logging capabilities to classes."""

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get a logger for this class."""
        return get_logger(self.__class__.__name__)


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
        self.start_time = None

    async def __aenter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        import time
        execution_time = time.time() - self.start_time if self.start_time else 0

        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation}",
                execution_time=execution_time
            )
        else:
            self.logger.error(
                f"Failed {self.operation}: {exc_val}",
                execution_time=execution_time,
                error_type=exc_type.__name__,
                error_message=str(exc_val)
            )

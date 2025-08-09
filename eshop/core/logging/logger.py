"""Structured logging configuration with SEQ support."""

import asyncio
import logging
import sys
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
) -> None:
    """Configure structured logging with optional SEQ support."""

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

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

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

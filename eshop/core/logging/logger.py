"""Logging configuration with structlog."""

import asyncio
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.stdlib import LoggerFactory


def configure_logging(
    log_level: str = "INFO",
    seq_url: str = "http://localhost:5341",
    enable_console: bool = True,
    enable_seq: bool = False  # Disabled since seqlog is not available
) -> None:
    """Configure logging with structlog."""
    
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
            structlog.processors.JSONRenderer()
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
        level=getattr(logging, log_level.upper())
    )
    
    # Note: SEQ logging is disabled since seqlog package is not available
    # You can implement a custom SEQ handler if needed
    if enable_seq:
        print("Warning: SEQ logging is disabled - seqlog package not available")
    
    # Configure console logging if enabled
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin to add logging capabilities to classes."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__name__)


def log_execution_time(logger_name: str = None):
    """Decorator to log execution time of functions."""
    def decorator(func):
        logger = get_logger(logger_name or func.__module__)
        
        async def async_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    "Function executed successfully",
                    function=func.__name__,
                    execution_time_ms=execution_time * 1000
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "Function execution failed",
                    function=func.__name__,
                    execution_time_ms=execution_time * 1000,
                    error=str(e)
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    "Function executed successfully",
                    function=func.__name__,
                    execution_time_ms=execution_time * 1000
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "Function execution failed",
                    function=func.__name__,
                    execution_time_ms=execution_time * 1000,
                    error=str(e)
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator 
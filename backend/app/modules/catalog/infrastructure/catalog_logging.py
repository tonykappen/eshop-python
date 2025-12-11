"""Structured logging configuration for catalog module."""

import logging
import sys
from typing import Any, Dict

from pydantic import Field
from pydantic_settings import BaseSettings


class CatalogLoggingConfig(BaseSettings):
    """Logging configuration for catalog module."""

    # Log level
    log_level: str = Field(
        default="INFO",
        alias="CATALOG_LOG_LEVEL",
        description="Log level for catalog module"
    )
    
    # Log format
    log_format: str = Field(
        default="json",
        alias="CATALOG_LOG_FORMAT",
        description="Log format (json, text)"
    )
    
    # Log output
    log_to_console: bool = Field(
        default=True,
        alias="CATALOG_LOG_TO_CONSOLE",
        description="Log to console"
    )
    
    log_to_file: bool = Field(
        default=False,
        alias="CATALOG_LOG_TO_FILE",
        description="Log to file"
    )
    
    log_file_path: str = Field(
        default="logs/catalog.log",
        alias="CATALOG_LOG_FILE_PATH",
        description="Log file path"
    )
    
    # Structured logging
    enable_structured_logging: bool = Field(
        default=True,
        alias="CATALOG_ENABLE_STRUCTURED_LOGGING",
        description="Enable structured logging"
    )
    
    # Context logging
    include_request_id: bool = Field(
        default=True,
        alias="CATALOG_INCLUDE_REQUEST_ID",
        description="Include request ID in logs"
    )
    
    include_correlation_id: bool = Field(
        default=True,
        alias="CATALOG_INCLUDE_CORRELATION_ID",
        description="Include correlation ID in logs"
    )
    
    include_user_id: bool = Field(
        default=True,
        alias="CATALOG_INCLUDE_USER_ID",
        description="Include user ID in logs"
    )
    
    # Performance logging
    log_slow_queries: bool = Field(
        default=True,
        alias="CATALOG_LOG_SLOW_QUERIES",
        description="Log slow database queries"
    )
    
    slow_query_threshold: float = Field(
        default=1.0,
        alias="CATALOG_SLOW_QUERY_THRESHOLD",
        description="Slow query threshold in seconds"
    )
    
    # Error logging
    log_exceptions: bool = Field(
        default=True,
        alias="CATALOG_LOG_EXCEPTIONS",
        description="Log exceptions with stack traces"
    )
    
    # External logging services
    enable_seq: bool = Field(
        default=False,
        alias="CATALOG_ENABLE_SEQ",
        description="Enable Seq logging"
    )
    
    seq_url: str = Field(
        default="http://localhost:5341",
        alias="CATALOG_SEQ_URL",
        description="Seq server URL"
    )
    
    enable_datadog: bool = Field(
        default=False,
        alias="CATALOG_ENABLE_DATADOG",
        description="Enable Datadog logging"
    )
    
    datadog_api_key: str = Field(
        default="",
        alias="CATALOG_DATADOG_API_KEY",
        description="Datadog API key"
    )

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class CatalogLogger:
    """Catalog module logger with structured logging."""

    def __init__(self, config: CatalogLoggingConfig):
        """
        Initialize the catalog logger.
        
        Args:
            config: Logging configuration
        """
        self.config = config
        self.logger = logging.getLogger("catalog")
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up the logger configuration."""
        # Set log level
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add console handler
        if self.config.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            
            if self.config.log_format == "json":
                formatter = self._get_json_formatter()
            else:
                formatter = self._get_text_formatter()
            
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler
        if self.config.log_to_file:
            file_handler = logging.FileHandler(self.config.log_file_path)
            file_handler.setLevel(log_level)
            
            if self.config.log_format == "json":
                formatter = self._get_json_formatter()
            else:
                formatter = self._get_text_formatter()
            
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False

    def _get_json_formatter(self) -> logging.Formatter:
        """Get JSON formatter."""
        if self.config.enable_structured_logging:
            return StructuredJSONFormatter()
        else:
            return logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
            )

    def _get_text_formatter(self) -> logging.Formatter:
        """Get text formatter."""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def log_with_context(
        self,
        level: str,
        message: str,
        **kwargs: Any
    ) -> None:
        """
        Log message with context.
        
        Args:
            level: Log level
            message: Log message
            **kwargs: Additional context
        """
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        
        if self.config.enable_structured_logging:
            # Add context to the message
            context = {}
            
            if self.config.include_request_id and "request_id" in kwargs:
                context["request_id"] = kwargs["request_id"]
            
            if self.config.include_correlation_id and "correlation_id" in kwargs:
                context["correlation_id"] = kwargs["correlation_id"]
            
            if self.config.include_user_id and "user_id" in kwargs:
                context["user_id"] = kwargs["user_id"]
            
            # Add any additional context
            context.update(kwargs)
            
            log_method(message, extra=context)
        else:
            log_method(message)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self.log_with_context("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self.log_with_context("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self.log_with_context("error", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self.log_with_context("debug", message, **kwargs)


class StructuredJSONFormatter(logging.Formatter):
    """Structured JSON formatter for logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON formatted log message
        """
        import json
        from datetime import datetime
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process", "getMessage", "exc_info", "exc_text", "stack_info"]:
                log_entry[key] = value
        
        return json.dumps(log_entry)


# Global configuration and logger instances
catalog_logging_config = CatalogLoggingConfig()
catalog_logger = CatalogLogger(catalog_logging_config)



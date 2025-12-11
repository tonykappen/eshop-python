"""Base logging class with standardized logging methods and structures."""

import logging
from datetime import UTC, datetime
from typing import Any


class LogFormatters:
    """Standardized log formatters for consistent logging across the application."""

    # Standard formatter with timestamp, logger name, level, and message
    STANDARD = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Simplified formatter for uvicorn logs (no logger name)
    UVICORN = "%(asctime)s - %(levelname)s - %(message)s"

    # Console formatter (message only)
    CONSOLE = "%(message)s"

    @classmethod
    def get_standard_formatter(cls) -> logging.Formatter:
        """Get a standard formatter instance."""
        return logging.Formatter(cls.STANDARD)

    @classmethod
    def get_uvicorn_formatter(cls) -> logging.Formatter:
        """Get a uvicorn formatter instance."""
        return logging.Formatter(cls.UVICORN)

    @classmethod
    def get_console_formatter(cls) -> logging.Formatter:
        """Get a console formatter instance."""
        return logging.Formatter(cls.CONSOLE)


class BaseLogger:
    """Base class providing standardized logging methods and structures."""

    def __init__(self, logger_name: str):
        """Initialize the base logger."""
        # Use standard Python logger to ensure CLEF handler processes it correctly
        self.logger = logging.getLogger(logger_name)
        self._logger_name = logger_name

    def _create_log_entry(
        self, message: str, level: str = "info", **kwargs: Any
    ) -> dict[str, Any]:
        """Create a standardized log entry with common fields."""
        log_entry = {
            "message": message,
            "logger": self._logger_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "level": level.upper(),
        }

        # Add any additional context
        if kwargs:
            log_entry.update(kwargs)

        return log_entry

    def log_error_with_context(
        self,
        message: str,
        error: Exception | None = None,
        error_type: str | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log an error with structured context and error details."""
        log_entry = self._create_log_entry(message=message, level="error", **kwargs)

        if error:
            log_entry["error"] = str(error)
            log_entry["error_type"] = error_type or type(error).__name__

        if context:
            log_entry["context"] = context

        extra_data = {
            k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]
        }
        self.logger.error(
            message,
            extra=extra_data,
        )

    def log_warning_with_context(
        self, message: str, context: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Log a warning with structured context."""
        self.log_with_context(message, "warning", context, **kwargs)

    def log_with_context(
        self,
        message: str,
        level: str = "info",
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log a message with structured context and standardized format."""
        log_entry = self._create_log_entry(message=message, level=level, **kwargs)

        if context:
            log_entry["context"] = context

        extra_data = {
            k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]
        }
        log_func = getattr(self.logger, level.lower())
        log_func(
            message,
            extra=extra_data,
        )

    def log_debug_with_context(
        self, message: str, context: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Log a debug message with structured context."""
        self.log_with_context(message, "debug", context, **kwargs)

    def log_exception_detailed(
        self,
        message: str,
        exception: Exception,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log an exception with detailed error information and context."""
        log_entry = self._create_log_entry(message=message, level="error", **kwargs)

        log_entry.update(
            {
                "error": str(exception),
                "error_type": type(exception).__name__,
                "exception_class": exception.__class__.__name__,
            }
        )

        if context:
            log_entry["context"] = context

        extra_data = {
            k: v
            for k, v in log_entry.items()
            if k not in ["message", "error", "timestamp"]
        }
        self.logger.error(
            f"Exception: {message}, Error: {str(exception)}",
            extra=extra_data,
            exc_info=True,
        )

    def log_security_audit(
        self,
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
        """Log a security event for audit trail and monitoring."""
        log_entry = self._create_log_entry(
            message=f"Security Event: {event_type}", level="info", **kwargs
        )

        security_data = {
            "event_type": event_type,
            "user_id": user_id,
            "session_id": session_id,
            "authentication_method": authentication_method,
            "authorization_outcome": authorization_outcome,
            "source_ip": source_ip,
            "user_agent": user_agent,
            "status_code": status_code,
        }

        # Filter out None values
        security_data = {k: v for k, v in security_data.items() if v is not None}
        log_entry.update(security_data)

        extra_data = {
            k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]
        }
        self.logger.info(
            f"Security Event: {event_type}",
            extra=extra_data,
        )

    def log_security_event(
        self,
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
        """Log a security event (alias for log_security_audit for compatibility)."""
        self.log_security_audit(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            authentication_method=authentication_method,
            authorization_outcome=authorization_outcome,
            source_ip=source_ip,
            user_agent=user_agent,
            status_code=status_code,
            **kwargs,
        )

    def log_exception(
        self,
        message: str,
        exception: Exception | None = None,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log an exception (alias for log_exception_detailed for compatibility)."""
        if exception:
            self.log_exception_detailed(message, exception, context, **kwargs)
        else:
            self.log_error_with_context(message, context=context, **kwargs)

    def get_logger(self) -> logging.Logger:
        """Get the underlying Python logger."""
        return self.logger

    # Standard method names for easy migration
    def info(self, message: str, *args, **kwargs) -> None:
        """Standard info method for easy migration."""
        if args:
            # Handle format string style: logger.info("User %s logged in", username)
            formatted_message = message % args if args else message
            self.log_with_context(formatted_message, "info", **kwargs)
        else:
            self.log_with_context(message, "info", **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Standard error method for easy migration."""
        if args:
            # Handle format string style: logger.error("Failed: %s", error)
            formatted_message = message % args if args else message
            self.log_error_with_context(formatted_message, **kwargs)
        else:
            self.log_error_with_context(message, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Standard warning method for easy migration."""
        if args:
            # Handle format string style: logger.warning("Warning: %s", issue)
            formatted_message = message % args if args else message
            self.log_warning_with_context(formatted_message, **kwargs)
        else:
            self.log_warning_with_context(message, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Standard debug method for easy migration."""
        if args:
            # Handle format string style: logger.debug("Debug: %s", data)
            formatted_message = message % args if args else message
            self.log_debug_with_context(formatted_message, **kwargs)
        else:
            self.log_debug_with_context(message, **kwargs)

"""Base logging class with standardized logging methods and structures."""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, Optional

import structlog


class BaseLogger:
    """Base class providing standardized logging methods and structures."""

    def __init__(self, logger_name: str):
        """Initialize the base logger."""
        self.logger = structlog.get_logger(logger_name)
        self._logger_name = logger_name

    def _create_log_entry(
        self,
        message: str,
        level: str = "info",
        **kwargs: Any
    ) -> Dict[str, Any]:
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

    def log_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        error_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Log an error with standardized structure."""
        log_entry = self._create_log_entry(
            message=message,
            level="error",
            **kwargs
        )
        
        if error:
            log_entry["error"] = str(error)
            log_entry["error_type"] = error_type or type(error).__name__
            
        if context:
            log_entry["context"] = context
            
        self.logger.error(
            "Error Message: %s, Time of occurrence %s",
            message,
            log_entry["timestamp"],
            **{k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]}
        )

    def log_warning(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Log a warning with standardized structure."""
        log_entry = self._create_log_entry(
            message=message,
            level="warning",
            **kwargs
        )
        
        if context:
            log_entry["context"] = context
            
        self.logger.warning(
            "Warning: %s, Time of occurrence %s",
            message,
            log_entry["timestamp"],
            **{k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]}
        )

    def log_info(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Log an info message with standardized structure."""
        log_entry = self._create_log_entry(
            message=message,
            level="info",
            **kwargs
        )
        
        if context:
            log_entry["context"] = context
            
        self.logger.info(
            "Info: %s, Time of occurrence %s",
            message,
            log_entry["timestamp"],
            **{k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]}
        )

    def log_debug(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Log a debug message with standardized structure."""
        log_entry = self._create_log_entry(
            message=message,
            level="debug",
            **kwargs
        )
        
        if context:
            log_entry["context"] = context
            
        self.logger.debug(
            "Debug: %s, Time of occurrence %s",
            message,
            log_entry["timestamp"],
            **{k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]}
        )

    def log_exception(
        self,
        message: str,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Log an exception with standardized structure."""
        log_entry = self._create_log_entry(
            message=message,
            level="error",
            **kwargs
        )
        
        log_entry.update({
            "error": str(exception),
            "error_type": type(exception).__name__,
            "exception_class": exception.__class__.__name__,
        })
        
        if context:
            log_entry["context"] = context
            
        self.logger.error(
            "Exception: %s, Error: %s, Time of occurrence %s",
            message,
            str(exception),
            log_entry["timestamp"],
            **{k: v for k, v in log_entry.items() if k not in ["message", "error", "timestamp"]}
        )

    def log_security_event(
        self,
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
        """Log a security event with standardized structure."""
        log_entry = self._create_log_entry(
            message=f"Security Event: {event_type}",
            level="info",
            **kwargs
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
        
        self.logger.info(
            "Security Event: %s, Time of occurrence %s",
            event_type,
            log_entry["timestamp"],
            **{k: v for k, v in log_entry.items() if k not in ["message", "timestamp"]}
        )

    def get_logger(self) -> structlog.stdlib.BoundLogger:
        """Get the underlying structlog logger."""
        return self.logger

    # Standard method names for easy migration
    def info(self, message: str, *args, **kwargs) -> None:
        """Standard info method for easy migration."""
        if args:
            # Handle format string style: logger.info("User %s logged in", username)
            formatted_message = message % args if args else message
            self.log_info(formatted_message, **kwargs)
        else:
            self.log_info(message, **kwargs)

    def error(self, message: str, *args, **kwargs) -> None:
        """Standard error method for easy migration."""
        if args:
            # Handle format string style: logger.error("Failed: %s", error)
            formatted_message = message % args if args else message
            self.log_error(formatted_message, **kwargs)
        else:
            self.log_error(message, **kwargs)

    def warning(self, message: str, *args, **kwargs) -> None:
        """Standard warning method for easy migration."""
        if args:
            # Handle format string style: logger.warning("Warning: %s", issue)
            formatted_message = message % args if args else message
            self.log_warning(formatted_message, **kwargs)
        else:
            self.log_warning(message, **kwargs)

    def debug(self, message: str, *args, **kwargs) -> None:
        """Standard debug method for easy migration."""
        if args:
            # Handle format string style: logger.debug("Debug: %s", data)
            formatted_message = message % args if args else message
            self.log_debug(formatted_message, **kwargs)
        else:
            self.log_debug(message, **kwargs)

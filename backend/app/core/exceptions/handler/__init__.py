"""Exception handler package."""

from app.core.exceptions.handler.custom_exception_handler import (
    CustomExceptionHandler,
    add_exception_handlers,
)

__all__ = [
    "CustomExceptionHandler",
    "add_exception_handlers",
]

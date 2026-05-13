"""Mediator for global module interface."""

from app.module_interface.mediator.mediator import IMediator, Mediator
from app.module_interface.mediator.registration import (
    discover_and_register_handlers,
    register_handlers_from_modules,
)

__all__ = [
    "Mediator",
    "IMediator",
    "register_handlers_from_modules",
    "discover_and_register_handlers",
]

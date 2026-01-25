"""Mediator for global module interface."""

from app.module_interface.mediator.mediator import Mediator, IMediator
from app.module_interface.mediator.registration import (
    register_handlers_from_modules,
    discover_and_register_handlers,
)

__all__ = [
    "Mediator",
    "IMediator",
    "register_handlers_from_modules",
    "discover_and_register_handlers",
]













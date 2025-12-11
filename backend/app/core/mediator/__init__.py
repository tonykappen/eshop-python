"""Mediator pattern implementation with 1-1 parity to .NET MediatR."""

from app.core.application.behaviors import AuthorizationBehavior, LoggingBehavior, ValidationBehavior
from app.core.mediator.extensions import add_mediator_with_assemblies
from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import Mediator

__all__ = [
    "Mediator",
    "HandlerRegistry",
    "AuthorizationBehavior",
    "ValidationBehavior",
    "LoggingBehavior",
    "add_mediator_with_assemblies",
]

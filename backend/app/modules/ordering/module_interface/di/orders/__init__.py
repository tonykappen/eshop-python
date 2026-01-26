"""Ordering module DI."""

from .orders_providers import get_ordering_container
from .orders_wiring import (
    register_ordering_handlers_with_mediator,
    wire_ordering_dependencies,
    wire_ordering_dependencies_to_fastapi,
)

__all__ = [
    "get_ordering_container",
    "wire_ordering_dependencies",
    "wire_ordering_dependencies_to_fastapi",
    "register_ordering_handlers_with_mediator",
]

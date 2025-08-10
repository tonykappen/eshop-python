"""Extensions for mediator registration with 1-1 parity to .NET MediatRExtensions."""

import inspect
from typing import Any

from app.core.logging.logger import get_logger

from .handler_registry import HandlerRegistry
from .mediator import Mediator


def add_mediator_with_assemblies(services: Any, *assemblies: Any) -> Any:
    """
    Add mediator with assemblies - matches .NET AddMediatRWithAssemblies().

    Args:
        services: Service collection (FastAPI dependency container)
        *assemblies: Assemblies to scan for handlers

    Returns:
        Service collection with mediator registered
    """
    logger = get_logger(__name__)

    # Create handler registry
    handler_registry = HandlerRegistry()

    # Scan assemblies for handlers
    for assembly in assemblies:
        logger.debug(f"Scanning assembly {assembly.__name__} for handlers")
        _register_handlers_from_assembly(handler_registry, assembly)

    # Create mediator
    mediator = Mediator(handler_registry)

    # Register mediator as singleton
    # In FastAPI, we'll register it in the dependency injection container
    services["mediator"] = mediator
    services["handler_registry"] = handler_registry

    logger.info(
        f"Registered mediator with {len(handler_registry.get_registered_types())} handlers"
    )

    return services


def _register_handlers_from_assembly(
    handler_registry: HandlerRegistry, assembly: Any
) -> None:
    """Register all handlers from an assembly - matches .NET RegisterServicesFromAssemblies()."""
    logger = get_logger(__name__)

    try:
        # Get all classes from the assembly
        for name, obj in inspect.getmembers(assembly):
            if inspect.isclass(obj) and _is_request_handler(obj):
                # Extract request type from handler
                request_type = _extract_request_type(obj)
                if request_type:
                    handler_instance = obj()
                    handler_registry.register_handler(request_type, handler_instance)
                    logger.debug(
                        f"Registered handler {name} for request {request_type.__name__}"
                    )
    except Exception as e:
        logger.warning(f"Failed to scan assembly {assembly.__name__}: {e}")


def _is_request_handler(cls: type[Any]) -> bool:
    """Check if a class is a request handler."""
    # Check if it implements IRequestHandler or has handle method
    if not inspect.isabstract(cls) and (
        any(base.__name__ == "IRequestHandler" for base in cls.__mro__)
        or (hasattr(cls, "handle") and inspect.iscoroutinefunction(cls.handle))
    ):
        return True

    return False


def _extract_request_type(handler_class: type[Any]) -> type[Any] | None:
    """Extract the request type from a handler class."""
    # Check if handler class has __orig_bases__ and __args__ directly
    if (
        hasattr(handler_class, "__orig_bases__")
        and hasattr(handler_class, "__args__")
        and len(handler_class.__args__) > 0
    ):
        return handler_class.__args__[0]  # type: ignore

    # Check generic parameters from base classes
    if hasattr(handler_class, "__orig_bases__"):
        for base in handler_class.__orig_bases__:
            if hasattr(base, "__args__") and len(base.__args__) > 0:
                return base.__args__[0]  # type: ignore

    # Check method signature
    if hasattr(handler_class, "handle"):
        handle_method = handler_class.handle
        if inspect.iscoroutinefunction(handle_method):
            sig = inspect.signature(handle_method)
            for param_name, param in sig.parameters.items():
                if (
                    param_name == "request"
                    and param.annotation != inspect.Parameter.empty
                ):
                    return param.annotation  # type: ignore

    return None


def get_mediator(services: dict[str, Any]) -> Mediator:
    """Get mediator instance from services."""
    return services.get("mediator")  # type: ignore


def get_handler_registry(services: dict[str, Any]) -> HandlerRegistry:
    """Get handler registry instance from services."""
    return services.get("handler_registry")  # type: ignore

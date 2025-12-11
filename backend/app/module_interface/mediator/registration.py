"""Auto-discovers CQRS handlers in modules."""

from typing import Any

from app.core.mediator.handler_registry import HandlerRegistry
from app.core.mediator.mediator import Mediator
from app.core.logging.base_logger import BaseLogger

logger = BaseLogger(__name__)


def discover_and_register_handlers(
    mediator: Mediator, modules: list[str] | None = None
) -> None:
    """
    Discover and register handlers from modules.
    
    Args:
        mediator: Mediator instance
        modules: List of module names to scan (defaults to catalog)
    """
    if modules is None:
        modules = ["app.modules.catalog"]
    
    logger.info(f"Discovering handlers from modules: {modules}")
    
    # Handler discovery is typically done by each module's wiring
    # This function provides a central place to coordinate discovery
    # Individual modules should register their handlers via their module_interface
    for module_name in modules:
        logger.debug(f"Scanning module for handlers: {module_name}")


def register_handlers_from_modules(
    mediator: Mediator, module_routers: list[Any]
) -> None:
    """
    Register handlers from module routers.
    
    Args:
        mediator: Mediator instance
        module_routers: List of module router registration functions
    """
    logger.info(f"Registering handlers from {len(module_routers)} modules")
    
    # Each module router should handle its own handler registration
    # This is a coordination point
    for router_func in module_routers:
        try:
            # Module routers typically register handlers during their initialization
            logger.debug(f"Processing module router: {router_func}")
        except Exception as e:
            logger.error(f"Error registering handlers from module: {e}")


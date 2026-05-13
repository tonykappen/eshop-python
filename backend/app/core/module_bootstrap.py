"""Module bootstrap contract — each bounded context implements this to register itself."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.mediator.handler_registry import HandlerRegistry


class IModuleBootstrap(ABC):
    """Contract for bounded-context module registration.

    Core holds a registry of module bootstraps and calls each method at startup.
    Adding a new module requires only implementing this interface and registering it.
    """

    @abstractmethod
    def register_handlers(self, handler_registry: HandlerRegistry) -> None:
        """Register CQRS command/query handlers with the mediator registry."""
        ...

    @abstractmethod
    def register_event_handlers(self, dispatcher: Any) -> None:
        """Register domain-event-to-integration-event subscriptions."""
        ...

    @abstractmethod
    def register_interceptors(self) -> None:
        """Register commit interceptors (outbox, cache, audit, etc.)."""
        ...

    @abstractmethod
    def register_routes(self, app: Any) -> Any:
        """Register HTTP routes and return the router."""
        ...

    @abstractmethod
    def register_lifecycle_hooks(self, registry: "LifecycleHookRegistry") -> None:
        """Register startup/shutdown hooks for the module."""
        ...

    @abstractmethod
    def get_outbox_orm_class(self) -> type | None:
        """Return the module's outbox ORM class for outbox service binding."""
        ...

    @abstractmethod
    def get_session_maker_factory(self) -> Any:
        """Return a callable that produces an async session maker."""
        ...


class LifecycleHookRegistry:
    """Registry for module startup/shutdown hooks executed by core lifecycle runner."""

    def __init__(self) -> None:
        self._startup_hooks: list[Any] = []
        self._shutdown_hooks: list[Any] = []

    def add_startup_hook(self, hook: Any) -> None:
        self._startup_hooks.append(hook)

    def add_shutdown_hook(self, hook: Any) -> None:
        self._shutdown_hooks.append(hook)

    @property
    def startup_hooks(self) -> list[Any]:
        return list(self._startup_hooks)

    @property
    def shutdown_hooks(self) -> list[Any]:
        return list(self._shutdown_hooks)


class ModuleRegistry:
    """Central registry of all module bootstraps. Core iterates this at startup."""

    def __init__(self) -> None:
        self._modules: list[IModuleBootstrap] = []

    def register(self, module: IModuleBootstrap) -> None:
        self._modules.append(module)

    @property
    def modules(self) -> list[IModuleBootstrap]:
        return list(self._modules)


module_registry = ModuleRegistry()

"""Assembly scanning for automatic service registration using importlib, inspect, and pkgutil."""

import importlib
import inspect
from collections.abc import Callable
from pathlib import Path
from typing import Any

from dependency_injector import containers, providers

from ..logging.logger import get_logger

logger = get_logger(__name__)


class AssemblyScanner:
    """Assembly scanner for automatic service discovery and registration."""

    def __init__(self, container: containers.Container):
        self.container = container
        self.discovered_services: set[str] = set()
        self.registered_services: dict[str, Any] = {}

    def scan_package(
        self,
        package_name: str,
        base_path: str | None = None,
        recursive: bool = True,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> None:
        """Scan a package for services and register them automatically."""
        try:
            package = importlib.import_module(package_name)
            package_path = Path(package.__file__).parent if package.__file__ else None

            if package_path:
                self._scan_directory(
                    package_path,
                    package_name,
                    recursive,
                    include_patterns,
                    exclude_patterns,
                )

            logger.info(f"Scanned package: {package_name}")

        except ImportError as e:
            logger.warning(f"Could not import package {package_name}: {e}")

    def scan_directory(
        self,
        directory_path: str,
        package_name: str,
        recursive: bool = True,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> None:
        """Scan a directory for services and register them automatically."""
        path = Path(directory_path)
        if not path.exists():
            logger.warning(f"Directory does not exist: {directory_path}")
            return

        self._scan_directory(
            path, package_name, recursive, include_patterns, exclude_patterns
        )

    def _scan_directory(
        self,
        directory: Path,
        package_name: str,
        recursive: bool,
        include_patterns: list[str] | None,
        exclude_patterns: list[str] | None,
    ) -> None:
        """Scan a directory recursively for Python modules."""
        for item in directory.iterdir():
            if (
                item.is_file()
                and item.suffix == ".py"
                and not item.name.startswith("__")
            ):
                module_name = f"{package_name}.{item.stem}"
                self._scan_module(module_name)

            elif item.is_dir() and recursive and not item.name.startswith("__"):
                if self._should_include(item.name, include_patterns, exclude_patterns):
                    sub_package_name = f"{package_name}.{item.name}"
                    self._scan_directory(
                        item,
                        sub_package_name,
                        recursive,
                        include_patterns,
                        exclude_patterns,
                    )

    def _scan_module(self, module_name: str) -> None:
        """Scan a single module for services."""
        try:
            module = importlib.import_module(module_name)
            self._discover_services_in_module(module, module_name)
        except ImportError as e:
            logger.warning(f"Could not import module {module_name}: {e}")

    def _discover_services_in_module(self, module: Any, module_name: str) -> None:
        """Discover services in a module and register them."""
        for name, obj in inspect.getmembers(module):
            if self._is_service_class(obj):
                service_name = self._get_service_name(obj, name)
                self._register_service(service_name, obj, module_name)

            elif self._is_service_function(obj):
                service_name = self._get_service_name(obj, name)
                self._register_function_service(service_name, obj, module_name)

    def _is_service_class(self, obj: Any) -> bool:
        """Check if an object is a service class."""
        return (
            inspect.isclass(obj)
            and not inspect.isabstract(obj)
            and not obj.__name__.startswith("_")
            and hasattr(obj, "__module__")
            and not obj.__module__.startswith("builtins")
        )

    def _is_service_function(self, obj: Any) -> bool:
        """Check if an object is a service function."""
        return (
            inspect.isfunction(obj)
            and not obj.__name__.startswith("_")
            and hasattr(obj, "__module__")
            and not obj.__module__.startswith("builtins")
        )

    def _get_service_name(self, obj: Any, name: str) -> str:
        """Get the service name for registration."""
        # Check for custom service name annotation
        if hasattr(obj, "__service_name__"):
            return str(obj.__service_name__)  # Explicitly cast to str

        # Use class/function name as service name
        return name.lower()

    def _register_service(
        self, service_name: str, service_class: type, module_name: str
    ) -> None:
        """Register a service class in the container."""
        if service_name in self.discovered_services:
            logger.debug(f"Service {service_name} already discovered, skipping")
            return

        try:
            # Determine scope based on naming conventions
            scope = self._determine_scope(service_class, service_name)

            # Create provider
            provider = self._create_provider(service_class, scope)

            # Register in container
            setattr(self.container, service_name, provider)

            self.discovered_services.add(service_name)
            self.registered_services[service_name] = service_class

            logger.info(
                f"Registered service: {service_name} ({scope}) from {module_name}"
            )

        except Exception as e:
            logger.error(f"Failed to register service {service_name}: {e}")

    def _register_function_service(
        self, service_name: str, service_func: Callable, module_name: str
    ) -> None:
        """Register a service function in the container."""
        if service_name in self.discovered_services:
            logger.debug(f"Service {service_name} already discovered, skipping")
            return

        try:
            # Create provider for function
            provider = providers.Callable(service_func)

            # Register in container
            setattr(self.container, service_name, provider)

            self.discovered_services.add(service_name)
            self.registered_services[service_name] = service_func

            logger.info(
                f"Registered function service: {service_name} from {module_name}"
            )

        except Exception as e:
            logger.error(f"Failed to register function service {service_name}: {e}")

    def _determine_scope(self, service_class: type, service_name: str) -> str:
        """Determine the scope of a service based on naming conventions."""
        name_lower = service_name.lower()

        # Repository pattern
        if "repository" in name_lower:
            return "singleton"

        # Service pattern
        if "service" in name_lower:
            return "singleton"

        # Handler pattern
        if "handler" in name_lower:
            return "transient"

        # Default to singleton
        return "singleton"

    def _create_provider(self, service_class: type, scope: str) -> Any:
        """Create a provider for the service class."""
        if scope == "singleton":
            return providers.Singleton(service_class)
        elif scope == "transient":
            return providers.Factory(service_class)
        else:
            return providers.Singleton(service_class)

    def _should_include(
        self,
        name: str,
        include_patterns: list[str] | None,
        exclude_patterns: list[str] | None,
    ) -> bool:
        """Check if a directory should be included in scanning."""
        if exclude_patterns:
            for pattern in exclude_patterns:
                if pattern in name:
                    return False

        if include_patterns:
            return any(pattern in name for pattern in include_patterns)

        return True

    def get_registered_services(self) -> dict[str, Any]:
        """Get all registered services."""
        return self.registered_services.copy()

    def clear_registrations(self) -> None:
        """Clear all registrations."""
        self.discovered_services.clear()
        self.registered_services.clear()


# Decorators for service registration
def service(
    scope: str = "singleton", name: str | None = None
) -> Callable[[type], type]:
    """Decorator to mark a class as a service."""

    def decorator(cls: type) -> type:
        setattr(cls, "__service_scope__", scope)
        if name:
            setattr(cls, "__service_name__", name)
        return cls

    return decorator


def singleton_service(name: str | None = None) -> Callable[[type], type]:
    """Decorator to mark a class as a singleton service."""
    return service("singleton", name)


def transient_service(name: str | None = None) -> Callable[[type], type]:
    """Decorator to mark a class as a transient service."""
    return service("transient", name)


def function_service(
    name: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to mark a function as a service."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if name:
            setattr(func, "__service_name__", name)
        return func

    return decorator

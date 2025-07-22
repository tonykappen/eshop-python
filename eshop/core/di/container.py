"""Dependency injection container with assembly scanning."""

import importlib
import inspect
import os
from typing import Any, Dict, List, Optional, Type

from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide


class AssemblyScanner:
    """Scans assemblies for services and registers them automatically."""
    
    def __init__(self, container):
        self.container = container
        self.scanned_modules: List[str] = []
    
    def scan_module(self, module_name: str) -> None:
        """Scan a module for services and register them."""
        if module_name in self.scanned_modules:
            return
        
        try:
            module = importlib.import_module(module_name)
            self._scan_module_for_services(module)
            self.scanned_modules.append(module_name)
        except ImportError as e:
            print(f"Warning: Could not import module {module_name}: {e}")
    
    def scan_directory(self, directory_path: str, package_name: str) -> None:
        """Scan a directory for Python modules and register services."""
        if not os.path.exists(directory_path):
            return
        
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('__'):
                    # Convert file path to module path
                    rel_path = os.path.relpath(root, directory_path)
                    if rel_path == '.':
                        module_path = f"{package_name}.{file[:-3]}"
                    else:
                        rel_path = rel_path.replace(os.sep, '.')
                        module_path = f"{package_name}.{rel_path}.{file[:-3]}"
                    
                    self.scan_module(module_path)
    
    def _scan_module_for_services(self, module: Any) -> None:
        """Scan a module for service classes and register them."""
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj):
                # Check for service decorators or naming conventions
                if self._is_service_class(obj):
                    self._register_service(obj)
    
    def _is_service_class(self, cls: Type) -> bool:
        """Check if a class should be registered as a service."""
        # Check for service decorators
        if hasattr(cls, '__service__'):
            return True
        
        # Check naming conventions
        service_suffixes = ['Service', 'Repository', 'Handler', 'Manager']
        return any(cls.__name__.endswith(suffix) for suffix in service_suffixes)
    
    def _register_service(self, service_class: Type) -> None:
        """Register a service class in the container."""
        service_name = service_class.__name__
        
        # Determine scope based on class attributes or naming
        if hasattr(service_class, '__scope__'):
            scope = service_class.__scope__
        elif 'Repository' in service_name:
            scope = 'singleton'
        elif 'Service' in service_name:
            scope = 'singleton'
        else:
            scope = 'transient'
        
        # Register based on scope
        if scope == 'singleton':
            provider = providers.Singleton(service_class)
        elif scope == 'scoped':
            provider = providers.Factory(service_class)
        else:  # transient
            provider = providers.Factory(service_class)
        
        setattr(self.container, service_name.lower(), provider)


class Container(containers.DeclarativeContainer):
    """Main dependency injection container."""
    
    # Configuration
    config = providers.Configuration()
    
    # Core services
    assembly_scanner = providers.Singleton(AssemblyScanner, container=providers.Self())
    
    # Database
    database = providers.Singleton(lambda: None)  # Will be configured later
    
    # Cache
    cache_service = providers.Singleton(lambda: None)  # Will be configured later
    
    # Messaging
    event_publisher = providers.Singleton(lambda: None)  # Will be configured later
    outbox_processor = providers.Singleton(lambda: None)  # Will be configured later
    
    # Logging
    logger = providers.Singleton(lambda: None)  # Will be configured later


class ServiceProvider:
    """Service provider for dependency injection."""
    
    def __init__(self, container: Container):
        self.container = container
        self._scoped_services: Dict[str, Any] = {}
    
    def get_service(self, service_type: Type) -> Any:
        """Get a service from the container."""
        return self.container.providers.get(service_type.__name__)
    
    def get_scoped_service(self, service_type: Type) -> Any:
        """Get a scoped service (singleton per request)."""
        service_name = service_type.__name__
        if service_name not in self._scoped_services:
            self._scoped_services[service_name] = self.get_service(service_type)()
        return self._scoped_services[service_name]
    
    def clear_scoped_services(self) -> None:
        """Clear all scoped services (called at end of request)."""
        self._scoped_services.clear()


def inject_service(service_type: Type):
    """Decorator to inject a service dependency."""
    return inject(service_type, Provide[Container])


def scoped_service():
    """Decorator to mark a class as a scoped service."""
    def decorator(cls):
        cls.__service__ = True
        cls.__scope__ = 'scoped'
        return cls
    return decorator


def singleton_service():
    """Decorator to mark a class as a singleton service."""
    def decorator(cls):
        cls.__service__ = True
        cls.__scope__ = 'singleton'
        return cls
    return decorator 
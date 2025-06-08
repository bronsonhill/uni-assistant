from typing import Dict, Any, Type
from mongodb.connection import get_mongodb_client

class Container:
    """Dependency injection container for managing application dependencies"""
    
    def __init__(self):
        self._repositories: Dict[str, Any] = {}
        self._services: Dict[str, Any] = {}
        self._components: Dict[str, Any] = {}
        self._db_client = get_mongodb_client()

    def register_repository(self, name: str, repository_class: Type) -> None:
        """Register a repository class"""
        self._repositories[name] = repository_class

    def register_service(self, name: str, service_class: Type) -> None:
        """Register a service class"""
        self._services[name] = service_class

    def register_component(self, name: str, component_class: Type) -> None:
        """Register a UI component class"""
        self._components[name] = component_class

    def get_repository(self, name: str) -> Any:
        """Get a repository instance"""
        if name not in self._repositories:
            raise KeyError(f"Repository '{name}' not found")
        return self._repositories[name](self._db_client)

    def get_service(self, name: str) -> Any:
        """Get a service instance"""
        if name not in self._services:
            raise KeyError(f"Service '{name}' not found")
        return self._services[name]()

    def get_component(self, name: str) -> Any:
        """Get a UI component instance"""
        if name not in self._components:
            raise KeyError(f"Component '{name}' not found")
        return self._components[name]() 
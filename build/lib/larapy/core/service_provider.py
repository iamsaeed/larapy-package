"""
Service Provider base class for application bootstrapping.

Service providers are the central place of all Larapy application bootstrapping.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .application import Application


class ServiceProvider(ABC):
    """
    Base class for service providers.
    
    Service providers are the central place for registering services and
    bootstrapping application components.
    """
    
    def __init__(self, app: "Application"):
        """
        Initialize the service provider.
        
        Args:
            app: The application instance
        """
        self.app = app
        self.defer = False
    
    @abstractmethod
    def register(self) -> None:
        """
        Register services in the container.
        
        This method is called during the application bootstrapping process.
        All container bindings should be registered here.
        """
        pass
    
    def boot(self) -> None:
        """
        Bootstrap services after all providers have been registered.
        
        This method is called after all service providers have been registered.
        """
        pass
    
    def provides(self) -> list:
        """
        Get the services provided by the provider.
        
        Returns:
            List of service names provided by this provider
        """
        return []
    
    def when(self) -> list:
        """
        Get the events that trigger this service provider registration.
        
        Returns:
            List of events that should trigger this provider
        """
        return []


class DeferrableProvider(ServiceProvider):
    """
    A service provider that can be deferred until needed.
    
    Deferred providers are only loaded when one of their services
    is actually needed by the application.
    """
    
    def __init__(self, app: "Application"):
        super().__init__(app)
        self.defer = True
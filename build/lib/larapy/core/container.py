"""
Service Container implementation for dependency injection.

This module provides Laravel-like dependency injection container functionality.
"""

import inspect
from typing import Any, Dict, Type, Callable, Optional, TypeVar, Union
from threading import RLock

T = TypeVar('T')


class BindingResolutionException(Exception):
    """Exception raised when a binding cannot be resolved."""
    pass


class Container:
    """
    Service container for dependency injection.
    
    Provides singleton and transient service registration with automatic
    dependency resolution and constructor injection.
    """
    
    def __init__(self):
        self._bindings: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._aliases: Dict[str, str] = {}
        self._lock = RLock()
        
    def bind(self, abstract: str, concrete: Union[Type, Callable, str, None] = None, 
             shared: bool = False) -> None:
        """
        Register a binding in the container.
        
        Args:
            abstract: The abstract type or name
            concrete: The concrete implementation
            shared: Whether the binding should be singleton
        """
        with self._lock:
            if concrete is None:
                concrete = abstract
                
            self._bindings[abstract] = {
                'concrete': concrete,
                'shared': shared
            }
            
            # Remove existing instance if re-binding
            if abstract in self._instances:
                del self._instances[abstract]
    
    def singleton(self, abstract: str, concrete: Union[Type, Callable, str, None] = None) -> None:
        """
        Register a shared binding in the container.
        
        Args:
            abstract: The abstract type or name
            concrete: The concrete implementation
        """
        self.bind(abstract, concrete, shared=True)
    
    def instance(self, abstract: str, instance: Any) -> Any:
        """
        Register an existing instance as shared in the container.
        
        Args:
            abstract: The abstract type or name
            instance: The instance to register
            
        Returns:
            The registered instance
        """
        with self._lock:
            self._instances[abstract] = instance
            return instance
    
    def alias(self, abstract: str, alias: str) -> None:
        """
        Alias an abstract type to another name.
        
        Args:
            abstract: The abstract type
            alias: The alias name
        """
        with self._lock:
            self._aliases[alias] = abstract
    
    def make(self, abstract: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Resolve the given type from the container.
        
        Args:
            abstract: The abstract type or name to resolve
            parameters: Additional parameters for resolution
            
        Returns:
            The resolved instance
            
        Raises:
            BindingResolutionException: If the binding cannot be resolved
        """
        return self._resolve(abstract, parameters or {})
    
    def resolve(self, abstract: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Alias for make method.
        
        Args:
            abstract: The abstract type or name to resolve
            parameters: Additional parameters for resolution
            
        Returns:
            The resolved instance
        """
        return self.make(abstract, parameters)
    
    def bound(self, abstract: str) -> bool:
        """
        Determine if the given abstract type has been bound.
        
        Args:
            abstract: The abstract type to check
            
        Returns:
            True if bound, False otherwise
        """
        return (abstract in self._bindings or 
                abstract in self._instances or 
                abstract in self._aliases)
    
    def _resolve(self, abstract: str, parameters: Dict[str, Any]) -> Any:
        """
        Resolve an abstract type from the container.
        
        Args:
            abstract: The abstract type to resolve
            parameters: Parameters for resolution
            
        Returns:
            The resolved instance
        """
        with self._lock:
            # Check for alias
            abstract = self._get_alias(abstract)
            
            # Check for existing instance
            if abstract in self._instances:
                return self._instances[abstract]
            
            # Check for binding
            if abstract in self._bindings:
                return self._build(abstract, parameters)
            
            # Try to auto-resolve if it's a class
            try:
                if hasattr(abstract, '__module__') and hasattr(abstract, '__name__'):
                    return self._build_class(abstract, parameters)
                
                # Try to import and resolve as string
                if isinstance(abstract, str) and '.' in abstract:
                    parts = abstract.rsplit('.', 1)
                    module = __import__(parts[0], fromlist=[parts[1]])
                    cls = getattr(module, parts[1])
                    return self._build_class(cls, parameters)
                    
            except (ImportError, AttributeError):
                pass
            
            raise BindingResolutionException(f"Unable to resolve [{abstract}] from container")
    
    def _build(self, abstract: str, parameters: Dict[str, Any]) -> Any:
        """
        Build an instance from a binding.
        
        Args:
            abstract: The abstract type
            parameters: Parameters for building
            
        Returns:
            The built instance
        """
        binding = self._bindings[abstract]
        concrete = binding['concrete']
        
        # Build the instance
        if callable(concrete):
            if inspect.isclass(concrete):
                instance = self._build_class(concrete, parameters)
            else:
                # It's a factory function/lambda
                instance = concrete(self)
        else:
            # It's a string, resolve it
            instance = self._resolve(concrete, parameters)
        
        # Store as singleton if shared
        if binding['shared']:
            self._instances[abstract] = instance
            
        return instance
    
    def _build_class(self, cls: Type[T], parameters: Dict[str, Any]) -> T:
        """
        Build a class with dependency injection.
        
        Args:
            cls: The class to build
            parameters: Parameters for building
            
        Returns:
            The built instance
        """
        # Get constructor signature
        try:
            signature = inspect.signature(cls.__init__)
        except (ValueError, TypeError):
            # No constructor or can't inspect, try without parameters
            return cls()
        
        # Build dependencies
        dependencies = {}
        for name, param in signature.parameters.items():
            if name == 'self':
                continue
                
            # Use provided parameter if available
            if name in parameters:
                dependencies[name] = parameters[name]
                continue
            
            # Try to resolve from type annotation
            if param.annotation != inspect.Parameter.empty:
                try:
                    annotation = param.annotation
                    if hasattr(annotation, '__name__'):
                        dependencies[name] = self._resolve(annotation.__name__, {})
                    else:
                        dependencies[name] = self._resolve(str(annotation), {})
                except BindingResolutionException:
                    # Can't resolve, check if parameter has default
                    if param.default == inspect.Parameter.empty:
                        raise BindingResolutionException(
                            f"Unable to resolve parameter [{name}] for class [{cls.__name__}]"
                        )
        
        return cls(**dependencies)
    
    def _get_alias(self, abstract: str) -> str:
        """
        Get the alias for an abstract type.
        
        Args:
            abstract: The abstract type
            
        Returns:
            The resolved alias or original abstract
        """
        return self._aliases.get(abstract, abstract)
    
    def flush(self) -> None:
        """
        Flush all bindings and instances from the container.
        """
        with self._lock:
            self._bindings.clear()
            self._instances.clear()
            self._aliases.clear()
    
    def __contains__(self, abstract: str) -> bool:
        """
        Check if an abstract type is bound.
        
        Args:
            abstract: The abstract type to check
            
        Returns:
            True if bound, False otherwise
        """
        return self.bound(abstract)
    
    def __getitem__(self, abstract: str) -> Any:
        """
        Resolve an abstract type using array syntax.
        
        Args:
            abstract: The abstract type to resolve
            
        Returns:
            The resolved instance
        """
        return self.make(abstract)
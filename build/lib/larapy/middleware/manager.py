"""
Middleware manager for Larapy.

This module manages middleware registration, grouping, and execution.
"""

from typing import Dict, List, Any, Union, Callable, Optional, Type
from .middleware import Middleware, MiddlewarePipeline


class MiddlewareManager:
    """Manages middleware registration and execution."""
    
    def __init__(self):
        self.middleware: Dict[str, Union[Type[Middleware], Callable]] = {}
        self.middleware_groups: Dict[str, List[str]] = {}
        self.middleware_priorities: Dict[str, int] = {}
        self.global_middleware: List[str] = []
        self.route_middleware: Dict[str, str] = {}
        
    def register(self, name: str, middleware: Union[Type[Middleware], Callable], 
                priority: int = 0) -> None:
        """Register a middleware."""
        self.middleware[name] = middleware
        self.middleware_priorities[name] = priority
        
    def register_group(self, group_name: str, middleware_list: List[str]) -> None:
        """Register a middleware group."""
        self.middleware_groups[group_name] = middleware_list
        
    def add_global_middleware(self, middleware_name: str) -> None:
        """Add middleware to the global middleware stack."""
        if middleware_name not in self.global_middleware:
            self.global_middleware.append(middleware_name)
            
    def register_route_middleware(self, alias: str, middleware_name: str) -> None:
        """Register a route-specific middleware alias."""
        self.route_middleware[alias] = middleware_name
        
    def get_middleware(self, name: str) -> Optional[Union[Type[Middleware], Callable]]:
        """Get a middleware by name."""
        return self.middleware.get(name)
        
    def resolve_middleware(self, middleware_spec: Union[str, List[str]]) -> List[str]:
        """Resolve middleware specification to a list of middleware names."""
        if isinstance(middleware_spec, str):
            return self._resolve_single_middleware(middleware_spec)
        else:
            resolved = []
            for spec in middleware_spec:
                resolved.extend(self._resolve_single_middleware(spec))
            return resolved
            
    def _resolve_single_middleware(self, spec: str) -> List[str]:
        """Resolve a single middleware specification."""
        # Check if it's a group
        if spec in self.middleware_groups:
            return self.middleware_groups[spec]
            
        # Check if it's a route middleware alias
        if spec in self.route_middleware:
            return [self.route_middleware[spec]]
            
        # Check if it's a direct middleware name
        if spec in self.middleware:
            return [spec]
            
        # If not found, return as-is (might be resolved later)
        return [spec]
        
    def create_pipeline(self, middleware_specs: List[str] = None, 
                       include_global: bool = True) -> MiddlewarePipeline:
        """Create a middleware pipeline."""
        pipeline = MiddlewarePipeline()
        middleware_list = []
        
        # Add global middleware if requested
        if include_global:
            middleware_list.extend(self.global_middleware)
            
        # Add specified middleware
        if middleware_specs:
            for spec in middleware_specs:
                middleware_list.extend(self.resolve_middleware(spec))
                
        # Sort by priority
        middleware_list = self._sort_by_priority(middleware_list)
        
        # Resolve to actual middleware instances
        resolved_middleware = []
        for name in middleware_list:
            middleware_class = self.get_middleware(name)
            if middleware_class:
                if isinstance(middleware_class, type):
                    resolved_middleware.append(middleware_class())
                else:
                    resolved_middleware.append(middleware_class)
                    
        pipeline.through(resolved_middleware)
        return pipeline
        
    def _sort_by_priority(self, middleware_list: List[str]) -> List[str]:
        """Sort middleware by priority."""
        return sorted(
            middleware_list,
            key=lambda name: self.middleware_priorities.get(name, 0),
            reverse=True  # Higher priority first
        )
        
    def has_middleware(self, name: str) -> bool:
        """Check if a middleware is registered."""
        return name in self.middleware
        
    def has_group(self, group_name: str) -> bool:
        """Check if a middleware group is registered."""
        return group_name in self.middleware_groups
        
    def get_global_middleware(self) -> List[str]:
        """Get the list of global middleware."""
        return self.global_middleware.copy()
        
    def get_middleware_groups(self) -> Dict[str, List[str]]:
        """Get all middleware groups."""
        return self.middleware_groups.copy()
        
    def disable_middleware(self, middleware_names: Union[str, List[str]]) -> 'MiddlewareDisabler':
        """Create a middleware disabler context manager."""
        if isinstance(middleware_names, str):
            middleware_names = [middleware_names]
        return MiddlewareDisabler(self, middleware_names)


class MiddlewareDisabler:
    """Context manager for temporarily disabling middleware."""
    
    def __init__(self, manager: MiddlewareManager, middleware_names: List[str]):
        self.manager = manager
        self.middleware_names = middleware_names
        self.original_middleware = {}
        
    def __enter__(self):
        # Store original middleware and remove them temporarily
        for name in self.middleware_names:
            if name in self.manager.middleware:
                self.original_middleware[name] = self.manager.middleware[name]
                del self.manager.middleware[name]
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original middleware
        for name, middleware in self.original_middleware.items():
            self.manager.middleware[name] = middleware


class MiddlewareStack:
    """Represents a configured middleware stack."""
    
    def __init__(self, manager: MiddlewareManager, middleware_specs: List[str] = None):
        self.manager = manager
        self.middleware_specs = middleware_specs or []
        self._cached_pipeline: Optional[MiddlewarePipeline] = None
        
    def add(self, middleware_spec: str) -> 'MiddlewareStack':
        """Add middleware to the stack."""
        new_stack = MiddlewareStack(self.manager, self.middleware_specs + [middleware_spec])
        return new_stack
        
    def prepend(self, middleware_spec: str) -> 'MiddlewareStack':
        """Prepend middleware to the stack."""
        new_stack = MiddlewareStack(self.manager, [middleware_spec] + self.middleware_specs)
        return new_stack
        
    def remove(self, middleware_spec: str) -> 'MiddlewareStack':
        """Remove middleware from the stack."""
        new_specs = [spec for spec in self.middleware_specs if spec != middleware_spec]
        new_stack = MiddlewareStack(self.manager, new_specs)
        return new_stack
        
    def get_pipeline(self) -> MiddlewarePipeline:
        """Get the middleware pipeline."""
        if self._cached_pipeline is None:
            self._cached_pipeline = self.manager.create_pipeline(self.middleware_specs)
        return self._cached_pipeline
        
    async def run(self, request: Any, destination: Callable[[Any], Any]) -> Any:
        """Run the request through the middleware stack."""
        pipeline = self.get_pipeline()
        return await pipeline.run(request, destination)
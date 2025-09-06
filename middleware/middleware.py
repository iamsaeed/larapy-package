"""
Base middleware class for Larapy.

This module provides the base middleware interface and functionality.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union


class Middleware(ABC):
    """Base middleware class."""
    
    def __init__(self):
        self.parameters: Dict[str, Any] = {}
        
    @abstractmethod
    def handle(self, request: Any, next_middleware: Callable[[Any], Any], *args: Any) -> Any:
        """
        Handle the request through the middleware.
        
        Args:
            request: The incoming request
            next_middleware: The next middleware in the pipeline
            *args: Additional parameters
            
        Returns:
            The response after processing
        """
        pass
        
    def terminate(self, request: Any, response: Any) -> None:
        """
        Perform any final actions after the response is sent.
        
        Args:
            request: The original request
            response: The response that was sent
        """
        pass
        
    def set_parameter(self, key: str, value: Any) -> 'Middleware':
        """Set a parameter for the middleware."""
        self.parameters[key] = value
        return self
        
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a parameter value."""
        return self.parameters.get(key, default)


class MiddlewarePipeline:
    """Handles the execution of middleware stack."""
    
    def __init__(self):
        self.middleware_stack: List[Union[Middleware, Callable]] = []
        
    def push(self, middleware: Union[Middleware, Callable, str]) -> 'MiddlewarePipeline':
        """Add middleware to the pipeline."""
        self.middleware_stack.append(middleware)
        return self
        
    def through(self, middleware_list: List[Union[Middleware, Callable, str]]) -> 'MiddlewarePipeline':
        """Set the middleware list."""
        self.middleware_stack = middleware_list
        return self
        
    async def run(self, request: Any, destination: Callable[[Any], Any]) -> Any:
        """Run the request through the middleware pipeline."""
        if not self.middleware_stack:
            return await self._call_destination(destination, request)
            
        # Build the pipeline from the end backwards
        pipeline = destination
        
        for middleware in reversed(self.middleware_stack):
            pipeline = self._wrap_middleware(middleware, pipeline)
            
        return await self._call_pipeline(pipeline, request)
        
    def _wrap_middleware(self, middleware: Union[Middleware, Callable, str], 
                        next_handler: Callable) -> Callable:
        """Wrap middleware around the next handler."""
        def wrapper(request: Any) -> Any:
            if isinstance(middleware, str):
                # Resolve middleware from string (would integrate with container)
                resolved_middleware = self._resolve_middleware(middleware)
                return resolved_middleware.handle(request, next_handler)
            elif isinstance(middleware, Middleware):
                return middleware.handle(request, next_handler)
            else:
                # Assume it's a callable
                return middleware(request, next_handler)
                
        return wrapper
        
    def _resolve_middleware(self, middleware_name: str) -> Middleware:
        """Resolve middleware from name (placeholder for container integration)."""
        # This would integrate with the service container to resolve middleware
        raise NotImplementedError("Middleware resolution not implemented")
        
    async def _call_destination(self, destination: Callable, request: Any) -> Any:
        """Call the final destination."""
        if asyncio.iscoroutinefunction(destination):
            return await destination(request)
        else:
            return destination(request)
            
    async def _call_pipeline(self, pipeline: Callable, request: Any) -> Any:
        """Call the pipeline."""
        if asyncio.iscoroutinefunction(pipeline):
            return await pipeline(request)
        else:
            return pipeline(request)


class ConditionalMiddleware(Middleware):
    """Middleware that only executes based on conditions."""
    
    def __init__(self, condition: Callable[[Any], bool]):
        super().__init__()
        self.condition = condition
        
    def handle(self, request: Any, next_middleware: Callable[[Any], Any], *args: Any) -> Any:
        """Handle the request conditionally."""
        if self.condition(request):
            return self._handle_when_condition_met(request, next_middleware, *args)
        else:
            return next_middleware(request)
            
    def _handle_when_condition_met(self, request: Any, next_middleware: Callable[[Any], Any], *args: Any) -> Any:
        """Handle when condition is met - override in subclasses."""
        return next_middleware(request)


class ParameterizedMiddleware(Middleware):
    """Middleware that accepts parameters."""
    
    def __init__(self, *parameters: Any, **kwargs: Any):
        super().__init__()
        self.init_parameters = parameters
        self.init_kwargs = kwargs
        
    def handle(self, request: Any, next_middleware: Callable[[Any], Any], *args: Any) -> Any:
        """Handle with parameters."""
        return self._handle_with_parameters(
            request, next_middleware, 
            *(self.init_parameters + args),
            **self.init_kwargs
        )
        
    def _handle_with_parameters(self, request: Any, next_middleware: Callable[[Any], Any], 
                               *args: Any, **kwargs: Any) -> Any:
        """Handle with parameters - override in subclasses."""
        return next_middleware(request)


# Import asyncio for async handling
import asyncio
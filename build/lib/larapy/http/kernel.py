"""
HTTP Kernel for request processing and middleware handling.

This module provides the central HTTP kernel that processes requests,
handles middleware stack, and manages the request/response lifecycle.
"""

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from .request import Request
from .response import Response

if TYPE_CHECKING:
    from ..routing.router import Router

if TYPE_CHECKING:
    from ..core.application import Application


class Kernel:
    """
    HTTP Kernel for processing requests through middleware and routing.
    
    Manages the request lifecycle including middleware stack processing,
    route dispatching, and response handling.
    """
    
    def __init__(self, app: "Application", router: "Router"):
        """
        Initialize the HTTP kernel.
        
        Args:
            app: The application instance
            router: The router instance
        """
        self.app = app
        self.router = router
        self.middleware: List[str] = []
        self.route_middleware: Dict[str, str] = {}
        self.middleware_groups: Dict[str, List[str]] = {
            'web': [],
            'api': []
        }
        
        # Register default middleware
        self._register_default_middleware()
    
    def _register_default_middleware(self) -> None:
        """Register default middleware."""
        # Default middleware would be registered here
        # For now, we'll keep it empty
        pass
    
    def handle(self, request: Request) -> Response:
        """
        Handle an incoming HTTP request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The HTTP response
        """
        try:
            # Create middleware stack
            middleware_stack = self._build_middleware_stack(request)
            
            # Process through middleware and route
            response = self._process_through_stack(middleware_stack, request)
            
            return response
            
        except Exception as e:
            if "RouteNotFoundException" in str(type(e)):
                return self._handle_not_found(request)
            else:
                return self._handle_exception(request, e)
    
    def _build_middleware_stack(self, request: Request) -> List[Callable]:
        """
        Build the middleware stack for the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            List of middleware callables
        """
        middleware_stack = []
        
        # Add global middleware
        for middleware_name in self.middleware:
            middleware_stack.append(self._resolve_middleware(middleware_name))
        
        # Find route to get route-specific middleware
        route = self.router.find_route(request)
        if route:
            for middleware_name in route.middleware:
                middleware_stack.append(self._resolve_middleware(middleware_name))
        
        # Add the final handler (route dispatcher)
        middleware_stack.append(self._dispatch_to_router)
        
        return middleware_stack
    
    def _resolve_middleware(self, middleware_name: str) -> Callable:
        """
        Resolve middleware by name.
        
        Args:
            middleware_name: The middleware name
            
        Returns:
            The middleware callable
        """
        # Check if it's a middleware alias
        if middleware_name in self.route_middleware:
            middleware_class_name = self.route_middleware[middleware_name]
        else:
            middleware_class_name = middleware_name
        
        # For now, return a placeholder middleware
        # In a full implementation, this would resolve from the container
        def placeholder_middleware(request: Request, next_handler: Callable) -> Response:
            # Just pass through to next middleware
            return next_handler(request)
        
        return placeholder_middleware
    
    def _process_through_stack(self, middleware_stack: List[Callable], request: Request) -> Response:
        """
        Process request through the middleware stack.
        
        Args:
            middleware_stack: The middleware stack
            request: The HTTP request
            
        Returns:
            The HTTP response
        """
        def create_handler(index: int) -> Callable:
            def handler(req: Request) -> Response:
                if index >= len(middleware_stack):
                    # End of stack, return empty response
                    return Response("", 500)
                
                middleware = middleware_stack[index]
                next_handler = create_handler(index + 1)
                
                # Handle different middleware signatures
                try:
                    # Try middleware with next parameter
                    return middleware(req, next_handler)
                except TypeError:
                    # Try middleware without next parameter
                    return middleware(req)
            
            return handler
        
        # Start processing from the first middleware
        handler = create_handler(0)
        return handler(request)
    
    def _dispatch_to_router(self, request: Request, next_handler: Optional[Callable] = None) -> Response:
        """
        Dispatch request to the router (final handler in middleware stack).
        
        Args:
            request: The HTTP request
            next_handler: Next handler (unused for router dispatch)
            
        Returns:
            The route response
        """
        return self.router.dispatch(request)
    
    def _handle_not_found(self, request: Request) -> Response:
        """
        Handle 404 Not Found errors.
        
        Args:
            request: The HTTP request
            
        Returns:
            404 response
        """
        return Response("Not Found", 404)
    
    def _handle_exception(self, request: Request, exception: Exception) -> Response:
        """
        Handle unhandled exceptions.
        
        Args:
            request: The HTTP request
            exception: The exception that occurred
            
        Returns:
            500 error response
        """
        # In production, you'd want to log the exception
        if self.app.is_local():
            # Show detailed error in local environment
            import traceback
            error_details = traceback.format_exc()
            return Response(f"Internal Server Error\n\n{error_details}", 500)
        else:
            # Generic error message in production
            return Response("Internal Server Error", 500)
    
    def push_middleware(self, middleware: str) -> None:
        """
        Add middleware to the global middleware stack.
        
        Args:
            middleware: The middleware name or class
        """
        self.middleware.append(middleware)
    
    def prepend_middleware(self, middleware: str) -> None:
        """
        Prepend middleware to the global middleware stack.
        
        Args:
            middleware: The middleware name or class
        """
        self.middleware.insert(0, middleware)
    
    def alias_middleware(self, alias: str, middleware: str) -> None:
        """
        Alias middleware for easier reference.
        
        Args:
            alias: The middleware alias
            middleware: The middleware class name
        """
        self.route_middleware[alias] = middleware
    
    def middleware_group(self, name: str, middleware: List[str]) -> None:
        """
        Define a middleware group.
        
        Args:
            name: The group name
            middleware: List of middleware in the group
        """
        self.middleware_groups[name] = middleware
    
    def get_middleware(self) -> List[str]:
        """
        Get all registered middleware.
        
        Returns:
            List of middleware names
        """
        return self.middleware.copy()
    
    def get_route_middleware(self) -> Dict[str, str]:
        """
        Get all route middleware aliases.
        
        Returns:
            Dictionary of middleware aliases
        """
        return self.route_middleware.copy()
    
    def get_middleware_groups(self) -> Dict[str, List[str]]:
        """
        Get all middleware groups.
        
        Returns:
            Dictionary of middleware groups
        """
        return self.middleware_groups.copy()
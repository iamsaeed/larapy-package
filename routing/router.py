"""
Router implementation for HTTP method routing and route management.

This module provides Laravel-like routing with HTTP method support,
route groups, parameter constraints, and route matching.
"""

from typing import Any, Callable, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..http.request import Request
    from ..http.response import Response

from .route import Route


class RouteNotFoundException(Exception):
    """Exception raised when no route matches the request."""
    pass


class Router:
    """
    HTTP Router class providing Laravel-like routing functionality.
    
    Handles route registration, matching, and dispatching with support
    for HTTP methods, route groups, middleware, and parameter constraints.
    """
    
    def __init__(self):
        """Initialize the router."""
        self.routes: List[Route] = []
        self.named_routes: Dict[str, Route] = {}
        self.group_stack: List[Dict[str, Any]] = []
        
        # Set this router as the global router for Route class methods
        Route.set_router(self)
    
    def add_route(self, route: Route) -> Route:
        """
        Add a route to the router.
        
        Args:
            route: The route to add
            
        Returns:
            The added route
        """
        # Apply group attributes if we're in a group
        if self.group_stack:
            self._apply_group_attributes(route)
        
        self.routes.append(route)
        
        # Register named route
        if route.name:
            self.named_routes[route.name] = route
        
        return route
    
    def _apply_group_attributes(self, route: Route) -> None:
        """
        Apply current group attributes to a route.
        
        Args:
            route: The route to apply attributes to
        """
        for group in self.group_stack:
            # Apply prefix
            if 'prefix' in group:
                prefix = group['prefix'].strip('/')
                if prefix:
                    route.uri = f"{prefix}/{route.uri}"
                    # Recompile regex with new URI
                    route.regex = route._compile_route_regex()
            
            # Apply middleware
            if 'middleware' in group:
                middleware = group['middleware']
                if isinstance(middleware, str):
                    middleware = [middleware]
                route.middleware.extend(middleware)
            
            # Apply name prefix
            if 'as' in group and route.name:
                route.name = f"{group['as']}{route.name}"
    
    def get(self, uri: str, action: Union[Callable, str]) -> Route:
        """
        Register a GET route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        return self.add_route(Route(['GET'], uri, action))
    
    def post(self, uri: str, action: Union[Callable, str]) -> Route:
        """
        Register a POST route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        return self.add_route(Route(['POST'], uri, action))
    
    def put(self, uri: str, action: Union[Callable, str]) -> Route:
        """
        Register a PUT route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        return self.add_route(Route(['PUT'], uri, action))
    
    def patch(self, uri: str, action: Union[Callable, str]) -> Route:
        """
        Register a PATCH route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        return self.add_route(Route(['PATCH'], uri, action))
    
    def delete(self, uri: str, action: Union[Callable, str]) -> Route:
        """
        Register a DELETE route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        return self.add_route(Route(['DELETE'], uri, action))
    
    def options(self, uri: str, action: Union[Callable, str]) -> Route:
        """
        Register an OPTIONS route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        return self.add_route(Route(['OPTIONS'], uri, action))
    
    def any(self, uri: str, action: Union[Callable, str]) -> Route:
        """
        Register a route for all HTTP methods.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD']
        return self.add_route(Route(methods, uri, action))
    
    def match(self, methods: List[str], uri: str, action: Union[Callable, str]) -> Route:
        """
        Register a route for specific HTTP methods.
        
        Args:
            methods: List of HTTP methods
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        return self.add_route(Route(methods, uri, action))
    
    def resource(self, name: str, controller: str) -> List[Route]:
        """
        Register resourceful routes.
        
        Args:
            name: The resource name
            controller: The controller name
            
        Returns:
            List of created routes
        """
        routes = []
        
        # Index route
        routes.append(self.get(f"{name}", f"{controller}@index").name(f"{name}.index"))
        
        # Create route  
        routes.append(self.get(f"{name}/create", f"{controller}@create").name(f"{name}.create"))
        
        # Store route
        routes.append(self.post(f"{name}", f"{controller}@store").name(f"{name}.store"))
        
        # Show route
        routes.append(self.get(f"{name}/{{id}}", f"{controller}@show").name(f"{name}.show"))
        
        # Edit route
        routes.append(self.get(f"{name}/{{id}}/edit", f"{controller}@edit").name(f"{name}.edit"))
        
        # Update routes
        routes.append(self.put(f"{name}/{{id}}", f"{controller}@update").name(f"{name}.update"))
        routes.append(self.patch(f"{name}/{{id}}", f"{controller}@update"))
        
        # Destroy route
        routes.append(self.delete(f"{name}/{{id}}", f"{controller}@destroy").name(f"{name}.destroy"))
        
        return routes
    
    def group(self, attributes: Dict[str, Any], callback: Callable) -> None:
        """
        Create a route group with shared attributes.
        
        Args:
            attributes: Shared attributes (middleware, prefix, etc.)
            callback: Callback to define routes in the group
        """
        # Push group attributes to stack
        self.group_stack.append(attributes)
        
        try:
            # Execute callback to register routes
            callback()
        finally:
            # Pop group attributes from stack
            self.group_stack.pop()
    
    def find_route(self, request: "Request") -> Optional[Route]:
        """
        Find a route that matches the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            The matching route or None
        """
        for route in self.routes:
            if route.matches(request):
                return route
        
        return None
    
    def dispatch(self, request: "Request") -> "Response":
        """
        Dispatch a request to the appropriate route.
        
        Args:
            request: The HTTP request
            
        Returns:
            The route response
            
        Raises:
            RouteNotFoundException: If no route matches
        """
        route = self.find_route(request)
        
        if route is None:
            raise RouteNotFoundException(f"No route found for {request.method} {request.path}")
        
        # Bind route parameters
        route.bind(request)
        
        # TODO: Apply middleware stack here
        
        # Call the route action
        result = route.call(request)
        
        # Convert result to Response if needed
        from ..http.response import Response
        if not isinstance(result, Response):
            if isinstance(result, (str, dict, list)):
                result = Response(result)
            else:
                result = Response(str(result))
        
        return result
    
    def route(self, name: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a URL for a named route.
        
        Args:
            name: The route name
            parameters: Route parameters
            
        Returns:
            The generated URL
            
        Raises:
            KeyError: If named route doesn't exist
        """
        if name not in self.named_routes:
            raise KeyError(f"Route '{name}' not found")
        
        route = self.named_routes[name]
        uri = route.uri
        
        if parameters:
            # Replace parameters in URI
            for param, value in parameters.items():
                # Replace both {param} and {param:pattern} formats
                uri = re.sub(f'\\{{{param}(?::[^}}]+)?\\}}', str(value), uri)
        
        # Add leading slash
        return f"/{uri}"
    
    def url(self, name: str, parameters: Optional[Dict[str, Any]] = None, absolute: bool = True) -> str:
        """
        Generate an absolute URL for a named route.
        
        Args:
            name: The route name
            parameters: Route parameters
            absolute: Whether to generate absolute URL
            
        Returns:
            The generated URL
        """
        path = self.route(name, parameters)
        
        if absolute:
            # TODO: Get base URL from application config
            base_url = "http://localhost:8000"
            return f"{base_url}{path}"
        
        return path
    
    def has_route(self, name: str) -> bool:
        """
        Check if a named route exists.
        
        Args:
            name: The route name
            
        Returns:
            True if route exists, False otherwise
        """
        return name in self.named_routes
    
    def get_routes(self) -> List[Route]:
        """
        Get all registered routes.
        
        Returns:
            List of all routes
        """
        return self.routes.copy()
    
    def get_named_routes(self) -> Dict[str, Route]:
        """
        Get all named routes.
        
        Returns:
            Dictionary of named routes
        """
        return self.named_routes.copy()
    
    def clear(self) -> None:
        """Clear all routes."""
        self.routes.clear()
        self.named_routes.clear()
        self.group_stack.clear()
    
    def __len__(self) -> int:
        """Get the number of registered routes."""
        return len(self.routes)
    
    def __iter__(self):
        """Iterate over registered routes."""
        return iter(self.routes)
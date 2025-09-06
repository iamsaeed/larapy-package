"""
Route definition and parameter handling for Larapy routing system.

This module provides Laravel-like route definition with parameter binding,
route naming, middleware assignment, and route model binding.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..http.request import Request
    from ..http.response import Response


class Route:
    """
    Route definition class providing Laravel-like routing functionality.
    
    Handles route definition, parameter extraction, middleware assignment,
    and route model binding.
    """
    
    # Class-level router instance
    _router: Optional["Router"] = None
    
    def __init__(self, 
                 methods: List[str], 
                 uri: str, 
                 action: Union[Callable, str],
                 name: Optional[str] = None):
        """
        Initialize a route.
        
        Args:
            methods: HTTP methods for this route
            uri: The route URI pattern
            action: The route action (function or controller string)
            name: Optional route name
        """
        self.methods = [method.upper() for method in methods]
        self.uri = uri.strip('/')
        self.action = action
        self._name = name
        self.middleware: List[str] = []
        self.parameters: Dict[str, Any] = {}
        self.parameter_names: List[str] = []
        
        # Compile regex pattern for route matching
        self.regex: Pattern[str] = self._compile_route_regex()
        
        # Extract parameter names from URI
        self._extract_parameter_names()
    
    def name(self, route_name: str = None) -> Union["Route", Optional[str]]:
        """
        Get or set the route name.
        
        Args:
            route_name: The route name to set (optional)
            
        Returns:
            If route_name is provided, returns self for chaining.
            If route_name is None, returns the current name.
        """
        if route_name is not None:
            self._name = route_name
            return self
        return getattr(self, '_name', None)
    
    def _compile_route_regex(self) -> Pattern[str]:
        """
        Compile the route URI into a regex pattern.
        
        Returns:
            Compiled regex pattern for route matching
        """
        # Start with the original URI
        pattern = self.uri
        
        # Replace parameter patterns
        # {id} -> (?P<id>[^/]+)
        # {id:pattern} -> (?P<id>pattern)
        pattern = re.sub(
            r'\{([a-zA-Z_][a-zA-Z0-9_]*):([^}]+)\}',
            r'(?P<\1>\2)',
            pattern
        )
        
        # Replace simple parameters
        # {id} -> (?P<id>[^/]+)
        pattern = re.sub(
            r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}',
            r'(?P<\1>[^/]+)',
            pattern
        )
        
        # Anchor the pattern
        pattern = f'^{pattern}$'
        
        return re.compile(pattern)
    
    def _extract_parameter_names(self) -> None:
        """Extract parameter names from the URI."""
        # Find all parameter patterns
        parameter_pattern = r'\{([a-zA-Z_][a-zA-Z0-9_]*)(?::([^}]+))?\}'
        matches = re.findall(parameter_pattern, self.uri)
        
        self.parameter_names = [match[0] for match in matches]
    
    def matches(self, request: "Request") -> bool:
        """
        Check if the route matches the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            True if route matches, False otherwise
        """
        # Check HTTP method
        if request.method not in self.methods:
            return False
        
        # Check URI pattern
        match = self.regex.match(request.path.strip('/'))
        if not match:
            return False
        
        # Extract parameters
        self.parameters = match.groupdict()
        
        return True
    
    def bind(self, request: "Request") -> Dict[str, Any]:
        """
        Bind route parameters from the request.
        
        Args:
            request: The HTTP request
            
        Returns:
            Dictionary of bound parameters
        """
        if not self.matches(request):
            return {}
        
        return self.parameters.copy()
    
    def with_middleware(self, middleware: Union[str, List[str]]) -> "Route":
        """
        Add middleware to the route.
        
        Args:
            middleware: Middleware name(s) to add
            
        Returns:
            Self for method chaining
        """
        if isinstance(middleware, str):
            middleware = [middleware]
        
        self.middleware.extend(middleware)
        return self
    
    
    def where(self, constraints: Dict[str, str]) -> "Route":
        """
        Add parameter constraints to the route.
        
        Args:
            constraints: Dictionary of parameter constraints
            
        Returns:
            Self for method chaining
        """
        # Rebuild the URI with constraints
        new_uri = self.uri
        for param, pattern in constraints.items():
            # Replace {param} with {param:pattern}
            new_uri = re.sub(
                f'\\{{{param}\\}}',
                f'{{{param}:{pattern}}}',
                new_uri
            )
        
        self.uri = new_uri
        self.regex = self._compile_route_regex()
        return self
    
    def call(self, request: "Request") -> Any:
        """
        Call the route action.
        
        Args:
            request: The HTTP request
            
        Returns:
            The route action result
        """
        if callable(self.action):
            # Direct callable
            return self.action(request, **self.parameters)
        elif isinstance(self.action, str):
            # Controller@method string
            from ..http.response import Response
            if '@' in self.action:
                controller_name, method_name = self.action.split('@', 1)
                # TODO: Implement controller resolution
                # For now, just return a placeholder
                return Response(f"Controller: {controller_name}@{method_name}")
            else:
                # Just a controller name
                return Response(f"Controller: {self.action}")
        else:
            from ..http.response import Response
            return Response("Invalid route action")
    
    def __str__(self) -> str:
        """String representation of the route."""
        methods_str = '|'.join(self.methods)
        return f"{methods_str} /{self.uri}"
    
    def __repr__(self) -> str:
        """Developer representation of the route."""
        return f"Route({self.methods}, '{self.uri}', {self.action!r})"
    
    # Class methods for fluent route definition
    @classmethod
    def get(cls, uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register a GET route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        route = cls(['GET'], uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def post(cls, uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register a POST route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        route = cls(['POST'], uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def put(cls, uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register a PUT route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        route = cls(['PUT'], uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def patch(cls, uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register a PATCH route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        route = cls(['PATCH'], uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def delete(cls, uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register a DELETE route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        route = cls(['DELETE'], uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def options(cls, uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register an OPTIONS route.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        route = cls(['OPTIONS'], uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def any(cls, uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register a route for all HTTP methods.
        
        Args:
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        methods = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD']
        route = cls(methods, uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def match(cls, methods: List[str], uri: str, action: Union[Callable, str]) -> "Route":
        """
        Register a route for specific HTTP methods.
        
        Args:
            methods: List of HTTP methods
            uri: The route URI
            action: The route action
            
        Returns:
            The created route
        """
        route = cls(methods, uri, action)
        if cls._router:
            cls._router.add_route(route)
        return route
    
    @classmethod
    def resource(cls, name: str, controller: str) -> List["Route"]:
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
        routes.append(cls.get(f"/{name}", f"{controller}@index").name(f"{name}.index"))
        
        # Create route  
        routes.append(cls.get(f"/{name}/create", f"{controller}@create").name(f"{name}.create"))
        
        # Store route
        routes.append(cls.post(f"/{name}", f"{controller}@store").name(f"{name}.store"))
        
        # Show route
        routes.append(cls.get(f"/{name}/{{id}}", f"{controller}@show").name(f"{name}.show"))
        
        # Edit route
        routes.append(cls.get(f"/{name}/{{id}}/edit", f"{controller}@edit").name(f"{name}.edit"))
        
        # Update route
        routes.append(cls.put(f"/{name}/{{id}}", f"{controller}@update").name(f"{name}.update"))
        routes.append(cls.patch(f"/{name}/{{id}}", f"{controller}@update").name(f"{name}.update"))
        
        # Destroy route
        routes.append(cls.delete(f"/{name}/{{id}}", f"{controller}@destroy").name(f"{name}.destroy"))
        
        return routes
    
    @classmethod
    def group(cls, attributes: Dict[str, Any], callback: Callable) -> None:
        """
        Create a route group with shared attributes.
        
        Args:
            attributes: Shared attributes (middleware, prefix, etc.)
            callback: Callback to define routes in the group
        """
        if cls._router:
            cls._router.group(attributes, callback)
    
    @classmethod
    def set_router(cls, router: "Router") -> None:
        """
        Set the router instance for class methods.
        
        Args:
            router: The router instance
        """
        cls._router = router
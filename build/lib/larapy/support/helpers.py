"""
Global helper functions for Larapy applications.

This module provides Laravel-like global helper functions for common
operations like container access, configuration, routing, and more.
"""

from typing import Any, Dict, Optional, TYPE_CHECKING, Union
import threading

if TYPE_CHECKING:
    from ..core.application import Application
    from ..http.request import Request
    from ..http.response import Response
    from ..config.config import Config

# Thread-local storage for application context
_local = threading.local()


def set_application(app: "Application") -> None:
    """
    Set the global application instance.
    
    Args:
        app: The application instance
    """
    _local.app = app


def app(service: Optional[str] = None) -> Any:
    """
    Get the application instance or resolve a service from the container.
    
    Args:
        service: Optional service name to resolve
        
    Returns:
        The application instance or resolved service
    """
    if not hasattr(_local, 'app'):
        raise RuntimeError("No application instance available")
    
    application = _local.app
    
    if service is None:
        return application
    
    return application.make(service)


def config(key: Optional[str] = None, default: Any = None) -> Any:
    """
    Get configuration value using dot notation.
    
    Args:
        key: Configuration key (dot notation supported)
        default: Default value if key not found
        
    Returns:
        Configuration value or entire config if no key provided
    """
    application = app()
    
    if key is None:
        return application._config
    
    return application.get_config(key, default)


def env(key: str, default: Any = None, cast_type: Optional[type] = None) -> Any:
    """
    Get environment variable with optional type casting.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        cast_type: Type to cast the value to
        
    Returns:
        Environment variable value or default
    """
    import os
    
    value = os.getenv(key, default)
    
    if value is None or value == default:
        return default
    
    # Type casting
    if cast_type:
        try:
            if cast_type == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif cast_type == int:
                return int(value)
            elif cast_type == float:
                return float(value)
            elif cast_type == str:
                return str(value)
            else:
                return cast_type(value)
        except (ValueError, TypeError):
            return default
    
    return value


def route(name: str, parameters: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate URL for a named route.
    
    Args:
        name: Route name
        parameters: Route parameters
        
    Returns:
        Generated URL
    """
    router = app('router')  # Assuming router is bound in container
    return router.route(name, parameters)


def url(path: str, parameters: Optional[Dict[str, Any]] = None, secure: Optional[bool] = None) -> str:
    """
    Generate a URL.
    
    Args:
        path: URL path
        parameters: URL parameters
        secure: Force HTTPS
        
    Returns:
        Generated URL
    """
    # Simple implementation - in a full version this would handle base URLs properly
    if parameters:
        query_string = '&'.join(f"{k}={v}" for k, v in parameters.items())
        path = f"{path}?{query_string}"
    
    if secure:
        # In a full implementation, this would generate proper HTTPS URLs
        pass
    
    return path


def request() -> Optional["Request"]:
    """
    Get the current request instance.
    
    Returns:
        Current request instance or None
    """
    try:
        return app('request')
    except:
        return None


def response(content: Any = "", status: int = 200, headers: Optional[Dict[str, str]] = None) -> "Response":
    """
    Create a response instance.
    
    Args:
        content: Response content
        status: HTTP status code
        headers: Response headers
        
    Returns:
        Response instance
    """
    from ..http.response import Response
    return Response(content, status, headers)


def json_response(data: Any = None, status: int = 200, headers: Optional[Dict[str, str]] = None) -> "Response":
    """
    Create a JSON response.
    
    Args:
        data: Data to serialize as JSON
        status: HTTP status code
        headers: Response headers
        
    Returns:
        JSON response instance
    """
    from ..http.response import JsonResponse
    return JsonResponse(data, status, headers)


def redirect(url: str, status: int = 302, headers: Optional[Dict[str, str]] = None) -> "Response":
    """
    Create a redirect response.
    
    Args:
        url: URL to redirect to
        status: HTTP status code
        headers: Additional headers
        
    Returns:
        Redirect response
    """
    from ..http.response import RedirectResponse
    return RedirectResponse(url, status, headers)


def abort(status: int, message: str = "") -> "Response":
    """
    Abort the request with an HTTP error.
    
    Args:
        status: HTTP status code
        message: Optional error message
        
    Returns:
        Error response
    """
    from ..http.response import abort as _abort
    return _abort(status, message)


def collect(items: Any = None) -> "Collection":
    """
    Create a collection instance.
    
    Args:
        items: Items to put in collection
        
    Returns:
        Collection instance
    """
    from .collection import Collection
    return Collection(items)


def value(value: Any, *args, **kwargs) -> Any:
    """
    Return the default value of the given value.
    
    Args:
        value: The value to return or call
        *args: Arguments for callable
        **kwargs: Keyword arguments for callable
        
    Returns:
        The resolved value
    """
    if callable(value):
        return value(*args, **kwargs)
    return value


def tap(value: Any, callback: Optional[callable] = None) -> Any:
    """
    Call the given callback with the given value then return the value.
    
    Args:
        value: The value to tap
        callback: Callback to call with the value
        
    Returns:
        The original value
    """
    if callback:
        callback(value)
    return value


def with_value(value: Any, callback: callable) -> Any:
    """
    Call the given callback with the given value and return the result.
    
    Args:
        value: The value to pass to callback
        callback: The callback to call
        
    Returns:
        The callback result
    """
    return callback(value)


def optional(value: Any) -> Any:
    """
    Create an optional object that allows method calls on null values.
    
    Args:
        value: The value to wrap
        
    Returns:
        Optional wrapper or the value itself
    """
    if value is None:
        return Optional(None)
    return value


class Optional:
    """
    Optional wrapper that allows method calls on None values.
    """
    
    def __init__(self, value: Any):
        self._value = value
    
    def __getattr__(self, name: str) -> Any:
        if self._value is None:
            return self
        
        attr = getattr(self._value, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                return Optional(result)
            return wrapper
        
        return Optional(attr)
    
    def __call__(self, *args, **kwargs) -> "Optional":
        if self._value is None or not callable(self._value):
            return self
        
        result = self._value(*args, **kwargs)
        return Optional(result)
    
    def __bool__(self) -> bool:
        return self._value is not None
    
    def __str__(self) -> str:
        return str(self._value) if self._value is not None else ""
    
    def __repr__(self) -> str:
        return f"Optional({self._value!r})"
    
    def get(self, default: Any = None) -> Any:
        """Get the wrapped value or default."""
        return self._value if self._value is not None else default


def dd(*args) -> None:
    """
    Dump and die - print variables and exit.
    
    Args:
        *args: Variables to dump
    """
    import pprint
    import sys
    
    for arg in args:
        pprint.pprint(arg)
    
    sys.exit(1)


def dump(*args) -> None:
    """
    Dump variables (without exiting).
    
    Args:
        *args: Variables to dump
    """
    import pprint
    
    for arg in args:
        pprint.pprint(arg)


def info(message: str, context: Union[Dict[str, Any], None] = None) -> None:
    """
    Log an info message.
    
    Args:
        message: The message to log
        context: Additional context
    """
    # Placeholder for logging - in a full implementation this would use proper logging
    print(f"INFO: {message}")
    if context:
        print(f"Context: {context}")


def logger(name: Union[str, None] = None):
    """
    Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    import logging
    return logging.getLogger(name)


def cache(key: Union[str, None] = None):
    """
    Get cache instance or cached value.
    
    Args:
        key: Cache key
        
    Returns:
        Cache instance or cached value
    """
    # Placeholder for caching system
    # In a full implementation, this would integrate with cache drivers
    class SimpleCache:
        def __init__(self):
            self._cache = {}
        
        def get(self, key: str, default: Any = None) -> Any:
            return self._cache.get(key, default)
        
        def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
            self._cache[key] = value
        
        def forget(self, key: str) -> None:
            self._cache.pop(key, None)
        
        def flush(self) -> None:
            self._cache.clear()
    
    cache_instance = SimpleCache()
    
    if key is None:
        return cache_instance
    
    return cache_instance.get(key)
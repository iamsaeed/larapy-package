"""
CORS middleware for Larapy.

Handles Cross-Origin Resource Sharing headers.
"""

from typing import Dict, List, Union, Any, Callable
from ..middleware import Middleware


class CorsMiddleware(Middleware):
    """CORS (Cross-Origin Resource Sharing) middleware."""
    
    def __init__(self, 
                 allowed_origins: Union[List[str], str] = '*',
                 allowed_methods: List[str] = None,
                 allowed_headers: List[str] = None,
                 exposed_headers: List[str] = None,
                 allow_credentials: bool = False,
                 max_age: int = 86400):
        super().__init__()
        
        self.allowed_origins = self._normalize_origins(allowed_origins)
        self.allowed_methods = allowed_methods or [
            'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'
        ]
        self.allowed_headers = allowed_headers or [
            'Accept', 'Authorization', 'Content-Type', 'X-Requested-With'
        ]
        self.exposed_headers = exposed_headers or []
        self.allow_credentials = allow_credentials
        self.max_age = max_age
        
    def handle(self, request: Any, next_middleware: Callable[[Any], Any], *args: Any) -> Any:
        """Handle CORS headers."""
        # Get origin from request
        origin = self._get_origin(request)
        
        # Handle preflight requests
        if self._is_preflight_request(request):
            return self._handle_preflight_request(request, origin)
            
        # Process the request
        response = next_middleware(request)
        
        # Add CORS headers to response
        return self._add_cors_headers(response, origin)
        
    def _normalize_origins(self, origins: Union[List[str], str]) -> Union[List[str], str]:
        """Normalize allowed origins."""
        if origins == '*':
            return '*'
        if isinstance(origins, str):
            return [origins]
        return origins
        
    def _get_origin(self, request: Any) -> str:
        """Get the origin from the request."""
        headers = getattr(request, 'headers', {})
        return headers.get('Origin', headers.get('origin', ''))
        
    def _is_preflight_request(self, request: Any) -> bool:
        """Check if this is a preflight request."""
        method = getattr(request, 'method', '').upper()
        headers = getattr(request, 'headers', {})
        
        return (method == 'OPTIONS' and 
                'Access-Control-Request-Method' in headers)
                
    def _handle_preflight_request(self, request: Any, origin: str) -> Any:
        """Handle preflight OPTIONS request."""
        # Create a simple response (this would depend on your response class)
        response = self._create_response('')
        
        # Add preflight headers
        if self._is_origin_allowed(origin):
            self._add_origin_header(response, origin)
            response = self._add_header(response, 'Access-Control-Allow-Methods', 
                                      ', '.join(self.allowed_methods))
            response = self._add_header(response, 'Access-Control-Allow-Headers', 
                                      ', '.join(self.allowed_headers))
            response = self._add_header(response, 'Access-Control-Max-Age', str(self.max_age))
            
            if self.allow_credentials:
                response = self._add_header(response, 'Access-Control-Allow-Credentials', 'true')
                
        return response
        
    def _add_cors_headers(self, response: Any, origin: str) -> Any:
        """Add CORS headers to response."""
        if self._is_origin_allowed(origin):
            self._add_origin_header(response, origin)
            
            if self.exposed_headers:
                response = self._add_header(response, 'Access-Control-Expose-Headers', 
                                          ', '.join(self.exposed_headers))
                
            if self.allow_credentials:
                response = self._add_header(response, 'Access-Control-Allow-Credentials', 'true')
                
        return response
        
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if the origin is allowed."""
        if not origin:
            return False
            
        if self.allowed_origins == '*':
            return True
            
        return origin in self.allowed_origins
        
    def _add_origin_header(self, response: Any, origin: str) -> None:
        """Add the Access-Control-Allow-Origin header."""
        if self.allowed_origins == '*' and not self.allow_credentials:
            self._add_header(response, 'Access-Control-Allow-Origin', '*')
        else:
            self._add_header(response, 'Access-Control-Allow-Origin', origin)
            
    def _add_header(self, response: Any, name: str, value: str) -> Any:
        """Add a header to the response."""
        # This would depend on your response class structure
        if hasattr(response, 'headers'):
            response.headers[name] = value
        elif hasattr(response, 'set_header'):
            response.set_header(name, value)
        return response
        
    def _create_response(self, content: str = '', status_code: int = 200) -> Any:
        """Create a basic response (placeholder)."""
        # This would create your framework's response object
        # For now, returning a simple dict
        return {
            'content': content,
            'status_code': status_code,
            'headers': {}
        }
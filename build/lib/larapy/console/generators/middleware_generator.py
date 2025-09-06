"""
Middleware Generator

Generates middleware classes for Larapy applications.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from .base_generator import BaseGenerator


class MiddlewareGenerator(BaseGenerator):
    """Generates middleware classes."""
    
    def __init__(self):
        super().__init__()
        self._load_templates()
    
    def generate(self, name: str, **options) -> bool:
        """
        Generate a middleware class.
        
        Args:
            name: Middleware name
            **options: Generation options
            
        Returns:
            True if generation was successful
        """
        class_name = self.get_class_name(name)
        if not class_name.endswith('Middleware'):
            class_name += 'Middleware'
        
        # Determine middleware type
        middleware_type = options.get('type', 'basic')
        
        if middleware_type == 'auth':
            return self._generate_auth_middleware(class_name, **options)
        elif middleware_type == 'cors':
            return self._generate_cors_middleware(class_name, **options)
        elif middleware_type == 'rate_limit':
            return self._generate_rate_limit_middleware(class_name, **options)
        elif middleware_type == 'cache':
            return self._generate_cache_middleware(class_name, **options)
        else:
            return self._generate_basic_middleware(class_name, **options)
    
    def _generate_basic_middleware(self, class_name: str, **options) -> bool:
        """Generate a basic middleware."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'description': options.get('description', f"{class_name} for handling HTTP requests"),
            'before_logic': options.get('before_logic', '# Add before logic here\n        pass'),
            'after_logic': options.get('after_logic', '# Add after logic here\n        pass')
        }
        
        # Render template
        template_content = self.get_template('basic_middleware')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/http/middleware/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_auth_middleware(self, class_name: str, **options) -> bool:
        """Generate an authentication middleware."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'guard': options.get('guard', 'web'),
            'redirect_to': options.get('redirect_to', '/login'),
            'except_routes': self._format_except_routes(options.get('except', []))
        }
        
        # Render template
        template_content = self.get_template('auth_middleware')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/http/middleware/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_cors_middleware(self, class_name: str, **options) -> bool:
        """Generate a CORS middleware."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'allowed_origins': self._format_origins(options.get('origins', ['*'])),
            'allowed_methods': self._format_methods(options.get('methods', ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])),
            'allowed_headers': self._format_headers(options.get('headers', ['*'])),
            'max_age': options.get('max_age', 86400)
        }
        
        # Render template
        template_content = self.get_template('cors_middleware')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/http/middleware/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_rate_limit_middleware(self, class_name: str, **options) -> bool:
        """Generate a rate limiting middleware."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'max_attempts': options.get('max_attempts', 60),
            'decay_minutes': options.get('decay_minutes', 1),
            'key_generator': options.get('key_generator', 'ip')
        }
        
        # Render template
        template_content = self.get_template('rate_limit_middleware')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/http/middleware/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _generate_cache_middleware(self, class_name: str, **options) -> bool:
        """Generate a cache middleware."""
        # Set template variables
        variables = {
            'class_name': class_name,
            'cache_time': options.get('cache_time', 3600),
            'cache_key_prefix': options.get('cache_key_prefix', 'http_cache'),
            'vary_headers': self._format_headers(options.get('vary_headers', ['Accept', 'Accept-Encoding']))
        }
        
        # Render template
        template_content = self.get_template('cache_middleware')
        content = self.render_template(template_content, variables)
        
        # Write file
        file_path = f"app/http/middleware/{self.get_snake_case(class_name)}.py"
        return self.write_file(file_path, content, options.get('force', False))
    
    def _format_except_routes(self, routes: List[str]) -> str:
        """Format except routes for template."""
        if not routes:
            return "[]"
        
        formatted_routes = [f"'{route}'" for route in routes]
        return f"[{', '.join(formatted_routes)}]"
    
    def _format_origins(self, origins: List[str]) -> str:
        """Format CORS origins for template."""
        formatted_origins = [f"'{origin}'" for origin in origins]
        return f"[{', '.join(formatted_origins)}]"
    
    def _format_methods(self, methods: List[str]) -> str:
        """Format HTTP methods for template."""
        formatted_methods = [f"'{method.upper()}'" for method in methods]
        return f"[{', '.join(formatted_methods)}]"
    
    def _format_headers(self, headers: List[str]) -> str:
        """Format headers for template."""
        formatted_headers = [f"'{header}'" for header in headers]
        return f"[{', '.join(formatted_headers)}]"
    
    def _load_templates(self):
        """Load middleware templates."""
        self.templates['basic_middleware'] = '''"""
{{class_name}} HTTP Middleware

{{description}}
"""

from larapy.http.request import Request
from larapy.http.response import Response
from typing import Callable


class {{class_name}}:
    """
    {{class_name}} for processing HTTP requests.
    """
    
    def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Process request before passing to next middleware
        {{before_logic}}
        
        # Call the next middleware
        response = next_handler(request)
        
        # Process response after receiving from next middleware
        {{after_logic}}
        
        return response
'''

        self.templates['auth_middleware'] = '''"""
{{class_name}} Authentication Middleware

Ensures the request is authenticated before proceeding.
"""

from larapy.http.request import Request
from larapy.http.response import Response
from larapy.http.redirect_response import RedirectResponse
from larapy.auth.access.gate import Gate
from typing import Callable


class {{class_name}}:
    """
    {{class_name}} for authenticating HTTP requests.
    """
    
    def __init__(self):
        self.guard = '{{guard}}'
        self.redirect_to = '{{redirect_to}}'
        self.except_routes = {{except_routes}}
    
    def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Check if route is in exceptions
        if self._should_skip(request):
            return next_handler(request)
        
        # Check if user is authenticated
        if not self._is_authenticated(request):
            return self._redirect_to_login(request)
        
        return next_handler(request)
    
    def _should_skip(self, request: Request) -> bool:
        """Check if authentication should be skipped for this request."""
        current_route = request.route
        
        if current_route:
            route_name = getattr(current_route, 'name', '')
            route_path = getattr(current_route, 'path', '')
            
            return route_name in self.except_routes or route_path in self.except_routes
        
        return False
    
    def _is_authenticated(self, request: Request) -> bool:
        """Check if the user is authenticated."""
        # Get auth manager from request or app container
        auth = request.app.resolve('auth')
        
        # Check if user is authenticated using the specified guard
        return auth.guard(self.guard).check()
    
    def _redirect_to_login(self, request: Request) -> RedirectResponse:
        """Redirect user to login page."""
        # Store intended URL for after login
        session = request.session
        if session:
            session.put('url.intended', request.url)
        
        return RedirectResponse(self.redirect_to)
'''

        self.templates['cors_middleware'] = '''"""
{{class_name}} CORS Middleware

Handles Cross-Origin Resource Sharing (CORS) for HTTP requests.
"""

from larapy.http.request import Request
from larapy.http.response import Response
from typing import Callable


class {{class_name}}:
    """
    {{class_name}} for handling CORS requests.
    """
    
    def __init__(self):
        self.allowed_origins = {{allowed_origins}}
        self.allowed_methods = {{allowed_methods}}
        self.allowed_headers = {{allowed_headers}}
        self.max_age = {{max_age}}
    
    def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Handle preflight requests
        if request.method == 'OPTIONS':
            return self._handle_preflight_request(request)
        
        # Handle actual request
        response = next_handler(request)
        
        # Add CORS headers to response
        return self._add_cors_headers(request, response)
    
    def _handle_preflight_request(self, request: Request) -> Response:
        """Handle CORS preflight request."""
        response = Response('', 200)
        return self._add_cors_headers(request, response)
    
    def _add_cors_headers(self, request: Request, response: Response) -> Response:
        """Add CORS headers to response."""
        origin = request.headers.get('Origin', '')
        
        # Check if origin is allowed
        if self._is_origin_allowed(origin):
            response.headers['Access-Control-Allow-Origin'] = origin
        elif '*' in self.allowed_origins:
            response.headers['Access-Control-Allow-Origin'] = '*'
        
        # Add other CORS headers
        response.headers['Access-Control-Allow-Methods'] = ', '.join(self.allowed_methods)
        response.headers['Access-Control-Allow-Headers'] = ', '.join(self.allowed_headers)
        response.headers['Access-Control-Max-Age'] = str(self.max_age)
        
        # Allow credentials if not using wildcard origin
        if '*' not in self.allowed_origins:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if the origin is allowed."""
        if not origin:
            return False
        
        return origin in self.allowed_origins or '*' in self.allowed_origins
'''

        self.templates['rate_limit_middleware'] = '''"""
{{class_name}} Rate Limiting Middleware

Limits the rate of requests from clients.
"""

from larapy.http.request import Request
from larapy.http.response import Response
from larapy.http.json_response import JsonResponse
from typing import Callable
import time
import hashlib


class {{class_name}}:
    """
    {{class_name}} for rate limiting HTTP requests.
    """
    
    def __init__(self):
        self.max_attempts = {{max_attempts}}
        self.decay_minutes = {{decay_minutes}}
        self.key_generator = '{{key_generator}}'
        self.cache = {}  # Simple in-memory cache (use Redis in production)
    
    def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Generate rate limit key
        key = self._generate_key(request)
        
        # Check rate limit
        if self._too_many_attempts(key):
            return self._rate_limit_response(key)
        
        # Increment attempt count
        self._increment_attempts(key)
        
        # Process request
        response = next_handler(request)
        
        # Add rate limit headers
        return self._add_rate_limit_headers(response, key)
    
    def _generate_key(self, request: Request) -> str:
        """Generate rate limit key for the request."""
        if self.key_generator == 'ip':
            identifier = request.client_ip
        elif self.key_generator == 'user' and hasattr(request, 'user'):
            identifier = str(getattr(request.user, 'id', 'anonymous'))
        else:
            identifier = request.client_ip
        
        # Create a hash of the identifier
        return hashlib.md5(f"rate_limit:{identifier}".encode()).hexdigest()
    
    def _too_many_attempts(self, key: str) -> bool:
        """Check if too many attempts have been made."""
        now = int(time.time())
        window_start = now - (self.decay_minutes * 60)
        
        # Clean old entries
        if key in self.cache:
            attempts = self.cache[key]
            self.cache[key] = [timestamp for timestamp in attempts if timestamp > window_start]
            return len(self.cache[key]) >= self.max_attempts
        
        return False
    
    def _increment_attempts(self, key: str) -> None:
        """Increment the attempt count for the key."""
        now = int(time.time())
        
        if key not in self.cache:
            self.cache[key] = []
        
        self.cache[key].append(now)
    
    def _rate_limit_response(self, key: str) -> JsonResponse:
        """Return rate limit exceeded response."""
        retry_after = self._get_retry_after(key)
        
        response = JsonResponse({
            'error': 'Too many requests',
            'message': f'Rate limit exceeded. Try again in {retry_after} seconds.',
            'retry_after': retry_after
        }, status=429)
        
        response.headers['Retry-After'] = str(retry_after)
        
        return response
    
    def _get_retry_after(self, key: str) -> int:
        """Get seconds until rate limit resets."""
        if key not in self.cache or not self.cache[key]:
            return 0
        
        oldest_attempt = min(self.cache[key])
        reset_time = oldest_attempt + (self.decay_minutes * 60)
        now = int(time.time())
        
        return max(0, reset_time - now)
    
    def _add_rate_limit_headers(self, response: Response, key: str) -> Response:
        """Add rate limit headers to response."""
        remaining = max(0, self.max_attempts - len(self.cache.get(key, [])))
        retry_after = self._get_retry_after(key)
        
        response.headers['X-RateLimit-Limit'] = str(self.max_attempts)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(int(time.time()) + retry_after)
        
        return response
'''

        self.templates['cache_middleware'] = '''"""
{{class_name}} HTTP Cache Middleware

Caches HTTP responses to improve performance.
"""

from larapy.http.request import Request
from larapy.http.response import Response
from typing import Callable
import hashlib
import time


class {{class_name}}:
    """
    {{class_name}} for caching HTTP responses.
    """
    
    def __init__(self):
        self.cache_time = {{cache_time}}  # seconds
        self.cache_key_prefix = '{{cache_key_prefix}}'
        self.vary_headers = {{vary_headers}}
        self.cache = {}  # Simple in-memory cache (use Redis in production)
    
    def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Only cache GET requests
        if request.method != 'GET':
            return next_handler(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get response from cache
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            return self._prepare_cached_response(cached_response)
        
        # Process request
        response = next_handler(request)
        
        # Cache the response if it's cacheable
        if self._should_cache_response(response):
            self._cache_response(cache_key, response)
        
        # Add cache headers
        return self._add_cache_headers(response)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for the request."""
        # Base key components
        key_parts = [
            self.cache_key_prefix,
            request.method,
            request.path,
            request.query_string or ''
        ]
        
        # Add vary headers to key
        for header_name in self.vary_headers:
            header_value = request.headers.get(header_name, '')
            key_parts.append(f"{header_name}:{header_value}")
        
        # Create hash
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str):
        """Get cached response if it exists and is not expired."""
        if cache_key not in self.cache:
            return None
        
        cached_data = self.cache[cache_key]
        
        # Check if expired
        if time.time() > cached_data['expires_at']:
            del self.cache[cache_key]
            return None
        
        return cached_data
    
    def _prepare_cached_response(self, cached_data: dict) -> Response:
        """Prepare cached response for return."""
        response = Response(
            content=cached_data['content'],
            status=cached_data['status'],
            headers=cached_data['headers'].copy()
        )
        
        # Add cache hit header
        response.headers['X-Cache'] = 'HIT'
        
        return response
    
    def _should_cache_response(self, response: Response) -> bool:
        """Check if response should be cached."""
        # Only cache successful responses
        if response.status_code != 200:
            return False
        
        # Don't cache responses with certain headers
        no_cache_headers = ['Set-Cookie', 'Authorization']
        for header in no_cache_headers:
            if header in response.headers:
                return False
        
        # Check Cache-Control header
        cache_control = response.headers.get('Cache-Control', '')
        if 'no-cache' in cache_control or 'no-store' in cache_control:
            return False
        
        return True
    
    def _cache_response(self, cache_key: str, response: Response) -> None:
        """Cache the response."""
        expires_at = time.time() + self.cache_time
        
        self.cache[cache_key] = {
            'content': response.content,
            'status': response.status_code,
            'headers': dict(response.headers),
            'expires_at': expires_at
        }
    
    def _add_cache_headers(self, response: Response) -> Response:
        """Add cache-related headers to response."""
        response.headers['X-Cache'] = 'MISS'
        response.headers['Cache-Control'] = f'public, max-age={self.cache_time}'
        
        # Add Vary header
        if self.vary_headers:
            response.headers['Vary'] = ', '.join(self.vary_headers)
        
        return response
'''
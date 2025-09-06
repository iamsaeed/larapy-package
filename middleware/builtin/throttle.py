"""
Request throttling middleware for rate limiting.

This middleware provides rate limiting functionality to protect against
abuse and ensure fair usage of resources.
"""

import time
from typing import Dict, Any, Optional, Callable
from ..middleware import Middleware
from ...http.request import Request
from ...http.response import Response, JsonResponse


class RequestThrottleMiddleware(Middleware):
    """Rate limiting middleware based on requests per time window."""
    
    def __init__(self, max_requests: int = 60, time_window: int = 60, 
                 key_func: Optional[Callable] = None):
        """
        Initialize throttling middleware.
        
        Args:
            max_requests: Maximum requests allowed per time window
            time_window: Time window in seconds
            key_func: Function to generate throttling key from request
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.key_func = key_func or self._default_key_func
        self.request_log: Dict[str, list] = {}
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request with rate limiting.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Generate throttling key
        key = self.key_func(request)
        
        # Clean old entries and check rate limit
        if self._is_rate_limited(key):
            return self._rate_limit_response(request, key)
        
        # Record the request
        self._record_request(key)
        
        # Proceed to next middleware
        response = await next_handler(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(key)
        reset_time = self._get_reset_time(key)
        
        if hasattr(response, 'header'):
            response.header('X-RateLimit-Limit', str(self.max_requests))
            response.header('X-RateLimit-Remaining', str(remaining))
            response.header('X-RateLimit-Reset', str(reset_time))
        
        return response
    
    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP."""
        return f"throttle:{request.ip}:{request.path}"
    
    def _is_rate_limited(self, key: str) -> bool:
        """Check if the key is rate limited."""
        self._clean_old_requests(key)
        
        if key not in self.request_log:
            return False
            
        return len(self.request_log[key]) >= self.max_requests
    
    def _record_request(self, key: str):
        """Record a request for the given key."""
        now = time.time()
        
        if key not in self.request_log:
            self.request_log[key] = []
        
        self.request_log[key].append(now)
    
    def _clean_old_requests(self, key: str):
        """Remove requests outside the time window."""
        if key not in self.request_log:
            return
        
        cutoff = time.time() - self.time_window
        self.request_log[key] = [
            timestamp for timestamp in self.request_log[key] 
            if timestamp > cutoff
        ]
    
    def _get_remaining_requests(self, key: str) -> int:
        """Get remaining requests for the key."""
        self._clean_old_requests(key)
        
        if key not in self.request_log:
            return self.max_requests
        
        return max(0, self.max_requests - len(self.request_log[key]))
    
    def _get_reset_time(self, key: str) -> int:
        """Get the time when the rate limit resets."""
        if key not in self.request_log or not self.request_log[key]:
            return int(time.time() + self.time_window)
        
        oldest_request = min(self.request_log[key])
        return int(oldest_request + self.time_window)
    
    def _rate_limit_response(self, request: Request, key: str) -> Response:
        """Create rate limit exceeded response."""
        retry_after = self._get_reset_time(key) - int(time.time())
        
        # Return JSON for API requests
        accept_header = request.header('accept', '')
        if 'application/json' in accept_header or request.is_ajax():
            response = JsonResponse({
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Try again in {retry_after} seconds.',
                'retry_after': retry_after
            }, status=429)
        else:
            # Return HTML for browser requests
            response = Response(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rate Limited</title>
                <style>
                    body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                    .error {{ color: #e74c3c; }}
                </style>
            </head>
            <body>
                <h1 class="error">Rate Limit Exceeded</h1>
                <p>Too many requests. Please try again in {retry_after} seconds.</p>
            </body>
            </html>
            """, status=429)
        
        if hasattr(response, 'header'):
            response.header('Retry-After', str(retry_after))
            response.header('X-RateLimit-Limit', str(self.max_requests))
            response.header('X-RateLimit-Remaining', '0')
            response.header('X-RateLimit-Reset', str(self._get_reset_time(key)))
        
        return response


class IPBasedThrottleMiddleware(RequestThrottleMiddleware):
    """IP-based throttling middleware."""
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        super().__init__(max_requests, time_window, self._ip_key_func)
    
    def _ip_key_func(self, request: Request) -> str:
        """Generate key based on IP address."""
        return f"ip_throttle:{request.ip}"


class UserThrottleMiddleware(RequestThrottleMiddleware):
    """User-based throttling middleware (requires authentication)."""
    
    def __init__(self, max_requests: int = 1000, time_window: int = 3600):
        super().__init__(max_requests, time_window, self._user_key_func)
    
    def _user_key_func(self, request: Request) -> str:
        """Generate key based on authenticated user."""
        if hasattr(request, 'user') and request.user:
            return f"user_throttle:{request.user.id}"
        else:
            # Fall back to IP-based throttling for unauthenticated users
            return f"guest_throttle:{request.ip}"
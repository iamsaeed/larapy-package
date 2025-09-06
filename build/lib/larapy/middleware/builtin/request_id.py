"""
Request ID middleware for request tracking and debugging.

This middleware adds unique request IDs to each request for easier
logging, debugging, and distributed tracing.
"""

import uuid
import time
from typing import Callable, Optional
from ..middleware import Middleware
from ...http.request import Request
from ...http.response import Response


class RequestIdMiddleware(Middleware):
    """Middleware to add unique request IDs."""
    
    def __init__(self, header_name: str = 'X-Request-ID', 
                 request_attr: str = 'request_id',
                 generator: Optional[Callable] = None):
        """
        Initialize request ID middleware.
        
        Args:
            header_name: Name of the header to add request ID
            request_attr: Name of the request attribute to store ID
            generator: Custom function to generate request IDs
        """
        self.header_name = header_name
        self.request_attr = request_attr
        self.generator = generator or self._default_generator
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Add request ID to request and response.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response with request ID header
        """
        # Check if request already has an ID (from client)
        request_id = request.header(self.header_name)
        
        # Generate new ID if not provided or invalid
        if not request_id or not self._is_valid_request_id(request_id):
            request_id = self.generator()
        
        # Store request ID in request object
        setattr(request, self.request_attr, request_id)
        
        # Process request
        response = await next_handler(request)
        
        # Add request ID to response headers
        if hasattr(response, 'header'):
            response.header(self.header_name, request_id)
        
        return response
    
    def _default_generator(self) -> str:
        """Default request ID generator using UUID4."""
        return str(uuid.uuid4())
    
    def _is_valid_request_id(self, request_id: str) -> bool:
        """Validate request ID format."""
        # Basic validation - not empty and reasonable length
        return bool(request_id) and len(request_id) <= 128


class CorrelationIdMiddleware(Middleware):
    """Middleware for correlation IDs in distributed systems."""
    
    def __init__(self, correlation_header: str = 'X-Correlation-ID',
                 request_header: str = 'X-Request-ID',
                 trace_header: str = 'X-Trace-ID'):
        """
        Initialize correlation ID middleware.
        
        Args:
            correlation_header: Header name for correlation ID
            request_header: Header name for request ID
            trace_header: Header name for trace ID
        """
        self.correlation_header = correlation_header
        self.request_header = request_header
        self.trace_header = trace_header
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """Add correlation and tracing IDs."""
        # Generate or extract correlation ID
        correlation_id = (request.header(self.correlation_header) or 
                         str(uuid.uuid4()))
        
        # Generate or extract trace ID
        trace_id = (request.header(self.trace_header) or 
                   str(uuid.uuid4()))
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Store IDs in request
        request.correlation_id = correlation_id
        request.trace_id = trace_id
        request.request_id = request_id
        
        # Process request
        response = await next_handler(request)
        
        # Add IDs to response headers
        if hasattr(response, 'header'):
            response.header(self.correlation_header, correlation_id)
            response.header(self.trace_header, trace_id)
            response.header(self.request_header, request_id)
        
        return response


class TimestampMiddleware(Middleware):
    """Middleware to add request timestamps."""
    
    def __init__(self, start_header: str = 'X-Request-Start',
                 duration_header: str = 'X-Response-Time'):
        """
        Initialize timestamp middleware.
        
        Args:
            start_header: Header for request start time
            duration_header: Header for request duration
        """
        self.start_header = start_header
        self.duration_header = duration_header
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """Add timing information to request/response."""
        # Record start time
        start_time = time.time()
        start_timestamp = int(start_time * 1000)  # milliseconds
        
        # Store start time in request
        request.start_time = start_time
        request.start_timestamp = start_timestamp
        
        # Process request
        response = await next_handler(request)
        
        # Calculate duration
        end_time = time.time()
        duration_ms = int((end_time - start_time) * 1000)
        
        # Add timing headers
        if hasattr(response, 'header'):
            response.header(self.start_header, str(start_timestamp))
            response.header(self.duration_header, f"{duration_ms}ms")
        
        return response


class RequestLoggingMiddleware(Middleware):
    """Middleware for structured request logging."""
    
    def __init__(self, logger=None, log_body: bool = False, 
                 log_headers: bool = True):
        """
        Initialize request logging middleware.
        
        Args:
            logger: Logger instance to use
            log_body: Whether to log request/response bodies
            log_headers: Whether to log headers
        """
        self.logger = logger
        self.log_body = log_body
        self.log_headers = log_headers
        
        if not self.logger:
            import logging
            self.logger = logging.getLogger('larapy.requests')
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """Log request and response details."""
        # Prepare request log data
        request_data = {
            'method': request.method,
            'path': request.path,
            'query': dict(request.query_params) if request.query_params else {},
            'ip': getattr(request, 'ip', 'unknown'),
            'user_agent': request.header('user-agent', 'unknown'),
            'request_id': getattr(request, 'request_id', None)
        }
        
        if self.log_headers:
            request_data['headers'] = dict(request.headers)
        
        if self.log_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = await request.body()
                if body:
                    request_data['body'] = body.decode('utf-8')[:1000]  # Limit size
            except Exception:
                request_data['body'] = '[Error reading body]'
        
        # Log request
        self.logger.info('Request started', extra=request_data)
        
        # Process request and measure time
        start_time = time.time()
        try:
            response = await next_handler(request)
            
            # Log successful response
            duration = int((time.time() - start_time) * 1000)
            self.logger.info('Request completed', extra={
                'request_id': getattr(request, 'request_id', None),
                'status_code': response.status_code,
                'duration_ms': duration
            })
            
            return response
            
        except Exception as e:
            # Log error response
            duration = int((time.time() - start_time) * 1000)
            self.logger.error('Request failed', extra={
                'request_id': getattr(request, 'request_id', None),
                'error': str(e),
                'error_type': type(e).__name__,
                'duration_ms': duration
            })
            raise
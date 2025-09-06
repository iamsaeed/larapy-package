"""
JSON response middleware for API consistency.

This middleware ensures consistent JSON response format and handles
automatic JSON serialization for API endpoints.
"""

import json
from typing import Any, Callable, Dict, Optional
from ..middleware import Middleware
from ...http.request import Request
from ...http.response import Response, JsonResponse


class JsonResponseMiddleware(Middleware):
    """Middleware to enforce JSON responses for API routes."""
    
    def __init__(self, force_json: bool = False, pretty_print: bool = False):
        """
        Initialize JSON response middleware.
        
        Args:
            force_json: Force all responses to be JSON
            pretty_print: Pretty print JSON responses
        """
        self.force_json = force_json
        self.pretty_print = pretty_print
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """
        Handle the incoming request and ensure JSON response.
        
        Args:
            request: The HTTP request
            next_handler: The next middleware in the stack
            
        Returns:
            HTTP response
        """
        # Get response from next middleware
        response = await next_handler(request)
        
        # Check if we should convert to JSON
        if self._should_convert_to_json(request, response):
            return self._convert_to_json_response(response)
        
        return response
    
    def _should_convert_to_json(self, request: Request, response: Response) -> bool:
        """Determine if response should be converted to JSON."""
        # Always convert if force_json is enabled
        if self.force_json:
            return True
        
        # Convert if request expects JSON
        accept_header = request.header('accept', '')
        if 'application/json' in accept_header:
            return True
        
        # Convert for AJAX requests
        if request.is_ajax():
            return True
        
        # Convert for API routes (check if path starts with /api)
        if request.path.startswith('/api'):
            return True
        
        # Don't convert if response is already JSON
        if isinstance(response, JsonResponse):
            return False
        
        # Don't convert if response has JSON content type
        content_type = response.headers.get('content-type', '')
        if 'application/json' in content_type:
            return False
        
        return False
    
    def _convert_to_json_response(self, response: Response) -> JsonResponse:
        """Convert response to JSON format."""
        # If it's already a JsonResponse, just update formatting
        if isinstance(response, JsonResponse):
            if self.pretty_print:
                response.indent = 2
            return response
        
        # Extract data from response
        data = self._extract_response_data(response)
        
        # Create JsonResponse
        json_response = JsonResponse(
            data, 
            status=response.status_code,
            headers=dict(response.headers)
        )
        
        if self.pretty_print:
            json_response.indent = 2
        
        return json_response
    
    def _extract_response_data(self, response: Response) -> Dict[str, Any]:
        """Extract data from response content."""
        content = response.content
        
        # Handle different content types
        if isinstance(content, dict):
            return content
        elif isinstance(content, (list, tuple)):
            return {'data': content}
        elif isinstance(content, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(content)
                return parsed if isinstance(parsed, dict) else {'data': parsed}
            except (json.JSONDecodeError, TypeError):
                return {'data': content}
        else:
            return {'data': str(content)}


class ApiJsonMiddleware(JsonResponseMiddleware):
    """JSON middleware specifically for API routes."""
    
    def __init__(self, pretty_print: bool = False):
        super().__init__(force_json=True, pretty_print=pretty_print)
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """Handle API request with consistent JSON structure."""
        try:
            response = await next_handler(request)
            
            # Wrap successful responses in consistent format
            if isinstance(response, JsonResponse) and response.status_code < 400:
                original_data = response.data
                
                # If not already wrapped, wrap it
                if not isinstance(original_data, dict) or 'data' not in original_data:
                    wrapped_data = {
                        'success': True,
                        'data': original_data,
                        'message': 'Request successful'
                    }
                    response.data = wrapped_data
            
            # Ensure JSON format
            if not isinstance(response, JsonResponse):
                response = self._convert_to_json_response(response)
            
            return response
            
        except Exception as e:
            # Convert exceptions to consistent JSON error format
            return JsonResponse({
                'success': False,
                'error': {
                    'type': type(e).__name__,
                    'message': str(e)
                },
                'data': None
            }, status=500)


class JsonValidationMiddleware(Middleware):
    """Middleware to validate JSON request bodies."""
    
    def __init__(self, required_fields: Optional[list] = None, 
                 schema: Optional[Dict[str, Any]] = None):
        """
        Initialize JSON validation middleware.
        
        Args:
            required_fields: List of required fields in JSON body
            schema: JSON schema for validation (future enhancement)
        """
        self.required_fields = required_fields or []
        self.schema = schema
    
    async def handle(self, request: Request, next_handler: Callable) -> Response:
        """Validate JSON request body."""
        # Only validate for POST, PUT, PATCH requests with JSON content
        if (request.method in ['POST', 'PUT', 'PATCH'] and 
            'application/json' in request.header('content-type', '')):
            
            try:
                # Parse JSON body
                json_data = await request.json()
                
                # Validate required fields
                missing_fields = []
                for field in self.required_fields:
                    if field not in json_data or json_data[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    return JsonResponse({
                        'success': False,
                        'error': {
                            'type': 'ValidationError',
                            'message': f'Missing required fields: {", ".join(missing_fields)}',
                            'missing_fields': missing_fields
                        }
                    }, status=400)
                
                # Store parsed JSON in request for use by controllers
                request._json_data = json_data
                
            except json.JSONDecodeError as e:
                return JsonResponse({
                    'success': False,
                    'error': {
                        'type': 'InvalidJSON',
                        'message': f'Invalid JSON: {str(e)}'
                    }
                }, status=400)
        
        return await next_handler(request)
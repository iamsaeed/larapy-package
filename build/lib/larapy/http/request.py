"""
HTTP Request handling for Larapy applications.

This module provides Laravel-like request handling with input data access,
file uploads, headers, and validation helpers.
"""

import json
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse
from starlette.requests import Request as StarletteRequest
from starlette.datastructures import UploadFile, FormData, QueryParams


class Request:
    """
    HTTP Request wrapper providing Laravel-like functionality.
    
    Wraps Starlette's Request to provide familiar Laravel methods
    for accessing request data, files, headers, and more.
    """
    
    def __init__(self, starlette_request: StarletteRequest):
        """
        Initialize the request wrapper.
        
        Args:
            starlette_request: The underlying Starlette request
        """
        self._request = starlette_request
        self._input_data: Optional[Dict[str, Any]] = None
        self._json_data: Optional[Dict[str, Any]] = None
        self._files: Optional[Dict[str, UploadFile]] = None
    
    @property
    def url(self) -> str:
        """Get the full URL for the request."""
        return str(self._request.url)
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the request."""
        return str(self._request.base_url)
    
    @property
    def path(self) -> str:
        """Get the path portion of the request URL."""
        return self._request.url.path
    
    @property
    def method(self) -> str:
        """Get the request method."""
        return self._request.method
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers."""
        return dict(self._request.headers)
    
    def header(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a header value.
        
        Args:
            key: The header name
            default: Default value if header not found
            
        Returns:
            The header value or default
        """
        return self._request.headers.get(key.lower(), default)
    
    def has_header(self, key: str) -> bool:
        """
        Check if a header exists.
        
        Args:
            key: The header name
            
        Returns:
            True if header exists, False otherwise
        """
        return key.lower() in self._request.headers
    
    @property
    def query_params(self) -> QueryParams:
        """Get query parameters."""
        return self._request.query_params
    
    def query(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get query parameter value(s).
        
        Args:
            key: The query parameter key, or None for all
            default: Default value if key not found
            
        Returns:
            Query parameter value, all parameters, or default
        """
        if key is None:
            return dict(self._request.query_params)
        
        return self._request.query_params.get(key, default)
    
    async def form(self) -> FormData:
        """
        Get form data from the request.
        
        Returns:
            The form data
        """
        return await self._request.form()
    
    async def json(self) -> Dict[str, Any]:
        """
        Get JSON data from the request.
        
        Returns:
            The JSON data as a dictionary
        """
        if self._json_data is None:
            try:
                self._json_data = await self._request.json()
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._json_data = {}
        
        return self._json_data
    
    async def body(self) -> bytes:
        """
        Get the raw body of the request.
        
        Returns:
            The raw request body
        """
        return await self._request.body()
    
    async def _load_input_data(self) -> None:
        """Load and cache input data from form and JSON."""
        if self._input_data is not None:
            return
        
        self._input_data = {}
        
        # Add query parameters
        self._input_data.update(dict(self._request.query_params))
        
        # Add form data if present
        if self.is_form():
            form_data = await self.form()
            for key, value in form_data.items():
                if isinstance(value, UploadFile):
                    # Store files separately
                    if self._files is None:
                        self._files = {}
                    self._files[key] = value
                else:
                    self._input_data[key] = value
        
        # Add JSON data if present
        elif self.is_json():
            json_data = await self.json()
            self._input_data.update(json_data)
    
    async def input(self, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get input data from the request.
        
        Args:
            key: The input key, or None for all input
            default: Default value if key not found
            
        Returns:
            Input value, all input, or default
        """
        await self._load_input_data()
        
        if key is None:
            return self._input_data.copy()
        
        return self._input_data.get(key, default)
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Alias for input() method.
        
        Args:
            key: The input key
            default: Default value if key not found
            
        Returns:
            Input value or default
        """
        return await self.input(key, default)
    
    async def all(self) -> Dict[str, Any]:
        """
        Get all input data.
        
        Returns:
            All input data as a dictionary
        """
        return await self.input()
    
    async def only(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get only specified input keys.
        
        Args:
            keys: List of keys to retrieve
            
        Returns:
            Dictionary with only specified keys
        """
        all_input = await self.all()
        return {key: all_input.get(key) for key in keys if key in all_input}
    
    async def except_(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get all input except specified keys.
        
        Args:
            keys: List of keys to exclude
            
        Returns:
            Dictionary without specified keys
        """
        all_input = await self.all()
        return {key: value for key, value in all_input.items() if key not in keys}
    
    async def has(self, key: Union[str, List[str]]) -> bool:
        """
        Check if input key(s) exist.
        
        Args:
            key: Single key or list of keys to check
            
        Returns:
            True if all keys exist, False otherwise
        """
        await self._load_input_data()
        
        if isinstance(key, str):
            return key in self._input_data
        
        return all(k in self._input_data for k in key)
    
    async def filled(self, key: Union[str, List[str]]) -> bool:
        """
        Check if input key(s) exist and are not empty.
        
        Args:
            key: Single key or list of keys to check
            
        Returns:
            True if all keys exist and are not empty, False otherwise
        """
        await self._load_input_data()
        
        def is_filled(k: str) -> bool:
            if k not in self._input_data:
                return False
            value = self._input_data[k]
            return value is not None and value != '' and value != []
        
        if isinstance(key, str):
            return is_filled(key)
        
        return all(is_filled(k) for k in key)
    
    async def file(self, key: str) -> Optional[UploadFile]:
        """
        Get an uploaded file.
        
        Args:
            key: The file input key
            
        Returns:
            The uploaded file or None
        """
        await self._load_input_data()
        
        if self._files is None:
            return None
        
        return self._files.get(key)
    
    async def has_file(self, key: str) -> bool:
        """
        Check if a file was uploaded.
        
        Args:
            key: The file input key
            
        Returns:
            True if file exists, False otherwise
        """
        file = await self.file(key)
        return file is not None and file.filename
    
    def is_json(self) -> bool:
        """
        Check if the request is JSON.
        
        Returns:
            True if request contains JSON, False otherwise
        """
        content_type = self.header('content-type', '')
        return 'application/json' in content_type
    
    def is_form(self) -> bool:
        """
        Check if the request is form data.
        
        Returns:
            True if request is form data, False otherwise
        """
        content_type = self.header('content-type', '')
        return ('application/x-www-form-urlencoded' in content_type or 
                'multipart/form-data' in content_type)
    
    def is_ajax(self) -> bool:
        """
        Check if the request is AJAX.
        
        Returns:
            True if request is AJAX, False otherwise
        """
        return self.header('x-requested-with') == 'XMLHttpRequest'
    
    def is_secure(self) -> bool:
        """
        Check if the request is over HTTPS.
        
        Returns:
            True if HTTPS, False otherwise
        """
        return self._request.url.scheme == 'https'
    
    def wants_json(self) -> bool:
        """
        Check if the request wants JSON response.
        
        Returns:
            True if JSON is preferred, False otherwise
        """
        accept = self.header('accept', '')
        return 'application/json' in accept
    
    def ip(self) -> Optional[str]:
        """
        Get the client IP address.
        
        Returns:
            The client IP address
        """
        # Check for forwarded headers first
        forwarded_for = self.header('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = self.header('x-real-ip')
        if real_ip:
            return real_ip
        
        # Fall back to client address
        if hasattr(self._request, 'client') and self._request.client:
            return self._request.client.host
        
        return None
    
    def user_agent(self) -> Optional[str]:
        """
        Get the User-Agent header.
        
        Returns:
            The User-Agent string
        """
        return self.header('user-agent')
    
    @property
    def cookies(self) -> Dict[str, str]:
        """Get request cookies."""
        return dict(self._request.cookies)
    
    def cookie(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a cookie value.
        
        Args:
            key: The cookie name
            default: Default value if cookie not found
            
        Returns:
            The cookie value or default
        """
        return self._request.cookies.get(key, default)
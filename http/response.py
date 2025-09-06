"""
HTTP Response handling for Larapy applications.

This module provides Laravel-like response creation and manipulation with
content management, status codes, headers, and JSON responses.
"""

import json
from typing import Any, Dict, Optional, Union
from starlette.responses import Response as StarletteResponse, JSONResponse, PlainTextResponse


class Response:
    """
    HTTP Response wrapper providing Laravel-like functionality.
    
    Provides methods for creating and manipulating HTTP responses with
    content, status codes, headers, and specialized response types.
    """
    
    def __init__(self, 
                 content: Any = "", 
                 status: int = 200, 
                 headers: Optional[Dict[str, str]] = None,
                 media_type: str = "text/html"):
        """
        Initialize the response.
        
        Args:
            content: The response content
            status: The HTTP status code
            headers: Response headers
            media_type: The response media type
        """
        self._content = content
        self._status = status
        self._headers = headers or {}
        self._media_type = media_type
        self._starlette_response: Optional[StarletteResponse] = None
    
    @property
    def content(self) -> Any:
        """Get the response content."""
        return self._content
    
    @content.setter
    def content(self, value: Any) -> None:
        """Set the response content."""
        self._content = value
        self._starlette_response = None  # Reset cached response
    
    @property 
    def status_code(self) -> int:
        """Get the response status code."""
        return self._status
    
    @status_code.setter
    def status_code(self, value: int) -> None:
        """Set the response status code."""
        self._status = value
        self._starlette_response = None  # Reset cached response
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get response headers."""
        return self._headers.copy()
    
    def header(self, key: str, value: str) -> "Response":
        """
        Add a header to the response.
        
        Args:
            key: The header name
            value: The header value
            
        Returns:
            Self for method chaining
        """
        self._headers[key] = value
        self._starlette_response = None  # Reset cached response
        return self
    
    def with_headers(self, headers: Dict[str, str]) -> "Response":
        """
        Add multiple headers to the response.
        
        Args:
            headers: Dictionary of headers to add
            
        Returns:
            Self for method chaining
        """
        self._headers.update(headers)
        self._starlette_response = None  # Reset cached response
        return self
    
    def without_header(self, key: str) -> "Response":
        """
        Remove a header from the response.
        
        Args:
            key: The header name to remove
            
        Returns:
            Self for method chaining
        """
        self._headers.pop(key, None)
        self._starlette_response = None  # Reset cached response
        return self
    
    def cookie(self, 
               key: str, 
               value: str = "", 
               max_age: Optional[int] = None,
               expires: Optional[str] = None,
               path: str = "/",
               domain: Optional[str] = None,
               secure: bool = False,
               httponly: bool = False,
               samesite: str = "lax") -> "Response":
        """
        Add a cookie to the response.
        
        Args:
            key: The cookie name
            value: The cookie value
            max_age: Maximum age in seconds
            expires: Expiration date
            path: Cookie path
            domain: Cookie domain
            secure: Whether cookie requires HTTPS
            httponly: Whether cookie is HTTP only
            samesite: SameSite attribute
            
        Returns:
            Self for method chaining
        """
        # For now, we'll store cookie info in headers
        # A full implementation would handle cookie creation properly
        cookie_header = f"{key}={value}"
        
        if max_age is not None:
            cookie_header += f"; Max-Age={max_age}"
        if expires:
            cookie_header += f"; Expires={expires}"
        if path:
            cookie_header += f"; Path={path}"
        if domain:
            cookie_header += f"; Domain={domain}"
        if secure:
            cookie_header += "; Secure"
        if httponly:
            cookie_header += "; HttpOnly"
        if samesite:
            cookie_header += f"; SameSite={samesite}"
        
        # Handle multiple Set-Cookie headers
        if "Set-Cookie" in self._headers:
            existing = self._headers["Set-Cookie"]
            self._headers["Set-Cookie"] = f"{existing}, {cookie_header}"
        else:
            self._headers["Set-Cookie"] = cookie_header
        
        return self
    
    def to_starlette_response(self) -> StarletteResponse:
        """
        Convert to Starlette response.
        
        Returns:
            The Starlette response object
        """
        if self._starlette_response is None:
            # Convert content to appropriate response type
            if isinstance(self._content, (dict, list)):
                self._starlette_response = JSONResponse(
                    content=self._content,
                    status_code=self._status,
                    headers=self._headers
                )
            elif isinstance(self._content, str):
                self._starlette_response = PlainTextResponse(
                    content=self._content,
                    status_code=self._status,
                    headers=self._headers,
                    media_type=self._media_type
                )
            else:
                # Handle other content types
                self._starlette_response = StarletteResponse(
                    content=str(self._content),
                    status_code=self._status,
                    headers=self._headers,
                    media_type=self._media_type
                )
        
        return self._starlette_response
    
    def __str__(self) -> str:
        """String representation of the response."""
        return str(self._content)
    
    def __repr__(self) -> str:
        """Developer representation of the response."""
        return f"Response({self._content!r}, {self._status})"


class JsonResponse(Response):
    """JSON response class."""
    
    def __init__(self, 
                 data: Any = None, 
                 status: int = 200, 
                 headers: Optional[Dict[str, str]] = None,
                 safe: bool = True,
                 json_dumps_params: Optional[Dict[str, Any]] = None):
        """
        Initialize JSON response.
        
        Args:
            data: The data to serialize as JSON
            status: The HTTP status code
            headers: Response headers
            safe: Whether to allow non-dict objects
            json_dumps_params: Parameters for json.dumps
        """
        super().__init__(data, status, headers, "application/json")
        self._safe = safe
        self._json_dumps_params = json_dumps_params or {}
        
        # Validate data if safe mode is enabled
        if self._safe and not isinstance(data, (dict, list)):
            raise TypeError(
                "In order to allow non-dict objects to be serialized, "
                "set the safe parameter to False."
            )
    
    def to_starlette_response(self) -> JSONResponse:
        """
        Convert to Starlette JSON response.
        
        Returns:
            The Starlette JSON response
        """
        if self._starlette_response is None:
            self._starlette_response = JSONResponse(
                content=self._content,
                status_code=self._status,
                headers=self._headers
            )
        
        return self._starlette_response


class RedirectResponse(Response):
    """Redirect response class."""
    
    def __init__(self, 
                 url: str, 
                 status: int = 302,
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialize redirect response.
        
        Args:
            url: The URL to redirect to
            status: The HTTP status code (302, 301, etc.)
            headers: Additional headers
        """
        super().__init__("", status, headers)
        self._url = url
        self.header("Location", url)
    
    @property
    def url(self) -> str:
        """Get the redirect URL."""
        return self._url
    
    def to_starlette_response(self) -> StarletteResponse:
        """
        Convert to Starlette redirect response.
        
        Returns:
            The Starlette response with redirect
        """
        from starlette.responses import RedirectResponse as StarletteRedirect
        
        if self._starlette_response is None:
            self._starlette_response = StarletteRedirect(
                url=self._url,
                status_code=self._status,
                headers=self._headers
            )
        
        return self._starlette_response


# Helper functions for creating responses
def response(content: Any = "", 
             status: int = 200, 
             headers: Optional[Dict[str, str]] = None) -> Response:
    """
    Create a new response instance.
    
    Args:
        content: The response content
        status: The HTTP status code
        headers: Response headers
        
    Returns:
        A new Response instance
    """
    return Response(content, status, headers)


def json_response(data: Any = None, 
                  status: int = 200, 
                  headers: Optional[Dict[str, str]] = None,
                  safe: bool = True) -> JsonResponse:
    """
    Create a JSON response.
    
    Args:
        data: The data to serialize
        status: The HTTP status code
        headers: Response headers
        safe: Whether to allow non-dict objects
        
    Returns:
        A JSON response instance
    """
    return JsonResponse(data, status, headers, safe)


def redirect(url: str, 
             status: int = 302,
             headers: Optional[Dict[str, str]] = None) -> RedirectResponse:
    """
    Create a redirect response.
    
    Args:
        url: The URL to redirect to
        status: The HTTP status code
        headers: Additional headers
        
    Returns:
        A redirect response instance
    """
    return RedirectResponse(url, status, headers)


def abort(status: int, message: str = "") -> Response:
    """
    Create an error response.
    
    Args:
        status: The HTTP status code
        message: Optional error message
        
    Returns:
        An error response
    """
    if not message:
        status_messages = {
            400: "Bad Request",
            401: "Unauthorized", 
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable"
        }
        message = status_messages.get(status, "Error")
    
    return Response(message, status)


class FileResponse(Response):
    """File download response class."""
    
    def __init__(self, 
                 file_path: str, 
                 filename: str = None,
                 content_type: str = None,
                 as_attachment: bool = True,
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialize file response.
        
        Args:
            file_path: Path to the file
            filename: Download filename (defaults to basename)
            content_type: MIME type (auto-detected if not provided)
            as_attachment: Whether to download as attachment
            headers: Additional headers
        """
        import os
        import mimetypes
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self._file_path = file_path
        self._filename = filename or os.path.basename(file_path)
        self._as_attachment = as_attachment
        
        # Auto-detect content type
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or 'application/octet-stream'
        
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
        
        super().__init__(content, 200, headers, content_type)
        
        # Set content disposition header
        disposition = 'attachment' if as_attachment else 'inline'
        self.header('Content-Disposition', f'{disposition}; filename="{self._filename}"')
        self.header('Content-Length', str(len(content)))
    
    def to_starlette_response(self):
        """Convert to Starlette file response."""
        from starlette.responses import FileResponse as StarletteFileResponse
        
        if self._starlette_response is None:
            headers = dict(self._headers)
            self._starlette_response = StarletteFileResponse(
                path=self._file_path,
                filename=self._filename,
                media_type=self._media_type,
                headers=headers
            )
        
        return self._starlette_response


class StreamedResponse(Response):
    """Streamed response for large content."""
    
    def __init__(self, 
                 generator,
                 media_type: str = "text/plain",
                 headers: Optional[Dict[str, str]] = None):
        """
        Initialize streamed response.
        
        Args:
            generator: Generator function that yields content chunks
            media_type: Content type
            headers: Additional headers
        """
        self._generator = generator
        super().__init__("", 200, headers, media_type)
        self.header('Transfer-Encoding', 'chunked')
    
    def to_starlette_response(self):
        """Convert to Starlette streaming response."""
        from starlette.responses import StreamingResponse
        
        if self._starlette_response is None:
            self._starlette_response = StreamingResponse(
                self._generator,
                media_type=self._media_type,
                headers=self._headers
            )
        
        return self._starlette_response
    
    def __iter__(self):
        """Stream content."""
        return iter(self._generator)


# Additional helper functions
def file_response(file_path: str, 
                  filename: str = None,
                  content_type: str = None,
                  as_attachment: bool = True) -> FileResponse:
    """Create a file download response."""
    return FileResponse(file_path, filename, content_type, as_attachment)


def streamed_response(generator, media_type: str = "text/plain") -> StreamedResponse:
    """Create a streamed response."""
    return StreamedResponse(generator, media_type)


def view(view_name: str, data: Optional[Dict[str, Any]] = None, 
         status: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    """
    Create a response with a rendered view.
    
    Args:
        view_name: Name of the view template
        data: Data to pass to the view
        status: HTTP status code
        headers: Additional headers
        
    Returns:
        Response with rendered view content
    """
    try:
        from ..view import view_response
        return view_response(view_name, data)
    except ImportError:
        # Fallback if view system not available
        content = f"<!-- View '{view_name}' not found - view system not loaded -->"
        return Response(content, status, headers)
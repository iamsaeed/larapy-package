"""
View response classes for Larapy.

Provides specialized response types for views and templates.
"""

from typing import Dict, Any, Optional
from ..http.response import Response


class ViewResponse(Response):
    """Response that renders a view template."""
    
    def __init__(self, view_name: str, data: Dict[str, Any] = None, 
                 status: int = 200, headers: Dict[str, str] = None):
        """
        Initialize view response.
        
        Args:
            view_name: Name of the view template
            data: Data to pass to the template
            status: HTTP status code
            headers: HTTP headers
        """
        self.view_name = view_name
        self.view_data = data or {}
        
        # Render the view
        from .view import view_manager
        content = view_manager.render(view_name, self.view_data)
        
        super().__init__(content, status=status, headers=headers)
        
        # Set content type to HTML by default
        if not self.headers.get('content-type'):
            self.header('Content-Type', 'text/html; charset=utf-8')
    
    def with_data(self, key: str, value: Any) -> 'ViewResponse':
        """
        Add data to the view response.
        
        Args:
            key: Data key
            value: Data value
            
        Returns:
            Self for method chaining
        """
        self.view_data[key] = value
        
        # Re-render with new data
        from .view import view_manager
        self.content = view_manager.render(self.view_name, self.view_data)
        
        return self


class TemplateResponse(Response):
    """Response for direct template rendering without view manager."""
    
    def __init__(self, template_content: str, data: Dict[str, Any] = None,
                 status: int = 200, headers: Dict[str, str] = None):
        """
        Initialize template response.
        
        Args:
            template_content: Raw template content
            data: Template data
            status: HTTP status code  
            headers: HTTP headers
        """
        self.template_content = template_content
        self.template_data = data or {}
        
        # Simple template rendering (variable substitution)
        try:
            content = template_content.format(**self.template_data)
        except KeyError as e:
            content = f"Template error: Missing variable {e}"
        
        super().__init__(content, status=status, headers=headers)
        self.header('Content-Type', 'text/html; charset=utf-8')


class ComponentResponse(Response):
    """Response for rendering a single component."""
    
    def __init__(self, component_name: str, attributes: Dict[str, Any] = None,
                 slots: Dict[str, str] = None, status: int = 200, 
                 headers: Dict[str, str] = None):
        """
        Initialize component response.
        
        Args:
            component_name: Name of the component
            attributes: Component attributes
            slots: Component slots
            status: HTTP status code
            headers: HTTP headers
        """
        from .component import component_registry
        
        component = component_registry.make(component_name, **(attributes or {}))
        
        if not component:
            content = f"<!-- Component '{component_name}' not found -->"
        else:
            # Add slots if provided
            if slots:
                for slot_name, slot_content in slots.items():
                    component.with_slot(slot_name, slot_content)
            
            content = component.render()
        
        super().__init__(content, status=status, headers=headers)
        self.header('Content-Type', 'text/html; charset=utf-8')


class LayoutResponse(ViewResponse):
    """Response that renders a view within a layout."""
    
    def __init__(self, view_name: str, layout: str = 'layouts.app',
                 data: Dict[str, Any] = None, status: int = 200,
                 headers: Dict[str, str] = None):
        """
        Initialize layout response.
        
        Args:
            view_name: Name of the content view
            layout: Name of the layout template
            data: Data to pass to templates
            status: HTTP status code
            headers: HTTP headers
        """
        self.layout_name = layout
        
        # Render the content view first
        from .view import view_manager
        content_html = view_manager.render(view_name, data or {})
        
        # Then render the layout with the content
        layout_data = {
            'content': content_html,
            **(data or {})
        }
        
        # Initialize parent with layout rendering
        Response.__init__(self, '', status=status, headers=headers)
        self.view_name = layout
        self.view_data = layout_data
        self.content = view_manager.render(layout, layout_data)
        
        # Set content type
        if not self.headers.get('content-type'):
            self.header('Content-Type', 'text/html; charset=utf-8')


class PartialResponse(Response):
    """Response for rendering partial views (AJAX responses)."""
    
    def __init__(self, view_name: str, data: Dict[str, Any] = None,
                 wrap_in_container: bool = False, container_id: str = None,
                 status: int = 200, headers: Dict[str, str] = None):
        """
        Initialize partial response.
        
        Args:
            view_name: Name of the partial view
            data: View data
            wrap_in_container: Whether to wrap in container div
            container_id: ID for container div
            status: HTTP status code
            headers: HTTP headers
        """
        from .view import view_manager
        content = view_manager.render(view_name, data or {})
        
        if wrap_in_container:
            container_attrs = f' id="{container_id}"' if container_id else ''
            content = f'<div{container_attrs}>{content}</div>'
        
        super().__init__(content, status=status, headers=headers)
        
        # Set appropriate headers for AJAX
        self.header('Content-Type', 'text/html; charset=utf-8')
        self.header('X-Requested-With', 'XMLHttpRequest')


class StreamedViewResponse(Response):
    """Response that streams view content."""
    
    def __init__(self, view_name: str, data_generator, 
                 status: int = 200, headers: Dict[str, str] = None):
        """
        Initialize streamed view response.
        
        Args:
            view_name: Name of the view template
            data_generator: Generator that yields data for each chunk
            status: HTTP status code
            headers: HTTP headers
        """
        self.view_name = view_name
        self.data_generator = data_generator
        
        super().__init__('', status=status, headers=headers)
        self.header('Content-Type', 'text/html; charset=utf-8')
        self.header('Transfer-Encoding', 'chunked')
    
    def __iter__(self):
        """Stream the view content."""
        from .view import view_manager
        
        for data_chunk in self.data_generator:
            chunk_content = view_manager.render(self.view_name, data_chunk)
            yield chunk_content.encode('utf-8')


class ErrorViewResponse(ViewResponse):
    """Response for error pages."""
    
    def __init__(self, error_code: int, message: str = None,
                 view_name: str = None, data: Dict[str, Any] = None):
        """
        Initialize error view response.
        
        Args:
            error_code: HTTP error code
            message: Error message
            view_name: Custom error view name
            data: Additional view data
        """
        # Default error view names
        if not view_name:
            view_name = f'errors.{error_code}'
        
        # Default error data
        error_data = {
            'error_code': error_code,
            'error_message': message or self._get_default_message(error_code),
            **(data or {})
        }
        
        super().__init__(view_name, error_data, status=error_code)
    
    def _get_default_message(self, code: int) -> str:
        """Get default error message for HTTP code."""
        messages = {
            400: 'Bad Request',
            401: 'Unauthorized', 
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            500: 'Internal Server Error',
            502: 'Bad Gateway',
            503: 'Service Unavailable'
        }
        return messages.get(code, 'An error occurred')


# Helper functions for creating responses
def view(view_name: str, data: Dict[str, Any] = None, 
         status: int = 200) -> ViewResponse:
    """Create a view response."""
    return ViewResponse(view_name, data, status)


def layout(view_name: str, layout_name: str = 'layouts.app',
           data: Dict[str, Any] = None, status: int = 200) -> LayoutResponse:
    """Create a layout response.""" 
    return LayoutResponse(view_name, layout_name, data, status)


def partial(view_name: str, data: Dict[str, Any] = None,
            wrap: bool = False, container_id: str = None) -> PartialResponse:
    """Create a partial response."""
    return PartialResponse(view_name, data, wrap, container_id)


def component(component_name: str, attributes: Dict[str, Any] = None,
              slots: Dict[str, str] = None) -> ComponentResponse:
    """Create a component response."""
    return ComponentResponse(component_name, attributes, slots)


def error(code: int, message: str = None, view_name: str = None,
          data: Dict[str, Any] = None) -> ErrorViewResponse:
    """Create an error response."""
    return ErrorViewResponse(code, message, view_name, data)
"""
Core view functionality for Larapy.

Provides the main View class and ViewManager for template rendering.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from ..http.response import Response


class View:
    """Represents a renderable view."""
    
    def __init__(self, name: str, data: Dict[str, Any] = None, engine: 'Engine' = None):
        """
        Initialize a view.
        
        Args:
            name: Template name
            data: View data
            engine: Template engine to use
        """
        self.name = name
        self.data = data or {}
        self.engine = engine
        
    def with_data(self, key: Union[str, Dict[str, Any]], value: Any = None) -> 'View':
        """Add data to the view."""
        if isinstance(key, dict):
            self.data.update(key)
        else:
            self.data[key] = value
        return self
    
    def render(self) -> str:
        """Render the view to string."""
        if not self.engine:
            raise ValueError("No template engine configured")
        return self.engine.render(self.name, self.data)
    
    def __str__(self) -> str:
        return self.render()


class ViewManager:
    """Manages view rendering and template engines."""
    
    def __init__(self):
        self.engines: Dict[str, 'Engine'] = {}
        self.paths: List[Path] = []
        self.shared_data: Dict[str, Any] = {}
        self.composers: Dict[str, List[callable]] = {}
        self.creators: Dict[str, List[callable]] = {}
        self.default_engine = 'jinja2'
        
    def add_path(self, path: Union[str, Path]):
        """Add a template search path."""
        if isinstance(path, str):
            path = Path(path)
        if path not in self.paths:
            self.paths.append(path)
    
    def add_engine(self, name: str, engine: 'Engine'):
        """Add a template engine."""
        self.engines[name] = engine
        engine.set_paths(self.paths)
    
    def make(self, name: str, data: Dict[str, Any] = None, engine: str = None) -> View:
        """Create a view instance."""
        engine_name = engine or self.default_engine
        
        if engine_name not in self.engines:
            raise ValueError(f"Template engine '{engine_name}' not found")
        
        # Merge shared data with view data
        view_data = self.shared_data.copy()
        if data:
            view_data.update(data)
        
        # Add security context
        view_data = self._add_security_context(view_data)
        
        # Create view
        view = View(name, view_data, self.engines[engine_name])
        
        # Run view composers
        self._run_composers(name, view)
        
        return view
    
    def _add_security_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add security-related context and Laravel-style helpers to all views."""
        try:
            from larapy.core.application import app
            from .template_functions import create_template_context, create_template_functions
            
            # Get Laravel-style context objects
            template_context = create_template_context(app)
            template_functions = create_template_functions(app)
            
            enhanced_data = {
                **data,
                **template_context,
                **template_functions,
            }
            
            return enhanced_data
            
        except Exception as e:
            # Fallback if app not available
            return {
                **data,
                'csrf_token': lambda: 'demo-token',
                'csrf_field': lambda: '<input type="hidden" name="_token" value="demo-token">',
                'method_field': lambda method: f'<input type="hidden" name="_method" value="{method.upper()}">',
                'old': lambda key, default='': default,
                'route': lambda name, **params: f"/{name}",
                'asset': lambda path: f"/assets/{path.lstrip('/')}",
                'url': lambda path: f"/{path.lstrip('/')}",
                'can': lambda perm, model=None: True,
                'cannot': lambda perm, model=None: False,
                'config': lambda key, default=None: {
                    'app.name': 'Larapy',
                    'app.env': 'local',
                    'app.debug': True,
                }.get(key, default),
                'auth': None,
                'errors': type('MockErrors', (), {
                    'has': lambda self, key: False,
                    'first': lambda self, key, default='': default,
                    'all': lambda self, key=None: {},
                    'count': lambda self, key=None: 0,
                })(),
                'session': {},
            }
    
    def share(self, key: Union[str, Dict[str, Any]], value: Any = None):
        """Share data across all views."""
        if isinstance(key, dict):
            self.shared_data.update(key)
        else:
            self.shared_data[key] = value
    
    def composer(self, views: Union[str, List[str]], callback: callable):
        """Register a view composer."""
        if isinstance(views, str):
            views = [views]
            
        for view in views:
            if view not in self.composers:
                self.composers[view] = []
            self.composers[view].append(callback)
    
    def creator(self, views: Union[str, List[str]], callback: callable):
        """Register a view creator."""
        if isinstance(views, str):
            views = [views]
            
        for view in views:
            if view not in self.creators:
                self.creators[view] = []
            self.creators[view].append(callback)
    
    def exists(self, name: str) -> bool:
        """Check if a view exists."""
        engine = self.engines.get(self.default_engine)
        if not engine:
            return False
        return engine.exists(name)
    
    def render(self, name: str, data: Dict[str, Any] = None) -> str:
        """Render a view to string."""
        view = self.make(name, data)
        return view.render()
    
    def _run_composers(self, name: str, view: View):
        """Run view composers for the given view."""
        # Check for exact matches
        if name in self.composers:
            for composer in self.composers[name]:
                composer(view)
        
        # Check for wildcard matches
        for pattern, composers in self.composers.items():
            if self._matches_pattern(name, pattern):
                for composer in composers:
                    composer(view)
    
    def _matches_pattern(self, name: str, pattern: str) -> bool:
        """Check if view name matches a pattern."""
        if '*' not in pattern:
            return name == pattern
        
        # Simple wildcard matching
        parts = pattern.split('*')
        if len(parts) == 2:
            start, end = parts
            return name.startswith(start) and name.endswith(end)
        
        return False


# Global view manager instance
view_manager = ViewManager()


def view(name: str, data: Dict[str, Any] = None) -> View:
    """Helper function to create a view."""
    return view_manager.make(name, data)


def view_response(name: str, data: Dict[str, Any] = None, status: int = 200, 
                  headers: Dict[str, str] = None) -> Response:
    """Create a view response."""
    content = view_manager.render(name, data)
    response = Response(content, status=status)
    
    if headers:
        for key, value in headers.items():
            response.header(key, value)
    
    # Set content type to HTML by default
    if 'content-type' not in (headers or {}):
        response.header('Content-Type', 'text/html; charset=utf-8')
    
    return response
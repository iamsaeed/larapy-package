"""
Template engine implementations for Larapy.

Provides support for multiple template engines including Jinja2.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from .security import TemplateSecurity, configure_template_security
from .directives import compile_directives


class Engine(ABC):
    """Abstract base class for template engines."""
    
    def __init__(self):
        self.paths: List[Path] = []
        
    def set_paths(self, paths: List[Path]):
        """Set template search paths."""
        self.paths = paths
        
    @abstractmethod
    def render(self, template: str, data: Dict[str, Any]) -> str:
        """Render a template with data."""
        pass
        
    @abstractmethod
    def exists(self, template: str) -> bool:
        """Check if a template exists."""
        pass


class Jinja2Engine(Engine):
    """Jinja2 template engine implementation with security features."""
    
    def __init__(self, **options):
        """
        Initialize Jinja2 engine.
        
        Args:
            **options: Jinja2 environment options
        """
        super().__init__()
        self.options = {
            'autoescape': True,
            'auto_reload': True,
            'cache_size': 400,
            'trim_blocks': True,
            'lstrip_blocks': True,
            **options
        }
        self._env = None
        self.security = TemplateSecurity()
        self.secret_key = options.get('secret_key', 'default-secret-key')
        
    def _get_env(self):
        """Get or create Jinja2 environment."""
        if self._env is None:
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape
                
                # Convert paths to strings for FileSystemLoader
                str_paths = [str(path) for path in self.paths]
                
                self._env = Environment(
                    loader=FileSystemLoader(str_paths),
                    autoescape=select_autoescape(['html', 'xml']) if self.options.get('autoescape') else False,
                    auto_reload=self.options.get('auto_reload', True),
                    cache_size=self.options.get('cache_size', 400),
                    trim_blocks=self.options.get('trim_blocks', True),
                    lstrip_blocks=self.options.get('lstrip_blocks', True)
                )
                
                # Configure security features
                self._env = configure_template_security(self._env, self.secret_key)
                
                # Add custom filters and functions
                self._add_custom_filters()
                self._add_global_functions()
                
            except ImportError:
                raise ImportError("Jinja2 is required for template rendering. Install with: pip install jinja2")
                
        return self._env
    
    def render(self, template: str, data: Dict[str, Any]) -> str:
        """Render a Jinja2 template with security features and directives."""
        env = self._get_env()
        
        try:
            # For now, skip directive compilation and render directly
            template_obj = env.get_template(template)
            return template_obj.render(**data)
            
            # TODO: Re-enable directive compilation once basic rendering works
            # Get template source from the loader
            # template_source, filename = env.loader.get_source(env, template)
            # 
            # # Compile Laravel-style directives to Jinja2
            # compiled_source = compile_directives(template_source)
            # 
            # # Create new template from compiled source
            # compiled_template = env.from_string(compiled_source)
            # 
            # return compiled_template.render(**data)
        except Exception as e:
            raise RuntimeError(f"Error rendering template '{template}': {str(e)}")
    
    def exists(self, template: str) -> bool:
        """Check if a Jinja2 template exists."""
        env = self._get_env()
        
        try:
            env.get_template(template)
            return True
        except:
            return False
    
    def _add_custom_filters(self):
        """Add custom Jinja2 filters."""
        env = self._get_env()
        
        def currency_filter(value, symbol='$'):
            """Format value as currency."""
            try:
                return f"{symbol}{float(value):.2f}"
            except (ValueError, TypeError):
                return value
        
        def truncate_words_filter(text, count=10, suffix='...'):
            """Truncate text to specified word count."""
            if not text:
                return text
            words = str(text).split()
            if len(words) <= count:
                return text
            return ' '.join(words[:count]) + suffix
            
        def slugify_filter(text):
            """Convert text to slug format."""
            import re
            text = str(text).lower()
            text = re.sub(r'[^\w\s-]', '', text)
            text = re.sub(r'[-\s]+', '-', text)
            return text.strip('-')
        
        # Add filters to environment
        env.filters['currency'] = currency_filter
        env.filters['truncate_words'] = truncate_words_filter
        env.filters['slugify'] = slugify_filter
    
    def _add_global_functions(self):
        """Add global template functions."""
        env = self._get_env()
        
        try:
            from larapy.core.application import app
            from .template_functions import create_template_functions, create_template_context
            
            # Create Laravel-style functions
            functions = create_template_functions(app)
            env.globals.update(functions)
            
            # Add context objects (auth, errors, config, etc.)
            context = create_template_context(app)
            env.globals.update(context)
            
        except Exception as e:
            # Fallback to basic functions if app not available
            def url(route_name, **kwargs):
                """Generate URL for named route."""
                if kwargs:
                    param_str = '/'.join(str(v) for v in kwargs.values())
                    return f"/{route_name}/{param_str}"
                return f"/{route_name}"
                
            def asset(path):
                """Generate asset URL."""
                return f"/assets/{path.lstrip('/')}"
                
            def csrf_token():
                """Generate CSRF token."""
                import secrets
                return secrets.token_urlsafe(32)
            
            def csrf_field():
                """Generate CSRF field."""
                token = csrf_token()
                return f'<input type="hidden" name="_token" value="{token}">'
                
            def old(key, default=''):
                """Get old input value."""
                return default
            
            def method_field(method):
                """Generate method field."""
                if method.upper() in ['PUT', 'PATCH', 'DELETE']:
                    return f'<input type="hidden" name="_method" value="{method.upper()}">'
                return ''
            
            # Add fallback functions
            env.globals.update({
                'url': url,
                'asset': asset,
                'csrf_token': csrf_token,
                'csrf_field': csrf_field,
                'old': old,
                'method_field': method_field,
                'route': url,  # alias for url
                'can': lambda perm, model=None: True,  # placeholder
                'cannot': lambda perm, model=None: False,  # placeholder
                'config': lambda key, default=None: {
                    'app.name': 'Larapy',
                    'app.env': 'local',
                    'app.debug': True,
                }.get(key, default),
            })


class SimpleEngine(Engine):
    """Simple string-based template engine."""
    
    def render(self, template: str, data: Dict[str, Any]) -> str:
        """Render template using simple string formatting."""
        template_content = self._load_template(template)
        
        if template_content is None:
            raise FileNotFoundError(f"Template '{template}' not found")
            
        # Simple variable replacement
        try:
            return template_content.format(**data)
        except KeyError as e:
            raise RuntimeError(f"Missing template variable: {e}")
    
    def exists(self, template: str) -> bool:
        """Check if template file exists."""
        return self._find_template_path(template) is not None
    
    def _load_template(self, template: str) -> Optional[str]:
        """Load template content from file."""
        template_path = self._find_template_path(template)
        
        if template_path is None:
            return None
            
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, OSError):
            return None
    
    def _find_template_path(self, template: str) -> Optional[Path]:
        """Find template file in search paths."""
        for path in self.paths:
            template_path = path / template
            if template_path.is_file():
                return template_path
                
            # Also try with .html extension
            html_path = path / f"{template}.html"
            if html_path.is_file():
                return html_path
                
        return None


class TemplateCache:
    """Template caching system."""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache: Dict[str, str] = {}
        self.access_order: List[str] = []
    
    def get(self, key: str) -> Optional[str]:
        """Get cached template."""
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, content: str):
        """Cache template content."""
        if key in self.cache:
            # Update existing
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest = self.access_order.pop(0)
            del self.cache[oldest]
        
        self.cache[key] = content
        self.access_order.append(key)
    
    def clear(self):
        """Clear all cached templates."""
        self.cache.clear()
        self.access_order.clear()
    
    def size(self) -> int:
        """Get cache size."""
        return len(self.cache)